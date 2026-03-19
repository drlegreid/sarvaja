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
    except Exception as e:
        # BUG-MONITOR-SILENT-001: Log instead of silently swallowing
        # BUG-420-MON-002: Add exc_info for stack trace preservation
        # BUG-464-SES-001: Sanitize logger message — exc_info=True already captures full stack
        logger.warning(f"Monitor event failed for session {session_id}: {type(e).__name__}", exc_info=True)


def _is_test_artifact(session: dict) -> bool:
    """Check if session was created by automated tests (not real work).

    Synced with heuristic_checks_session.py _INTEGRATION_TEST_PATTERNS.
    """
    sid = session.get("session_id", "")
    agent_id = session.get("agent_id", "")
    # Exact test session IDs from conftest and unit tests
    if sid in ("SESSION-FAIL", "SESSION-TEST"):
        return True
    # Integration test patterns (from heuristic_checks_session.py)
    test_patterns = (
        "-CHAT-TEST", "-CHAT-FAIL", "-CHAT-BOOM", "-CHAT-NO-TOOLS",
        "-CHAT-NO-THOUGHTS", "-CHAT-DELETE", "-CHAT-FALLBACK",
        "-CHAT-COMPLETE-SESSION", "-CHAT-CVP",
        "-CHAT-FULL-LIFECYCLE", "-CHAT-REVIEWING",
        "-CHAT-HELLO", "-CHAT-LINKING", "-CHAT-VERIFY",
        "-CHAT-TESTING", "-CHAT-SUMMARY", "-CHAT--STATUS",
        "-CHAT--HELP", "-CHAT-STORE-", "-CHAT-TYPEDB-",
        "-CHAT-RESILIENT", "-CHAT-DONE", "-CHAT-ORPHAN",
        "-CHAT-AAA", "-CHAT-BBB", "-CHAT-CCC",
        "-CHAT-HEURISTIC-", "-CHAT-SESSION-BRIDGE",
        "-INTTEST-", "E2E-TEST-",
        # CC test probe patterns (P2-10e)
        "-CC-TEST-", "-CC-PROBE-",
    )
    if any(p in sid for p in test_patterns):
        return True
    # Test agent IDs (from integration conftest)
    test_agents = ("test-agent", "e2e-test-agent", "inttest-agent")
    return agent_id in test_agents


