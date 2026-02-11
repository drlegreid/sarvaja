"""Session Service Layer - Single code path for all session operations.

Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.

Created: 2026-02-01
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from governance.stores import (
    get_typedb_client,
    get_all_sessions_from_typedb,
    get_session_from_typedb,
    _sessions_store,
    session_to_response,
)
from governance.stores.audit import record_audit
from governance.middleware.event_log import log_event

logger = logging.getLogger(__name__)


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
            )
            if created:
                record_audit("CREATE", "session", session_id,
                             actor_id=agent_id or "system",
                             metadata={"description": description, "source": source})
                _monitor("create", session_id, source=source)
                log_event("session", "create", session_id=session_id, agent_id=agent_id, source=source)
                return session_to_response(created)
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
    source: str = "rest",
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

    record_audit("UPDATE", "session", session_id,
                 actor_id=agent_id or "system",
                 old_value=old_status, new_value=status,
                 metadata={"source": source})
    _monitor("update", session_id, source=source, status=status)
    log_event("session", "update", session_id=session_id, status=status, source=source)
    return dict(session)


def delete_session(session_id: str, source: str = "rest") -> bool:
    """Delete a session from TypeDB and fallback store.

    Returns:
        True if deleted, False if not found.
    """
    deleted = False
    client = get_typedb_client()
    if client:
        try:
            existing = client.get_session(session_id)
            if existing and client.delete_session(session_id):
                deleted = True
        except Exception as e:
            logger.warning(f"TypeDB session delete failed, using fallback: {e}")

    if session_id in _sessions_store:
        del _sessions_store[session_id]
        deleted = True

    if deleted:
        record_audit("DELETE", "session", session_id, metadata={"source": source})
        _monitor("delete", session_id, source=source)
        log_event("session", "delete", session_id=session_id, source=source)
    return deleted


def end_session(
    session_id: str,
    tasks_completed: Optional[int] = None,
    evidence_files: Optional[List[str]] = None,
    source: str = "rest",
) -> Optional[Dict[str, Any]]:
    """End an active session.

    Returns:
        Updated session dict or None if not found.

    Raises:
        ValueError: If session already completed.
    """
    client = get_typedb_client()
    if client:
        try:
            session = client.get_session(session_id)
            if session:
                updated = client.end_session(session_id)
                if updated:
                    # Also update _sessions_store for consistent fallback
                    # (TypeDB derives tasks_completed from relations, but chat
                    # sessions store tool_call count here for API visibility)
                    if session_id in _sessions_store:
                        _sessions_store[session_id]["status"] = "COMPLETED"
                        _sessions_store[session_id]["end_time"] = datetime.now().isoformat()
                        if tasks_completed is not None:
                            _sessions_store[session_id]["tasks_completed"] = tasks_completed
                        if evidence_files is not None:
                            _sessions_store[session_id]["evidence_files"] = evidence_files
                    record_audit("UPDATE", "session", session_id,
                                 old_value="ACTIVE", new_value="COMPLETED",
                                 metadata={"action": "end_session", "source": source})
                    _monitor("end", session_id, source=source)
                    log_event("session", "end", session_id=session_id, source=source)
                    return session_to_response(updated)
                return None
        except Exception as e:
            logger.warning(f"TypeDB session end failed, using fallback: {e}")

    # Fallback to in-memory
    if session_id not in _sessions_store:
        return None

    session = _sessions_store[session_id]
    if session.get("status") == "COMPLETED":
        raise ValueError(f"Session {session_id} already completed")

    session["status"] = "COMPLETED"
    session["end_time"] = datetime.now().isoformat()
    if tasks_completed is not None:
        session["tasks_completed"] = tasks_completed
    if evidence_files is not None:
        session["evidence_files"] = evidence_files

    record_audit("UPDATE", "session", session_id,
                 old_value="ACTIVE", new_value="COMPLETED",
                 metadata={"action": "end_session", "source": source})
    _monitor("end", session_id, source=source)
    log_event("session", "end", session_id=session_id, source=source)
    return dict(session)
