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
from .helpers import compute_session_duration_from_timestamps
from .retry import retry_on_transient

logger = logging.getLogger(__name__)


def _typedb_query_tasks(client, **kwargs):
    """Execute TypeDB task query with retry on transient failures."""
    @retry_on_transient(max_attempts=2, base_delay=0.5)
    def _inner():
        return client.get_all_tasks(**kwargs)
    return _inner()


def _typedb_get_task(client, task_id):
    """Execute TypeDB single task get with retry."""
    @retry_on_transient(max_attempts=2, base_delay=0.5)
    def _inner():
        return client.get_task(task_id)
    return _inner()


def _typedb_query_sessions(client):
    """Execute TypeDB session query with retry."""
    @retry_on_transient(max_attempts=2, base_delay=0.5)
    def _inner():
        return client.get_all_sessions()
    return _inner()


def _typedb_get_session(client, session_id):
    """Execute TypeDB single session get with retry."""
    @retry_on_transient(max_attempts=2, base_delay=0.5)
    def _inner():
        return client.get_session(session_id)
    return _inner()


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
            tasks = _typedb_query_tasks(client, status=status, phase=phase, agent_id=agent_id)
            # Convert to dict format for API compatibility
            result = [_task_to_dict(t) for t in tasks]
            # Merge evidence from in-memory store (EPIC-DR-008 workaround for Python 3.13)
            typedb_ids = set()
            for task_dict in result:
                task_id = task_dict.get("task_id")
                typedb_ids.add(task_id)
                if task_id and task_id in _tasks_store:
                    mem_evidence = _tasks_store[task_id].get("evidence")
                    if mem_evidence and not task_dict.get("evidence"):
                        task_dict["evidence"] = mem_evidence
            # BUG-TASK-UI-001: Merge orphan memory tasks (not in TypeDB results)
            # Same pattern as sessions: get_all_sessions_from_typedb merges orphans
            for mem_id, mem_task in list(_tasks_store.items()):
                if mem_id not in typedb_ids:
                    # Apply same filters as TypeDB query
                    if status and mem_task.get("status") != status:
                        continue
                    if phase and mem_task.get("phase") != phase:
                        continue
                    if agent_id and mem_task.get("agent_id") != agent_id:
                        continue
                    orphan = dict(mem_task)
                    orphan["persistence_status"] = "memory_only"
                    result.append(orphan)
            return result
        except Exception as e:
            # BUG-411-TDB-001: Add exc_info for stack trace preservation
            # BUG-473-TDA-1: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB task query failed: {type(e).__name__}", exc_info=True)
            if not allow_fallback:
                # BUG-377-TDB-001: Sanitize exception — don't forward raw error to HTTP clients
                raise TypeDBUnavailable(f"TypeDB unavailable: {type(e).__name__}")

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
            task = _typedb_get_task(client, task_id)
            if task:
                return _task_to_dict(task)
            return None
        except Exception as e:
            # BUG-411-TDB-002: Add exc_info for stack trace preservation
            # BUG-473-TDA-2: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB task get failed: {type(e).__name__}", exc_info=True)
            if not allow_fallback:
                # BUG-377-TDB-001: Sanitize exception — don't forward raw error to HTTP clients
                raise TypeDBUnavailable(f"TypeDB unavailable: {type(e).__name__}")

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
            sessions = _typedb_query_sessions(client)
            result = [_session_to_dict(s) for s in sessions]
            for s in result:
                s["persistence_status"] = "persisted"
            # BUG-SESSIONS-ONGOING-001: Merge in-memory status/end_time for
            # TypeDB sessions where TypeDB lacks completed-at but in-memory
            # has correct COMPLETED status (e.g. session ended via API but
            # completed-at not persisted to TypeDB, or ingested CC sessions).
            if allow_fallback:
                typedb_ids = {s["session_id"] for s in result}
                mem_snapshot = {
                    v.get("session_id"): v
                    for v in list(_sessions_store.values())
                    if v.get("session_id")
                }
                for s in result:
                    sid = s["session_id"]
                    mem = mem_snapshot.get(sid)
                    if mem:
                        mem_status = (mem.get("status") or "").upper()
                        tdb_status = (s.get("status") or "").upper()
                        # In-memory says COMPLETED but TypeDB says ACTIVE:
                        # trust the in-memory data (service layer wrote it)
                        if mem_status in ("COMPLETED", "CLOSED", "ENDED") and tdb_status == "ACTIVE":
                            s["status"] = mem_status
                            if mem.get("end_time") and not s.get("end_time"):
                                s["end_time"] = mem["end_time"]
                # Merge orphan sessions from _sessions_store (memory-only)
                # BUG-205-ITER-001: Snapshot to avoid RuntimeError on concurrent dict mutation
                for sid, mem_session in mem_snapshot.items():
                    if sid not in typedb_ids:
                        orphan = dict(mem_session)
                        orphan["persistence_status"] = "memory_only"
                        result.append(orphan)
            return result
        except Exception as e:
            # BUG-411-TDB-003: Add exc_info for stack trace preservation
            # BUG-473-TDA-3: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB session query failed: {type(e).__name__}", exc_info=True)
            if not allow_fallback:
                # BUG-377-TDB-001: Sanitize exception — don't forward raw error to HTTP clients
                raise TypeDBUnavailable(f"TypeDB unavailable: {type(e).__name__}")

    if allow_fallback:
        logger.warning("Using deprecated in-memory fallback for sessions")
        result = []
        # BUG-205-ITER-001: Snapshot to avoid RuntimeError on concurrent dict mutation
        for s in list(_sessions_store.values()):
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
            session = _typedb_get_session(client, session_id)
            if session:
                return _session_to_dict(session)
            return None
        except Exception as e:
            # BUG-411-TDB-004: Add exc_info for stack trace preservation
            # BUG-473-TDA-4: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB session get failed: {type(e).__name__}", exc_info=True)
            if not allow_fallback:
                # BUG-377-TDB-001: Sanitize exception — don't forward raw error to HTTP clients
                raise TypeDBUnavailable(f"TypeDB unavailable: {type(e).__name__}")

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
    # BUG-291-TDB-001: Guard against None task from partial TypeDB results
    if task is None:
        raise ValueError("Cannot convert None task to dict")
    return {
        "task_id": getattr(task, 'id', None),
        "name": task.name or "",  # Short title
        "description": task.body or task.description or task.name or "",  # Detailed content
        "phase": task.phase,
        "status": task.status,
        "priority": task.priority,  # BUG-TASK-TAXONOMY-001
        "task_type": task.task_type,  # BUG-TASK-TAXONOMY-001
        "summary": getattr(task, 'summary', None),  # Phase 9c
        "agent_id": task.agent_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "claimed_at": task.claimed_at.isoformat() if task.claimed_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "body": task.body,
        "resolution": task.resolution,  # BUG-STORE-001: missing from _task_to_dict
        "linked_rules": task.linked_rules or [],  # BUG-STORE-002: null-safe
        "linked_sessions": task.linked_sessions or [],
        "linked_commits": task.linked_commits or [],  # BUG-STORE-007: null-safe per GAP-TASK-LINK-002
        "linked_documents": list(dict.fromkeys(task.linked_documents or [])),  # BUG-TASK-DOC-DUP-001: dedup
        "gap_id": task.gap_id,
        "evidence": task.evidence,
        "document_path": task.document_path,
        "workspace_id": getattr(task, 'workspace_id', None),  # EPIC-GOV-TASKS-V2 Phase 6c
        # SRVJ-BUG-DUAL-WRITE-01: TypeDB entity = persisted by definition
        "persistence_status": "persisted",
    }


