"""Task Service Mutations — update, delete, and linking operations.

Per DOC-SIZE-01-v1: Extracted from tasks.py.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from governance.stores import (
    get_typedb_client,
    _tasks_store,
    task_to_response,
)
from governance.stores.audit import record_audit
from governance.middleware.event_log import log_event

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
    except Exception:
        pass


def update_task(
    task_id: str,
    description: Optional[str] = None,
    status: Optional[str] = None,
    phase: Optional[str] = None,
    agent_id: Optional[str] = None,
    body: Optional[str] = None,
    evidence: Optional[str] = None,
    linked_rules: Optional[List[str]] = None,
    linked_sessions: Optional[List[str]] = None,
    gap_id: Optional[str] = None,
    source: str = "rest",
) -> Optional[Dict[str, Any]]:
    """Update task fields in TypeDB with fallback.

    Returns:
        Updated task dict or None if not found.
    """
    client = get_typedb_client()
    task_obj = None
    if client:
        try:
            task_obj = client.get_task(task_id)
            if not task_obj:
                return None
            if status or evidence:
                updated = client.update_task_status(
                    task_id, status or task_obj.status,
                    agent_id or task_obj.agent_id, evidence=evidence,
                )
                task_obj = updated or task_obj
            # Persist linked_sessions to TypeDB via relations
            if linked_sessions:
                for sid in linked_sessions:
                    try:
                        client.link_task_to_session(task_id, sid)
                    except Exception as le:
                        logger.debug(f"TypeDB session link {task_id}->{sid}: {le}")
        except Exception as e:
            logger.warning(f"TypeDB task update failed, using fallback: {e}")

    # Ensure task in fallback store
    if task_id not in _tasks_store:
        if client and task_obj:
            created_at = task_obj.created_at.isoformat() if task_obj.created_at else datetime.now().isoformat()
            _tasks_store[task_id] = {
                "task_id": task_id,
                "description": task_obj.name or getattr(task_obj, 'description', '') or "",
                "phase": task_obj.phase or "",
                "status": task_obj.status or "TODO",
                "agent_id": task_obj.agent_id,
                "created_at": created_at,
                "body": getattr(task_obj, 'body', None),
                "gap_id": getattr(task_obj, 'gap_id', None),
            }
        else:
            return None

    old_status = _tasks_store[task_id].get("status")

    # Per H-TASK-002: IN_PROGRESS tasks must have agent_id
    if status and status.upper() == "IN_PROGRESS" and not agent_id:
        existing_agent = _tasks_store[task_id].get("agent_id")
        if not existing_agent:
            agent_id = "code-agent"
            logger.warning(
                f"[H-TASK-002] Task {task_id} set to IN_PROGRESS without agent_id, "
                f"auto-assigning '{agent_id}'"
            )

    updates = {
        "description": description, "phase": phase, "status": status,
        "agent_id": agent_id, "body": body, "evidence": evidence,
        "linked_rules": linked_rules, "linked_sessions": linked_sessions,
        "gap_id": gap_id,
    }
    for field, val in updates.items():
        if val is not None:
            _tasks_store[task_id][field] = val
            if field == "status" and val == "DONE":
                _tasks_store[task_id]["completed_at"] = datetime.now().isoformat()

    record_audit("UPDATE", "task", task_id,
                 actor_id=agent_id or "system",
                 old_value=old_status, new_value=status,
                 metadata={"phase": phase, "source": source})
    _monitor("update", task_id, source=source, status=status, phase=phase)
    log_event("task", "update", task_id=task_id, old_status=old_status, status=status, source=source)
    return dict(_tasks_store[task_id])


def delete_task(task_id: str, source: str = "rest") -> bool:
    """Delete a task from TypeDB and fallback store.

    Returns:
        True if deleted, False if not found.
    """
    deleted = False
    client = get_typedb_client()
    if client:
        try:
            if client.get_task(task_id) and client.delete_task(task_id):
                deleted = True
        except Exception as e:
            logger.warning(f"TypeDB task delete failed, using fallback: {e}")

    if task_id in _tasks_store:
        del _tasks_store[task_id]
        deleted = True

    if deleted:
        record_audit("DELETE", "task", task_id, metadata={"source": source})
        _monitor("delete", task_id, source=source)
        log_event("task", "delete", task_id=task_id, source=source)
    return deleted


def link_task_to_rule(task_id: str, rule_id: str, source: str = "rest") -> bool:
    """Link task to rule via implements-rule relation."""
    client = get_typedb_client()
    if not client:
        return False
    try:
        if not client.get_task(task_id):
            return False
        result = client.link_task_to_rule(task_id, rule_id)
        if result:
            _monitor("link_rule", task_id, source=source, rule_id=rule_id)
        return bool(result)
    except Exception as e:
        logger.error(f"Failed to link task {task_id} to rule {rule_id}: {e}")
        return False


def link_task_to_session(task_id: str, session_id: str, source: str = "rest") -> bool:
    """Link task to session via completed-in relation."""
    client = get_typedb_client()
    if not client:
        return False
    try:
        if not client.get_task(task_id):
            return False
        result = client.link_task_to_session(task_id, session_id)
        if result:
            _monitor("link_session", task_id, source=source, session_id=session_id)
        return bool(result)
    except Exception as e:
        logger.error(f"Failed to link task {task_id} to session {session_id}: {e}")
        return False
