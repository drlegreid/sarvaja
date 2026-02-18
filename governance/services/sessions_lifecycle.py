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
from governance.services.session_evidence import generate_session_evidence

logger = logging.getLogger(__name__)

__all__ = [
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
    except Exception as e:
        # BUG-MONITOR-SILENT-001: Log instead of silently swallowing
        # BUG-420-MON-003: Add exc_info for stack trace preservation
        # BUG-464-SLC-001: Sanitize logger message — exc_info=True already captures full stack
        logger.warning(f"Monitor event failed for session {session_id}: {type(e).__name__}", exc_info=True)


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
            # BUG-408-SLC-001: Add exc_info for stack trace preservation
            # BUG-464-SLC-002: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB session delete failed, using fallback: {type(e).__name__}", exc_info=True)

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
                # BUG-228-SESSIONS-003: Guard against double-complete in TypeDB path
                # BUG-385-LCY-001: Handle both dict and dataclass session objects
                _status = session.get("status") if isinstance(session, dict) else getattr(session, 'status', None)
                if _status == "COMPLETED":
                    raise ValueError(f"Session {session_id} already completed")
                updated = client.end_session(session_id)
                if updated:
                    # BUG-261-LIFECYCLE-001: Capture end_time once for consistency
                    end_time_str = datetime.now().isoformat()
                    # Auto-generate evidence when none provided (P0 fix)
                    if evidence_files is None:
                        try:
                            # BUG-189-001: Use dataclasses.asdict for Session entity, not dict()
                            import dataclasses
                            session_dict = dataclasses.asdict(session) if not isinstance(session, dict) else session
                            # BUG-213-LIFECYCLE-UPDATE-001: Merge store FIRST, then set
                            # status/end_time to prevent stale "ACTIVE" overwrite
                            if session_id in _sessions_store:
                                session_dict.update(_sessions_store[session_id])
                            session_dict["status"] = "COMPLETED"
                            session_dict["end_time"] = end_time_str
                            auto_path = generate_session_evidence(session_dict)
                            if auto_path:
                                evidence_files = [auto_path]
                                logger.info(f"Auto-generated evidence: {auto_path}")
                        except Exception as ae:
                            # BUG-408-SLC-002: Add exc_info for stack trace preservation
                            # BUG-464-SLC-003: Sanitize logger message — exc_info=True already captures full stack
                            logger.warning(f"Auto-evidence failed: {type(ae).__name__}", exc_info=True)
                    # BUG-SESSION-EVIDENCE-001: Link evidence to TypeDB
                    if evidence_files:
                        for ef in evidence_files:
                            try:
                                client.link_evidence_to_session(session_id, ef)
                            except Exception as le:
                                # BUG-LIFECYCLE-EVIDENCE-LOG-001: WARNING not DEBUG — data integrity
                                # BUG-436-SLC-001: Add exc_info for stack trace preservation
                                # BUG-464-SLC-004: Sanitize logger message — exc_info=True already captures full stack
                                logger.warning(f"TypeDB evidence link failed {session_id}->{ef}: {type(le).__name__}", exc_info=True)
                    # Also update _sessions_store for consistent fallback
                    # (TypeDB derives tasks_completed from relations, but chat
                    # sessions store tool_call count here for API visibility)
                    if session_id in _sessions_store:
                        _sessions_store[session_id]["status"] = "COMPLETED"
                        _sessions_store[session_id]["end_time"] = end_time_str
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
        except ValueError:
            # BUG-242-LCY-001: Re-raise ValueError (double-complete) instead of swallowing
            raise
        except Exception as e:
            # BUG-408-SLC-003: Add exc_info for stack trace preservation
            # BUG-464-SLC-005: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB session end failed, using fallback: {type(e).__name__}", exc_info=True)

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

    # Auto-generate evidence when none provided (P0 architectural fix)
    if evidence_files is None:
        try:
            auto_path = generate_session_evidence(session)
            if auto_path:
                evidence_files = [auto_path]
                logger.info(f"Auto-generated evidence for {session_id}: {auto_path}")
        except Exception as e:
            # BUG-420-SLC-001: Add exc_info for stack trace preservation
            # BUG-464-SLC-006: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"Auto-evidence generation failed for {session_id}: {type(e).__name__}", exc_info=True)

    if evidence_files is not None:
        session["evidence_files"] = evidence_files

    record_audit("UPDATE", "session", session_id,
                 old_value="ACTIVE", new_value="COMPLETED",
                 metadata={"action": "end_session", "source": source})
    _monitor("end", session_id, source=source)
    log_event("session", "end", session_id=session_id, source=source)
    return dict(session)
