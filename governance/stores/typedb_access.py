"""
Governance Stores - TypeDB Data Access Functions.

Per RULE-032: Modularized from stores.py (503 lines).
Contains: TypeDB-first data access for tasks and sessions.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from .config import get_typedb_client
from .data_stores import (
    TypeDBUnavailable,
    _tasks_store,
    _sessions_store,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TYPEDB-FIRST DATA ACCESS (Per GAP-STUB-001/002/003/004)
# =============================================================================

def get_all_tasks_from_typedb(
    status: str = None,
    phase: str = None,
    agent_id: str = None,
    allow_fallback: bool = False
) -> List[Dict[str, Any]]:
    """
    Get all tasks from TypeDB (source of truth).

    Per GAP-STUB-001/002: TypeDB is the primary data source for tasks.

    Args:
        status: Optional filter by status
        phase: Optional filter by phase
        agent_id: Optional filter by agent
        allow_fallback: If True, fallback to in-memory when TypeDB unavailable

    Returns:
        List of task dicts

    Raises:
        TypeDBUnavailable: If TypeDB is down and allow_fallback=False
    """
    client = get_typedb_client()

    if client:
        try:
            tasks = client.get_all_tasks(status=status, phase=phase, agent_id=agent_id)
            # Convert to dict format for API compatibility
            result = [_task_to_dict(t) for t in tasks]
            # Merge evidence from in-memory store (EPIC-DR-008 workaround for Python 3.13)
            for task_dict in result:
                task_id = task_dict.get("task_id")
                if task_id and task_id in _tasks_store:
                    mem_evidence = _tasks_store[task_id].get("evidence")
                    if mem_evidence and not task_dict.get("evidence"):
                        task_dict["evidence"] = mem_evidence
            return result
        except Exception as e:
            logger.warning(f"TypeDB task query failed: {e}")
            if not allow_fallback:
                raise TypeDBUnavailable(f"TypeDB unavailable: {e}")

    if allow_fallback:
        # Fallback to in-memory (deprecated path)
        logger.warning("Using deprecated in-memory fallback for tasks")
        tasks = list(_tasks_store.values())
        if phase:
            tasks = [t for t in tasks if t.get("phase") == phase]
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        if agent_id:
            tasks = [t for t in tasks if t.get("agent_id") == agent_id]
        return tasks

    raise TypeDBUnavailable("TypeDB client not available")


def get_task_from_typedb(task_id: str, allow_fallback: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a specific task from TypeDB.

    Per GAP-STUB-001/002: TypeDB is the primary data source for tasks.
    """
    client = get_typedb_client()

    if client:
        try:
            task = client.get_task(task_id)
            if task:
                return _task_to_dict(task)
            return None
        except Exception as e:
            logger.warning(f"TypeDB task get failed: {e}")
            if not allow_fallback:
                raise TypeDBUnavailable(f"TypeDB unavailable: {e}")

    if allow_fallback:
        logger.warning("Using deprecated in-memory fallback for task get")
        return _tasks_store.get(task_id)

    raise TypeDBUnavailable("TypeDB client not available")


def get_all_sessions_from_typedb(allow_fallback: bool = False) -> List[Dict[str, Any]]:
    """
    Get all sessions from TypeDB (source of truth).

    Per GAP-STUB-003/004: TypeDB is the primary data source for sessions.
    Per Phase-1 Data Integrity: Merges in-memory orphan sessions that
    failed to persist to TypeDB, tagged with persistence_status.
    """
    client = get_typedb_client()

    if client:
        try:
            sessions = client.get_all_sessions()
            result = [_session_to_dict(s) for s in sessions]
            for s in result:
                s["persistence_status"] = "persisted"
            # Merge orphan sessions from _sessions_store (memory-only)
            if allow_fallback:
                typedb_ids = {s["session_id"] for s in result}
                for mem_session in _sessions_store.values():
                    sid = mem_session.get("session_id")
                    if sid and sid not in typedb_ids:
                        orphan = dict(mem_session)
                        orphan["persistence_status"] = "memory_only"
                        result.append(orphan)
            return result
        except Exception as e:
            logger.warning(f"TypeDB session query failed: {e}")
            if not allow_fallback:
                raise TypeDBUnavailable(f"TypeDB unavailable: {e}")

    if allow_fallback:
        logger.warning("Using deprecated in-memory fallback for sessions")
        result = []
        for s in _sessions_store.values():
            entry = dict(s)
            entry["persistence_status"] = "memory_only"
            result.append(entry)
        return result

    raise TypeDBUnavailable("TypeDB client not available")


