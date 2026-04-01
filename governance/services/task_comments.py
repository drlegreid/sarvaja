"""Task Comments Service — CRUD for resolution comments.

Per EPIC-ISSUE-EVIDENCE P19: Comment thread on tasks.
In-memory store with TypeDB persistence (best-effort write-through).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from governance.stores.audit import record_audit

logger = logging.getLogger(__name__)

# In-memory store: task_id -> list of comment dicts
_comments_store: Dict[str, List[Dict[str, Any]]] = {}

# Max comments per task (anti-rot cap)
_MAX_COMMENTS_PER_TASK = 100


def _get_typedb_client():
    """Get TypeDB client if available (best-effort)."""
    try:
        from governance.stores import get_typedb_client
        client = get_typedb_client()
        if client and client.is_connected():
            return client
    except Exception:
        pass
    return None


def add_comment(
    task_id: str,
    body: str,
    author: str = "code-agent",
) -> Dict[str, Any]:
    """Add a comment to a task.

    Persists to in-memory store and TypeDB (best-effort write-through).

    Raises:
        ValueError: If task_id or body is empty.
    """
    if not task_id:
        raise ValueError("task_id is required")
    if not body or not body.strip():
        raise ValueError("body is required")

    comment = {
        "comment_id": f"CMT-{uuid.uuid4().hex[:8]}",
        "task_id": task_id,
        "author": author,
        "body": body.strip()[:5000],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # In-memory store (always)
    if task_id not in _comments_store:
        _comments_store[task_id] = []
    _comments_store[task_id].append(comment)

    # Anti-rot: cap per task
    if len(_comments_store[task_id]) > _MAX_COMMENTS_PER_TASK:
        _comments_store[task_id] = _comments_store[task_id][-_MAX_COMMENTS_PER_TASK:]

    # TypeDB persistence (best-effort)
    client = _get_typedb_client()
    if client:
        try:
            client.insert_comment(
                task_id=task_id,
                comment_id=comment["comment_id"],
                body=comment["body"],
                author=comment["author"],
                created_at=comment["created_at"],
            )
        except Exception as e:
            logger.debug("TypeDB comment persist failed: %s", e)

    record_audit(
        "COMMENT", "task", task_id,
        actor_id=author,
        metadata={"action": "add", "comment_id": comment["comment_id"]},
    )
    logger.info("Comment %s added to %s by %s", comment["comment_id"], task_id, author)
    return comment


def list_comments(
    task_id: str,
    offset: int = 0,
    limit: int = None,
) -> List[Dict[str, Any]]:
    """List comments for a task, chronologically (oldest first).

    Per SRVJ-FEAT-AUDIT-TRAIL-01 P8 (GAP 2): TypeDB read-through + merge.
    MCP servers (local processes) write comments to TypeDB but not to the
    container's in-memory _comments_store. This function merges both sources,
    deduplicating by comment_id (TypeDB wins on conflict).

    Fallback: if TypeDB is unavailable, returns in-memory only.

    Args:
        task_id: Task identifier.
        offset: Skip first N comments (default 0, negative treated as 0).
        limit: Max comments to return (default None = all).
    """
    memory_comments = _comments_store.get(task_id, [])

    # Try TypeDB read-through
    typedb_comments = []
    client = _get_typedb_client()
    if client:
        try:
            typedb_comments = client.get_comments_for_task(task_id)
        except Exception as e:
            logger.debug("TypeDB comment read failed for %s: %s", task_id, e)

    # Merge: TypeDB wins on conflict (dedup by comment_id)
    if typedb_comments:
        merged = {}
        # TypeDB first (authoritative)
        for c in typedb_comments:
            cid = c.get("comment_id")
            if cid:
                merged[cid] = c
        # In-memory: add only if not already in TypeDB (pending sync)
        for c in memory_comments:
            cid = c.get("comment_id")
            if cid and cid not in merged:
                merged[cid] = c
        # Sort chronologically (oldest first)
        comments = sorted(merged.values(), key=lambda c: c.get("created_at") or "")
    else:
        comments = list(memory_comments)

    # Pagination
    offset = max(0, offset)
    if limit is not None:
        limit = max(0, limit)
        return comments[offset:offset + limit]
    return comments[offset:]


def delete_comment(task_id: str, comment_id: str) -> bool:
    """Delete a comment by ID.

    Removes from in-memory store and TypeDB (best-effort).
    """
    comments = _comments_store.get(task_id, [])
    found = False
    for i, c in enumerate(comments):
        if c["comment_id"] == comment_id:
            comments.pop(i)
            found = True
            break

    if not found:
        return False

    # TypeDB delete (best-effort)
    client = _get_typedb_client()
    if client:
        try:
            client.delete_comment(comment_id)
        except Exception as e:
            logger.debug("TypeDB comment delete failed: %s", e)

    record_audit(
        "COMMENT", "task", task_id,
        actor_id="system",
        metadata={"action": "delete", "comment_id": comment_id},
    )
    logger.info("Comment %s deleted from %s", comment_id, task_id)
    return True


def get_comment(task_id: str, comment_id: str) -> Optional[Dict[str, Any]]:
    """Get a single comment by ID."""
    for c in _comments_store.get(task_id, []):
        if c["comment_id"] == comment_id:
            return c
    return None
