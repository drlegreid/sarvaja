"""Task Comments Service — CRUD for resolution comments.

Per EPIC-ISSUE-EVIDENCE P19: Comment thread on tasks.
In-memory store with TypeDB persistence (best-effort write-through).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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

    logger.info("Comment %s added to %s by %s", comment["comment_id"], task_id, author)
    return comment


def list_comments(task_id: str) -> List[Dict[str, Any]]:
    """List all comments for a task, chronologically (oldest first).

    Reads from in-memory store (TypeDB is write-through backup).
    """
    return list(_comments_store.get(task_id, []))


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

    logger.info("Comment %s deleted from %s", comment_id, task_id)
    return True


def get_comment(task_id: str, comment_id: str) -> Optional[Dict[str, Any]]:
    """Get a single comment by ID."""
    for c in _comments_store.get(task_id, []):
        if c["comment_id"] == comment_id:
            return c
    return None
