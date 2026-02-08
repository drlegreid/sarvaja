"""Task Service Layer - Single code path for all task operations.

Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.

Created: 2026-02-01
"""
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Optional, Dict, Any, List

from governance.stores import (
    get_typedb_client,
    get_all_tasks_from_typedb,
    _tasks_store,
    task_to_response,
)
from governance.stores.audit import record_audit

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


def list_tasks(
    status: Optional[str] = None,
    phase: Optional[str] = None,
    agent_id: Optional[str] = None,
    sort_by: str = "task_id",
    order: str = "asc",
    offset: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """List tasks with pagination, sorting, filtering.

    Returns:
        Dict with 'items' (list of task dicts) and 'pagination' metadata.

    Raises:
        ConnectionError: If TypeDB unavailable and no fallback data.
    """
    tasks = get_all_tasks_from_typedb(
        status=status, phase=phase, agent_id=agent_id, allow_fallback=True
    )
    total = len(tasks)
    sort_field = sort_by if sort_by in ("task_id", "status", "phase", "name") else "task_id"
    tasks.sort(key=lambda t: t.get(sort_field) or "", reverse=order.lower() == "desc")
    paginated = tasks[offset: offset + limit]
    return {
        "items": paginated,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(paginated)) < total,
    }


def create_task(
    task_id: str,
    description: str = "",
    status: str = "OPEN",
    phase: str = "P10",
    agent_id: Optional[str] = None,
    body: Optional[str] = None,
    gap_id: Optional[str] = None,
    linked_rules: Optional[List[str]] = None,
    linked_sessions: Optional[List[str]] = None,
    source: str = "rest",
) -> Dict[str, Any]:
    """Create a task in TypeDB with fallback to in-memory store.

    Returns:
        Task dict on success.

    Raises:
        ValueError: If task already exists.
    """
    client = get_typedb_client()
    if client:
        try:
            if client.get_task(task_id):
                raise ValueError(f"Task {task_id} already exists")
            created = client.insert_task(
                task_id=task_id, name=description, status=status,
                phase=phase, body=body, gap_id=gap_id,
                linked_rules=linked_rules, linked_sessions=linked_sessions,
                agent_id=agent_id,
            )
            if created:
                record_audit("CREATE", "task", task_id,
                             actor_id=agent_id or "system",
                             metadata={"phase": phase, "status": status, "source": source})
                _monitor("create", task_id, source=source, status=status, phase=phase)
                return task_to_response(created)
        except ValueError:
            raise
        except Exception as e:
            logger.warning(f"TypeDB task insert failed, using fallback: {e}")

    # Fallback to in-memory store
    if task_id in _tasks_store:
        raise ValueError(f"Task {task_id} already exists")

    task_data = {
        "task_id": task_id, "description": description, "phase": phase,
        "status": status, "agent_id": agent_id, "body": body,
        "linked_rules": linked_rules, "linked_sessions": linked_sessions,
        "gap_id": gap_id, "created_at": datetime.now().isoformat(),
    }
    _tasks_store[task_id] = task_data
    record_audit("CREATE", "task", task_id,
                 actor_id=agent_id or "system",
                 metadata={"phase": phase, "status": status, "source": source})
    _monitor("create", task_id, source=source, status=status, phase=phase)
    return task_data


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Get a task by ID from TypeDB or fallback store.

    Returns:
        Task dict or None if not found.
    """
    client = get_typedb_client()
    if client:
        try:
            task = client.get_task(task_id)
            if task:
                return task_to_response(task)
        except Exception as e:
            logger.warning(f"TypeDB task get failed, using fallback: {e}")
    if task_id in _tasks_store:
        return dict(_tasks_store[task_id])
    return None


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
