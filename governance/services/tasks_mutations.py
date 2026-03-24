"""Task Service Mutations — update, delete, and linking operations.

Per DOC-SIZE-01-v1: Hub module. Preload in tasks_preload.py,
linking in tasks_mutations_linking.py.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from governance.stores import (
    get_typedb_client,
    _tasks_store,
    _sessions_store,
    task_to_response,
)
from governance.stores.audit import record_audit
from governance.middleware.event_log import log_event
from .tasks_preload import _monitor, _preload_task_from_typedb  # noqa: F401
from .tasks_mutations_linking import (  # noqa: F401
    link_task_to_rule,
    link_task_to_session,
    link_task_to_document,
    unlink_task_from_document,
    link_task_to_workspace,
)

logger = logging.getLogger(__name__)

__all__ = [
    "update_task",
    "delete_task",
    "link_task_to_rule",
    "link_task_to_session",
    "link_task_to_document",
    # BUG-214-011: Was missing from __all__ despite being defined at line 252
    "unlink_task_from_document",
    "link_task_to_workspace",  # EPIC-GOV-TASKS-V2 Phase 4
]


def update_task(
    task_id: str,
    description: Optional[str] = None,
    status: Optional[str] = None,
    phase: Optional[str] = None,
    agent_id: Optional[str] = None,
    body: Optional[str] = None,
    priority: Optional[str] = None,
    task_type: Optional[str] = None,
    evidence: Optional[str] = None,
    linked_rules: Optional[List[str]] = None,
    linked_sessions: Optional[List[str]] = None,
    linked_documents: Optional[List[str]] = None,
    gap_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    summary: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    source: str = "rest",
) -> Optional[Dict[str, Any]]:
    """Update task fields in TypeDB with fallback.

    Returns:
        Updated task dict or None if not found.
    """
    # BUG-STATUS-CASE-001: Normalize status to uppercase at service boundary
    if status:
        status = status.upper()

    # SRVJ-BUG-023: Validate agent_id against registered agents at write boundary
    if agent_id:
        from governance.services.task_rules import validate_agent_id
        agent_errors = validate_agent_id(agent_id)
        if agent_errors:
            raise ValueError(f"Invalid agent_id '{agent_id}': {agent_errors[0].message}")

    # Per DATA-LINK-01-v1 / EPIC-GOV-TASKS-V2 Phase 2: Auto-link to active session
    # on status transition when no linked_sessions provided
    if status and not linked_sessions:
        from governance.services.tasks import _get_active_session_id
        # Check if task already has sessions in fallback store
        existing = _tasks_store.get(task_id, {}).get("linked_sessions", [])
        if not existing:
            active_sid = _get_active_session_id()
            if active_sid:
                linked_sessions = [active_sid]
                logger.info(
                    f"[DATA-LINK-01] Auto-linking task {task_id} to session "
                    f"{active_sid} on status transition to {status}"
                )

    # SRVJ-FEAT-002: DONE gate — validate mandatory fields on completion
    if status and status.upper() == "DONE":
        from governance.services.task_rules import validate_on_complete, format_validation_result
        # P14: ALWAYS refresh from TypeDB for DONE gate — linked_documents may
        # have been added via MCP after initial creation (stale _tasks_store data).
        _preload_task_from_typedb(task_id)
        # Gather existing task data for validation
        existing = _tasks_store.get(task_id, {})
        effective_summary = summary or existing.get("summary")
        effective_agent = agent_id or existing.get("agent_id")
        effective_sessions = linked_sessions or existing.get("linked_sessions", [])
        # SRVJ-BUG-002: Pre-compute completed_at — system auto-sets it on DONE
        # transition (line 230), so validation should see the future value
        effective_completed = existing.get("completed_at") or datetime.now().isoformat()
        effective_docs = linked_documents or existing.get("linked_documents", [])

        done_errors = validate_on_complete(
            task_id=task_id,
            summary=effective_summary,
            agent_id=effective_agent,
            completed_at=effective_completed,
            linked_sessions=effective_sessions,
            linked_documents=effective_docs,
        )
        if done_errors:
            for err in done_errors:
                logger.warning(f"[DONE-GATE] {err.rule}: {err.message}")
            result = format_validation_result(done_errors)
            raise ValueError(f"DONE gate validation failed: {result}")

    # P17: Auto-populate resolution_notes on DONE transition (if empty)
    if status and status.upper() == "DONE" and not resolution_notes:
        existing = _tasks_store.get(task_id, {})
        existing_rn = existing.get("resolution_notes")
        if not existing_rn:
            from governance.services.resolution_collator import (
                build_resolution_summary,
                fetch_session_metadata,
            )
            task_snapshot = dict(existing)
            # Merge in any fields being set in this same call
            if linked_sessions:
                task_snapshot["linked_sessions"] = linked_sessions
            if linked_documents:
                task_snapshot["linked_documents"] = linked_documents
            if evidence:
                task_snapshot["evidence"] = evidence
            session_ids = task_snapshot.get("linked_sessions") or []
            session_meta = fetch_session_metadata(session_ids) if session_ids else []
            resolution_notes = build_resolution_summary(task_snapshot, session_meta)
            logger.info(f"[P17] Auto-populated resolution_notes for {task_id}")

    # SRVJ-FEAT-008: Auto-attach evidence summary for test tasks on DONE
    if status and status.upper() == "DONE":
        existing = _tasks_store.get(task_id, {})
        effective_type = task_type or existing.get("task_type")
        if effective_type == "test" and not evidence:
            evidence = (
                f"[Verification: Auto] Test task completed "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

    client = get_typedb_client()
    task_obj = None
    if client:
        try:
            task_obj = client.get_task(task_id)
            if not task_obj and task_id not in _tasks_store:
                return None
            # SRVJ-BUG-018: Resolve agent_id BEFORE TypeDB writes.
            # H-TASK-002 was previously after the writes, so auto-assigned
            # agent_id only went to _tasks_store, never to TypeDB.
            if status and status.upper() == "IN_PROGRESS" and not agent_id:
                existing_agent = task_obj.agent_id if task_obj else None
                if not existing_agent:
                    from governance.stores.agents import DEFAULT_AGENT_ID
                    agent_id = DEFAULT_AGENT_ID
                    logger.warning(
                        f"[H-TASK-002] Task {task_id} set to IN_PROGRESS without "
                        f"agent_id, auto-assigning '{DEFAULT_AGENT_ID}'"
                    )
            if task_obj and (status or evidence):
                updated = client.update_task_status(
                    task_id, status or task_obj.status,
                    agent_id or task_obj.agent_id, evidence=evidence,
                )
                task_obj = updated or task_obj
            # BUG-TASK-TAXONOMY-001: Persist priority/task_type/name/phase/summary to TypeDB
            # SRVJ-BUG-018: Also persist agent_id via update_task()
            if task_obj and (priority or task_type or phase or description or summary or agent_id or resolution_notes):
                try:
                    client.update_task(
                        task_id,
                        priority=priority,
                        task_type=task_type,
                        name=description,
                        phase=phase,
                        summary=summary,
                        agent_id=agent_id,
                        resolution_notes=resolution_notes,
                    )
                except Exception as ue:
                    # BUG-TASK-TAXONOMY-DEBUG-001: WARNING not DEBUG — data divergence
                    # BUG-464-TM-002: Sanitize logger message + add exc_info for stack trace
                    logger.warning(f"TypeDB attribute update {task_id}: {type(ue).__name__}", exc_info=True)
            # Persist linked_sessions to TypeDB via relations
            if linked_sessions:
                for sid in linked_sessions:
                    try:
                        client.link_task_to_session(task_id, sid)
                    except Exception as le:
                        # BUG-MUTATIONS-002: Link failures are data integrity issues
                        # BUG-464-TM-003: Sanitize logger message + add exc_info for stack trace
                        logger.warning(f"TypeDB session link {task_id}->{sid}: {type(le).__name__}", exc_info=True)
            # Persist linked_documents to TypeDB via relations
            if linked_documents:
                for doc_path in linked_documents:
                    try:
                        client.link_task_to_document(task_id, doc_path)
                    except Exception as le:
                        # BUG-MUTATIONS-002: Link failures are data integrity issues
                        # BUG-464-TM-004: Sanitize logger message + add exc_info for stack trace
                        logger.warning(f"TypeDB document link {task_id}->{doc_path}: {type(le).__name__}", exc_info=True)
            # EPIC-GOV-TASKS-V2 Phase 4: Persist workspace link
            if workspace_id:
                try:
                    client.link_task_to_workspace(workspace_id, task_id)  # BUG-WS-CREATE-001: fix arg order
                except Exception as le:
                    logger.warning(f"TypeDB workspace link {task_id}->{workspace_id}: {type(le).__name__}", exc_info=True)
        except Exception as e:
            # BUG-408-TM-001: Add exc_info for stack trace preservation
            # BUG-464-TM-005: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB task update failed, using fallback: {type(e).__name__}", exc_info=True)

    # Ensure task in fallback store
    if task_id not in _tasks_store:
        if client and task_obj:
            created_at = task_obj.created_at.isoformat() if task_obj.created_at else datetime.now().isoformat()
            # BUG-TASK-003: Include all fields in fallback task creation
            # BUG-SERVICE-002: Include evidence, timestamps, resolution, commits
            _claimed = getattr(task_obj, 'claimed_at', None)
            _completed = getattr(task_obj, 'completed_at', None)
            _tasks_store[task_id] = {
                "task_id": task_id,
                "description": task_obj.name or getattr(task_obj, 'description', '') or "",
                "phase": task_obj.phase or "",
                "status": task_obj.status or "TODO",
                "agent_id": task_obj.agent_id,
                "created_at": created_at,
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
                "workspace_id": getattr(task_obj, 'workspace_id', None),  # EPIC-GOV-TASKS-V2 Phase 6c
                "resolution_notes": getattr(task_obj, 'resolution_notes', None),  # P17
            }
        else:
            return None

    old_status = _tasks_store[task_id].get("status")

    # SRVJ-BUG-018: H-TASK-002 fallback for non-client path.
    # Primary check is now before TypeDB writes (line ~170).
    # This catches the edge case where client is None.
    if status and status.upper() == "IN_PROGRESS" and not agent_id:
        existing_agent = _tasks_store[task_id].get("agent_id")
        if not existing_agent:
            from governance.stores.agents import DEFAULT_AGENT_ID
            agent_id = DEFAULT_AGENT_ID
            logger.warning(
                f"[H-TASK-002] Task {task_id} set to IN_PROGRESS without agent_id, "
                f"auto-assigning '{DEFAULT_AGENT_ID}' (fallback path)"
            )

    updates = {
        "description": description, "phase": phase, "status": status,
        "priority": priority, "task_type": task_type,
        "agent_id": agent_id, "body": body, "evidence": evidence,
        "linked_rules": linked_rules, "linked_sessions": linked_sessions,
        "linked_documents": linked_documents, "gap_id": gap_id,
        "workspace_id": workspace_id, "summary": summary,
        "resolution_notes": resolution_notes,
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
            # BUG-408-TM-002: Add exc_info for stack trace preservation
            # BUG-464-TM-006: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"TypeDB task delete failed, using fallback: {type(e).__name__}", exc_info=True)

    if task_id in _tasks_store:
        del _tasks_store[task_id]
        deleted = True

    if deleted:
        record_audit("DELETE", "task", task_id, metadata={"source": source})
        _monitor("delete", task_id, source=source)
        log_event("task", "delete", task_id=task_id, source=source)
    return deleted
