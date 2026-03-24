"""Task Preload & Monitoring Utilities.

Per DOC-SIZE-01-v1: Extracted from tasks_mutations.py.
Shared by update/delete (hub) and linking operations.
"""
import logging

from governance.stores import get_typedb_client, _tasks_store

logger = logging.getLogger(__name__)


def _monitor(action: str, task_id: str, source: str = "service", **extra):
    """Log task monitoring event for MCP compliance."""
    try:
        from governance.mcp_tools.common import log_monitor_event
        log_monitor_event(
            event_type="task_event",
            source=source,
            details={"task_id": task_id, "action": action, **extra},
            severity="INFO",
        )
    except Exception as e:
        # BUG-MONITOR-SILENT-001: Log instead of silently swallowing
        # BUG-420-MON-004: Add exc_info for stack trace preservation
        # BUG-464-TM-001: Sanitize logger message — exc_info=True already captures full stack
        logger.warning(f"Monitor event failed for task {task_id}: {type(e).__name__}", exc_info=True)


def _preload_task_from_typedb(task_id: str) -> bool:
    """Preload task from TypeDB into _tasks_store for DONE gate validation.

    Per EPIC-TASK-QUALITY-V3 P14: Always refresh from TypeDB to pick up
    linked_documents/sessions added via MCP after initial creation.

    Returns True if task was loaded/refreshed, False otherwise.
    """
    client = get_typedb_client()
    if not client:
        return False
    task_obj = client.get_task(task_id)
    if not task_obj:
        return False

    _claimed = getattr(task_obj, 'claimed_at', None)
    _completed = getattr(task_obj, 'completed_at', None)
    _tasks_store[task_id] = {
        "task_id": task_id,
        "description": task_obj.name or getattr(task_obj, 'description', '') or "",
        "phase": task_obj.phase or "",
        "status": task_obj.status or "TODO",
        "agent_id": task_obj.agent_id,
        "created_at": task_obj.created_at.isoformat() if task_obj.created_at else None,
        "body": getattr(task_obj, 'body', None),
        "gap_id": getattr(task_obj, 'gap_id', None),
        "priority": getattr(task_obj, 'priority', None),
        "task_type": getattr(task_obj, 'task_type', None),
        "evidence": getattr(task_obj, 'evidence', None),
        "resolution": getattr(task_obj, 'resolution', None),
        "claimed_at": _claimed.isoformat() if _claimed else None,
        "completed_at": _completed.isoformat() if _completed else None,
        "document_path": getattr(task_obj, 'document_path', None),
        "linked_rules": getattr(task_obj, 'linked_rules', []) or [],
        "linked_sessions": getattr(task_obj, 'linked_sessions', []) or [],
        "linked_commits": getattr(task_obj, 'linked_commits', []) or [],
        "linked_documents": getattr(task_obj, 'linked_documents', []) or [],
        "summary": getattr(task_obj, 'summary', None) or task_obj.name,
        "workspace_id": getattr(task_obj, 'workspace_id', None),
    }
    logger.info(f"[DONE-GATE] Pre-loaded task {task_id} from TypeDB into _tasks_store")
    return True