def list_sessions(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    sort_by: str = "started_at",
    order: str = "desc",
    offset: int = 0,
    limit: int = 50,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    exclude_test: bool = False,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """List sessions with pagination, sorting, filtering.

    Args:
        exclude_test: If True, filter out sessions created by automated tests.
        search: Keyword search across session_id, description, agent_id.

    Returns:
        Dict with 'items' (list of session dicts) and pagination metadata.
    """
    # BUG-295-SES-001: Enforce bounds at service layer (defense-in-depth beyond route)
    offset = max(0, offset)
    limit = max(1, min(limit, 500))
    # BUG-295-SES-002: Cap search string to prevent O(n * len) DoS
    if search and len(search) > 500:
        search = search[:500]
    # BUG-354-SES-001: Whitelist status values to prevent injection/bypass
    _VALID_STATUSES = {"ACTIVE", "COMPLETED", "ENDED", "FAILED", "CANCELLED"}
    if status and status.upper() not in _VALID_STATUSES:
        status = None  # Ignore invalid status silently

    sessions = get_all_sessions_from_typedb(allow_fallback=True)

    if exclude_test:
        sessions = [s for s in sessions if not _is_test_artifact(s)]
    if status:
        sessions = [s for s in sessions if s.get("status") == status]
    if agent_id:
        sessions = [s for s in sessions if s.get("agent_id") == agent_id]
    if date_from:
        sessions = [s for s in sessions if (s.get("start_time") or "")[:10] >= date_from]
    if date_to:
        sessions = [s for s in sessions if (s.get("start_time") or "")[:10] <= date_to]
    if search:
        q = search.lower()
        sessions = [
            s for s in sessions
            if q in (s.get("session_id") or "").lower()
            or q in (s.get("description") or "").lower()
            or q in (s.get("agent_id") or "").lower()
            or q in (s.get("cc_project_slug") or "").lower()
            or q in (s.get("cc_git_branch") or "").lower()
            or q in (s.get("cc_external_name") or "").lower()
        ]

    valid_sort_fields = ["started_at", "session_id", "status", "start_time"]
    sort_field = sort_by if sort_by in valid_sort_fields else "started_at"
    if sort_field == "started_at":
        sort_field = "start_time"
    is_desc = order.lower() == "desc"
    # Sort with nulls last (desc) or nulls first (asc):
    # Key tuple: (has_value_flag, value). With reverse=True, 1 > 0 so real values come first.
    sessions.sort(
        key=lambda s: (
            0 if (s.get(sort_field) is None or s.get(sort_field) == "") else 1,
            s.get(sort_field) or "",
        ),
        reverse=is_desc,
    )

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
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    status: Optional[str] = None,
    cc_session_uuid: Optional[str] = None,
    cc_project_slug: Optional[str] = None,
    cc_git_branch: Optional[str] = None,
    cc_tool_count: Optional[int] = None,
    cc_thinking_chars: Optional[int] = None,
    cc_compaction_count: Optional[int] = None,
    cc_external_name: Optional[str] = None,
    **kwargs,
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
                start_time=start_time,
                end_time=end_time,
                status=status,
                cc_session_uuid=cc_session_uuid,
                cc_project_slug=cc_project_slug,
                cc_git_branch=cc_git_branch,
                cc_tool_count=cc_tool_count,
                cc_thinking_chars=cc_thinking_chars,
                cc_compaction_count=cc_compaction_count,
                cc_external_name=cc_external_name,
            )
            if created:
                record_audit("CREATE", "session", session_id,
                             actor_id=agent_id or "system",
                             metadata={"description": description, "source": source})
                _monitor("create", session_id, source=source)
                log_event("session", "create", session_id=session_id, agent_id=agent_id, source=source)
                # BUG-SESSION-PYDANTIC-001: session_to_response returns SessionResponse
                # (Pydantic model), which doesn't support __setitem__. The subscript
                # assignment was silently crashing, causing TypeDB creates to fall
                # through to in-memory fallback despite successful TypeDB write.
                return session_to_response(created)
        except Exception as e:
            # BUG-408-SES-001: Add exc_info for stack trace preservation
            # BUG-464-SES-002: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB session insert failed, using fallback: {type(e).__name__}", exc_info=True)

    # Fallback to in-memory
    if session_id in _sessions_store:
        raise ValueError(f"Session {session_id} already exists")

    session_data = {
        "session_id": session_id,
        "start_time": start_time or datetime.now().isoformat(),
        "end_time": end_time,
        "status": status or "ACTIVE",
        "tasks_completed": 0,
        "description": description,
        "agent_id": agent_id,
        "cc_session_uuid": cc_session_uuid,
        "cc_project_slug": cc_project_slug,
        "cc_git_branch": cc_git_branch,
        "cc_tool_count": cc_tool_count,
        "cc_thinking_chars": cc_thinking_chars,
        "cc_compaction_count": cc_compaction_count,
        "cc_external_name": cc_external_name,
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
    cc_external_name: Optional[str] = None,
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
                cc_external_name=cc_external_name,
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
            # BUG-408-SES-002: Add exc_info for stack trace preservation
            # BUG-464-SES-003: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB session update failed, using fallback: {type(e).__name__}", exc_info=True)

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
    # BUG-SESSION-002: CC fields must also update in fallback path
    if cc_session_uuid is not None:
        session["cc_session_uuid"] = cc_session_uuid
    if cc_project_slug is not None:
        session["cc_project_slug"] = cc_project_slug
    if cc_git_branch is not None:
        session["cc_git_branch"] = cc_git_branch
    if cc_tool_count is not None:
        session["cc_tool_count"] = cc_tool_count
    if cc_thinking_chars is not None:
        session["cc_thinking_chars"] = cc_thinking_chars
    if cc_compaction_count is not None:
        session["cc_compaction_count"] = cc_compaction_count
    if cc_external_name is not None:
        session["cc_external_name"] = cc_external_name

    # BUG-AUDIT-NULL-001: Use old_status when status is None (matches TypeDB path)
    record_audit("UPDATE", "session", session_id,
                 actor_id=agent_id or "system",
                 old_value=old_status, new_value=status if status is not None else old_status,
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
            # BUG-SYNC-FIELDS-001: Pass CC fields atomically to insert_session
            client.insert_session(
                session_id=session_id,
                description=session_data.get("description", ""),
                agent_id=session_data.get("agent_id"),
                cc_session_uuid=session_data.get("cc_session_uuid"),
                cc_project_slug=session_data.get("cc_project_slug"),
                cc_git_branch=session_data.get("cc_git_branch"),
                cc_tool_count=session_data.get("cc_tool_count"),
                cc_thinking_chars=session_data.get("cc_thinking_chars"),
                cc_compaction_count=session_data.get("cc_compaction_count"),
                cc_external_name=session_data.get("cc_external_name"),
                start_time=session_data.get("start_time"),
                end_time=session_data.get("end_time"),
                status=session_data.get("status"),
            )
            # Sync status if present (handled by insert_session now but kept for compat)
            status_val = session_data.get("status")
            if status_val:
                try:
                    client.update_session(session_id, status=status_val)
                except Exception as se:
                    # BUG-SYNC-STATUS-SILENT-001: Log instead of silent pass
                    # BUG-436-SES-001: Add exc_info for stack trace preservation
                    # BUG-464-SES-004: Sanitize logger message — exc_info=True already captures full stack
                    logger.warning(f"Status sync failed for {session_id} (insert OK): {type(se).__name__}", exc_info=True)
            # BUG-205-SYNC-001: Mark as persisted to prevent duplicate in next list
            if session_id in _sessions_store:
                _sessions_store[session_id]["persistence_status"] = "persisted"
            synced += 1
            logger.info(f"Synced orphan session to TypeDB: {session_id}")
        except Exception as e:
            failed += 1
            # BUG-408-SES-003: Add exc_info for stack trace preservation
            # BUG-464-SES-005: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"Failed to sync session {session_id}: {type(e).__name__}", exc_info=True)

    return {
        "synced": synced,
        "failed": failed,
        "already_persisted": already_persisted,
    }