def get_session_from_typedb(session_id: str, allow_fallback: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a specific session from TypeDB.

    Per GAP-STUB-003/004: TypeDB is the primary data source for sessions.
    """
    client = get_typedb_client()

    if client:
        try:
            session = client.get_session(session_id)
            if session:
                return _session_to_dict(session)
            return None
        except Exception as e:
            logger.warning(f"TypeDB session get failed: {e}")
            if not allow_fallback:
                raise TypeDBUnavailable(f"TypeDB unavailable: {e}")

    if allow_fallback:
        logger.warning("Using deprecated in-memory fallback for session get")
        return _sessions_store.get(session_id)

    raise TypeDBUnavailable("TypeDB client not available")


def get_task_count(allow_fallback: bool = True) -> int:
    """Get total task count from TypeDB or fallback."""
    try:
        tasks = get_all_tasks_from_typedb(allow_fallback=allow_fallback)
        return len(tasks)
    except TypeDBUnavailable:
        return 0


def get_session_count(allow_fallback: bool = True) -> int:
    """Get total session count from TypeDB or fallback."""
    try:
        sessions = get_all_sessions_from_typedb(allow_fallback=allow_fallback)
        return len(sessions)
    except TypeDBUnavailable:
        return 0


def _task_to_dict(task) -> Dict[str, Any]:
    """Convert TypeDB Task entity to dict format.

    GAP-DATA-001: Ensure description has content from body if description is empty.
    Priority: body > description > name (for UI display)
    """
    return {
        "task_id": task.id,
        "name": task.name or "",  # Short title
        "description": task.body or task.description or task.name or "",  # Detailed content
        "phase": task.phase,
        "status": task.status,
        "agent_id": task.agent_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "claimed_at": task.claimed_at.isoformat() if task.claimed_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "body": task.body,
        "linked_rules": task.linked_rules,
        "linked_sessions": task.linked_sessions,
        "gap_id": task.gap_id,
        "evidence": task.evidence,
        "document_path": task.document_path
    }


def _session_to_dict(session) -> Dict[str, Any]:
    """Convert TypeDB Session entity to dict format."""
    return {
        "session_id": session.id,
        "start_time": session.started_at.isoformat() if session.started_at else datetime.now().isoformat(),
        "end_time": session.completed_at.isoformat() if session.completed_at else None,
        "status": session.status,
        "tasks_completed": session.tasks_completed or 0,
        "agent_id": session.agent_id,
        "description": session.description,
        "file_path": session.file_path,
        "evidence_files": session.evidence_files,
        "linked_rules_applied": session.linked_rules_applied,
        "linked_decisions": session.linked_decisions,
        # Claude Code session attributes (SESSION-CC-01-v1)
        "cc_session_uuid": getattr(session, 'cc_session_uuid', None),
        "cc_project_slug": getattr(session, 'cc_project_slug', None),
        "cc_git_branch": getattr(session, 'cc_git_branch', None),
        "cc_tool_count": getattr(session, 'cc_tool_count', None),
        "cc_thinking_chars": getattr(session, 'cc_thinking_chars', None),
        "cc_compaction_count": getattr(session, 'cc_compaction_count', None),
        "project_id": getattr(session, 'project_id', None),
    }
