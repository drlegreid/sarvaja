"""Session Service Lifecycle — end_session and delete_session operations.

Per DOC-SIZE-01-v1: Extracted from sessions.py.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from governance.stores import (
    get_typedb_client,
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
