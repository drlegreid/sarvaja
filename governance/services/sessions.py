"""Session Service Layer — Hub module with re-exports.

Per DOC-SIZE-01-v1: CRUD ops in sessions_crud.py, lifecycle in sessions_lifecycle.py.
Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.

Created: 2026-02-01
"""
import logging
from typing import Dict, Any

from governance.stores import (
    get_typedb_client,
    _sessions_store,
)

# Re-export CRUD operations for backward compatibility
from governance.services.sessions_crud import (  # noqa: F401
    _is_test_artifact,
    list_sessions,
    create_session,
    get_session,
    update_session,
)

# Re-export lifecycle operations for backward compatibility
from governance.services.sessions_lifecycle import (  # noqa: F401
    delete_session,
    end_session,
)

logger = logging.getLogger(__name__)

__all__ = [
    # CRUD (from sessions_crud)
    "list_sessions",
    "create_session",
    "get_session",
    "update_session",
    # Lifecycle (from sessions_lifecycle)
    "delete_session",
    "end_session",
    # Local
    "sync_pending_sessions",
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
