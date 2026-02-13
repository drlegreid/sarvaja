"""Session Service Layer - Single code path for all session operations.

Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.
Per DOC-SIZE-01-v1: Lifecycle operations in sessions_lifecycle.py.

Created: 2026-02-01
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from governance.stores import (
    get_typedb_client,
    get_all_sessions_from_typedb,
    get_session_from_typedb,
    _sessions_store,
    session_to_response,
)
from governance.stores.audit import record_audit
from governance.middleware.event_log import log_event

# Re-export for backward compatibility
from governance.services.sessions_lifecycle import (  # noqa: F401
    delete_session,
    end_session,
)

logger = logging.getLogger(__name__)

__all__ = [
    "list_sessions",
    "create_session",
    "get_session",
    "update_session",
    "sync_pending_sessions",
    # Re-exports from sessions_lifecycle
    "delete_session",
    "end_session",
]


def _monitor(action: str, session_id: str, source: str = "service", **extra):
    """Log session monitoring event for MCP compliance."""
    try:
        from governance.mcp_tools.common import log_monitor_event
        log_monitor_event(
            event_type="session_event",
            source=source,
            details={"session_id": session_id, "action": action, **extra},
            severity="INFO",
        )
    except Exception:
        pass


def list_sessions(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    sort_by: str = "started_at",
    order: str = "desc",
    offset: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """List sessions with pagination, sorting, filtering.

    Returns:
        Dict with 'items' (list of session dicts) and pagination metadata.
    """
    sessions = get_all_sessions_from_typedb(allow_fallback=True)

    if status:
        sessions = [s for s in sessions if s.get("status") == status]
    if agent_id:
        sessions = [s for s in sessions if s.get("agent_id") == agent_id]

    valid_sort_fields = ["started_at", "session_id", "status", "start_time"]
    sort_field = sort_by if sort_by in valid_sort_fields else "started_at"
    if sort_field == "started_at":
        sort_field = "start_time"
    sessions.sort(key=lambda s: s.get(sort_field) or "", reverse=order.lower() == "desc")

    total = len(sessions)
    paginated = sessions[offset: offset + limit]
    return {
        "items": paginated,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(paginated)) < total,
    }


def create_session(
    session_id: Optional[str] = None,
    description: str = "",
    agent_id: Optional[str] = None,
    source: str = "rest",
    cc_session_uuid: Optional[str] = None,
    cc_project_slug: Optional[str] = None,
    cc_git_branch: Optional[str] = None,
    cc_tool_count: Optional[int] = None,
    cc_thinking_chars: Optional[int] = None,
    cc_compaction_count: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a session in TypeDB with fallback to in-memory store.

    Returns:
        Session dict on success.

    Raises:
        ValueError: If session already exists.
    """
    if not session_id:
        session_id = f"SESSION-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6].upper()}"

    client = get_typedb_client()
    if client:
        try:
            created = client.insert_session(
                session_id=session_id,
                description=description,
                agent_id=agent_id,
                cc_session_uuid=cc_session_uuid,
                cc_project_slug=cc_project_slug,
                cc_git_branch=cc_git_branch,
                cc_tool_count=cc_tool_count,
                cc_thinking_chars=cc_thinking_chars,
                cc_compaction_count=cc_compaction_count,
            )
            if created:
                record_audit("CREATE", "session", session_id,
                             actor_id=agent_id or "system",
                             metadata={"description": description, "source": source})
                _monitor("create", session_id, source=source)
                log_event("session", "create", session_id=session_id, agent_id=agent_id, source=source)
                result = session_to_response(created)
                result["persistence_status"] = "persisted"
                return result
        except Exception as e:
            logger.warning(f"TypeDB session insert failed, using fallback: {e}")

    # Fallback to in-memory
    if session_id in _sessions_store:
        raise ValueError(f"Session {session_id} already exists")

    session_data = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat(),
        "status": "ACTIVE",
        "tasks_completed": 0,
        "description": description,
        "agent_id": agent_id,
        "cc_session_uuid": cc_session_uuid,
        "cc_project_slug": cc_project_slug,
        "cc_git_branch": cc_git_branch,
        "cc_tool_count": cc_tool_count,
        "cc_thinking_chars": cc_thinking_chars,
        "cc_compaction_count": cc_compaction_count,
        "persistence_status": "memory_only",
    }
    _sessions_store[session_id] = session_data
    record_audit("CREATE", "session", session_id,
                 actor_id=agent_id or "system",
                 metadata={"description": description, "source": source})
    _monitor("create", session_id, source=source)
    log_event("session", "create", session_id=session_id, agent_id=agent_id, source=source)
    return session_data


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get a session by ID from TypeDB or fallback store.

    Returns:
        Session dict or None if not found.
    """
    session = get_session_from_typedb(session_id, allow_fallback=True)
    return session


def update_session(
    session_id: str,
    description: Optional[str] = None,
    status: Optional[str] = None,
    tasks_completed: Optional[int] = None,
    agent_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    source: str = "rest",
    cc_session_uuid: Optional[str] = None,
    cc_project_slug: Optional[str] = None,
    cc_git_branch: Optional[str] = None,
    cc_tool_count: Optional[int] = None,
    cc_thinking_chars: Optional[int] = None,
    cc_compaction_count: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Update session fields in TypeDB with fallback.

    Returns:
        Updated session dict or None if not found.
    """
    client = get_typedb_client()

    if client:
        try:
            existing = client.get_session(session_id)
            if not existing:
                return None
            updated = client.update_session(
                session_id=session_id,
                description=description,
                status=status,
                tasks_completed=tasks_completed,
                agent_id=agent_id,
                start_time=start_time,
                end_time=end_time,
                cc_session_uuid=cc_session_uuid,
                cc_project_slug=cc_project_slug,
                cc_git_branch=cc_git_branch,
                cc_tool_count=cc_tool_count,
                cc_thinking_chars=cc_thinking_chars,
                cc_compaction_count=cc_compaction_count,
            )
            if updated:
                old_status = getattr(existing, 'status', None) if hasattr(existing, 'status') else existing.get("status")
                record_audit("UPDATE", "session", session_id,
                             actor_id=agent_id or "system",
                             old_value=old_status,
                             new_value=status or old_status,
                             metadata={"description": description, "source": source})
                _monitor("update", session_id, source=source, status=status)
                log_event("session", "update", session_id=session_id, status=status, source=source)
                return session_to_response(updated)
        except Exception as e:
            logger.warning(f"TypeDB session update failed, using fallback: {e}")

    # Fallback to in-memory
    if session_id not in _sessions_store:
        return None

    session = _sessions_store[session_id]
    old_status = session.get("status")
    if description is not None:
        session["description"] = description
    if status is not None:
        session["status"] = status
    if tasks_completed is not None:
        session["tasks_completed"] = tasks_completed
    if agent_id is not None:
        session["agent_id"] = agent_id
    if start_time is not None:
        session["start_time"] = start_time
    if end_time is not None:
        session["end_time"] = end_time

    record_audit("UPDATE", "session", session_id,
                 actor_id=agent_id or "system",
                 old_value=old_status, new_value=status,
                 metadata={"source": source})
    _monitor("update", session_id, source=source, status=status)
    log_event("session", "update", session_id=session_id, status=status, source=source)
    return dict(session)


def sync_pending_sessions() -> Dict[str, Any]:
    """Push memory-only sessions to TypeDB.

    Per Phase-1 Data Integrity: Retries sessions that failed initial
    TypeDB persistence. Called on-demand via API or at session end.

    Returns:
        Dict with synced/failed/already_persisted/error counts.
    """
    client = get_typedb_client()
    if not client:
        return {"error": "TypeDB unavailable", "synced": 0, "failed": 0}

    synced = 0
    failed = 0
    already_persisted = 0

    for session_id, session_data in list(_sessions_store.items()):
        try:
            existing = client.get_session(session_id)
            if existing:
                already_persisted += 1
                continue
            client.insert_session(
                session_id=session_id,
                description=session_data.get("description", ""),
                agent_id=session_data.get("agent_id"),
            )
            synced += 1
            logger.info(f"Synced orphan session to TypeDB: {session_id}")
        except Exception as e:
            failed += 1
            logger.warning(f"Failed to sync session {session_id}: {e}")

    return {
        "synced": synced,
        "failed": failed,
        "already_persisted": already_persisted,
    }