def _session_to_dict(session) -> Dict[str, Any]:
    """Convert TypeDB Session entity to dict format.

    P0-2: Duration computed server-side via compute_session_duration_from_timestamps
    to ensure identical results across all API paths (list, detail, update).
    """
    return {
        "session_id": session.id,
        # BUG-226-TYPEDB-003: Use stable sentinel instead of non-deterministic datetime.now()
        "start_time": session.started_at.isoformat() if session.started_at else "1970-01-01T00:00:00",
        "end_time": session.completed_at.isoformat() if session.completed_at else None,
        "status": session.status,
        "tasks_completed": session.tasks_completed or 0,
        "agent_id": session.agent_id,
        "description": session.description,
        "file_path": session.file_path,
        # BUG-STORE-008: Null-safe list fields for session relations
        "evidence_files": session.evidence_files or [],
        "linked_rules_applied": session.linked_rules_applied or [],
        "linked_decisions": session.linked_decisions or [],
        # Claude Code session attributes (SESSION-CC-01-v1)
        "cc_session_uuid": getattr(session, 'cc_session_uuid', None),
        "cc_project_slug": getattr(session, 'cc_project_slug', None),
        "cc_git_branch": getattr(session, 'cc_git_branch', None),
        "cc_tool_count": getattr(session, 'cc_tool_count', None),
        "cc_thinking_chars": getattr(session, 'cc_thinking_chars', None),
        "cc_compaction_count": getattr(session, 'cc_compaction_count', None),
        "cc_external_name": getattr(session, 'cc_external_name', None),
        "project_id": getattr(session, 'project_id', None),
        # P0-2: Server-computed duration — single source of truth
        "duration": compute_session_duration_from_timestamps(
            session.started_at, session.completed_at),
    }
