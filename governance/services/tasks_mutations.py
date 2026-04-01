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
    task_to_response,
)
from governance.stores.audit import record_audit
from governance.middleware.event_log import log_event
from governance.services.task_activity_comments import maybe_add_activity_comment
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
    layer: Optional[str] = None,
    concern: Optional[str] = None,
    method: Optional[str] = None,
    source: str = "rest",
) -> Optional[Dict[str, Any]]:
    """Update task fields in TypeDB with fallback.

    Returns:
        Updated task dict or None if not found.
    """
    # BUG-STATUS-CASE-001: Normalize status to uppercase at service boundary
    if status:
        status = status.upper()

    # EPIC-TASK-TAXONOMY-V2 Session 3: Normalize CLOSED→DONE at service boundary
    if status:
        from governance.task_lifecycle import normalize_status
        status = normalize_status(status)

    # EPIC-TASK-TAXONOMY-V2: Normalize deprecated task_type aliases
    if task_type:
        from agent.governance_ui.state.constants import TASK_TYPE_ALIASES
        task_type = TASK_TYPE_ALIASES.get(task_type, task_type)

    # SRVJ-BUG-023: Validate agent_id against registered agents at write boundary
    if agent_id:
        from governance.services.task_rules import validate_agent_id
        agent_errors = validate_agent_id(agent_id)
        if agent_errors:
            raise ValueError(f"Invalid agent_id '{agent_id}': {agent_errors[0].message}")

    # SRVJ-BUG-DEAD-LIFECYCLE-01: Wire status transition validation.
    # validate_status_transition() had 36+ passing tests but was never called —
    # any status transition (TODO→DONE, DONE→BLOCKED) was silently accepted.
    if status:
        from governance.task_lifecycle import validate_status_transition, TaskStatus
        current_raw = _tasks_store.get(task_id, {}).get("status")
        if current_raw:
            try:
                from_status = TaskStatus(current_raw)
                to_status = TaskStatus(status)
            except ValueError:
                # Legacy/unknown enum value in store — skip check gracefully
                logger.warning(
                    f"[LIFECYCLE] Skipping transition check — unrecognized status: "
                    f"{current_raw!r} → {status!r}"
                )
            else:
                if not validate_status_transition(from_status, to_status):
                    raise ValueError(
                        f"Invalid status transition: {from_status.value} → {to_status.value}"
                    )

    # P9 (BUG-SESSION-POISON-01): Auto-linking on update REMOVED.
    # Session must be passed explicitly via linked_sessions parameter.

    # SRVJ-FEAT-008: Auto-attach evidence for test tasks BEFORE DONE gate.
    # Moved from after the gate (where it was dead code) to before it,
    # so the auto-stamp is visible to validate_on_complete().
    if status and status.upper() == "DONE":
        _existing_pre = _tasks_store.get(task_id, {})
        _eff_type = task_type or _existing_pre.get("task_type")
        if _eff_type == "test" and not evidence and not _existing_pre.get("evidence"):
            evidence = (
                f"[Verification: Auto] Test task completed "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            logger.info(f"[SRVJ-FEAT-008] Auto-generated evidence for test task {task_id}")

    # SRVJ-FEAT-002: DONE gate — validate mandatory fields on completion
    # SRVJ-BUG-DONE-GATE-01 (P5): Track whether validation used TypeDB or cache
    _done_gate_validation_source = None
    if status and status.upper() == "DONE":
        from governance.services.task_rules import validate_on_complete, format_validation_result
        # P14: ALWAYS refresh from TypeDB for DONE gate — linked_documents may
        # have been added via MCP after initial creation (stale _tasks_store data).
        _typedb_preloaded = _preload_task_from_typedb(task_id)
        _done_gate_validation_source = "typedb" if _typedb_preloaded else "cache"
        if _done_gate_validation_source == "cache":
            logger.warning(
                f"[DONE-GATE] validation_source=cache for task {task_id} — "
                f"TypeDB unreachable, validating against stale _tasks_store data"
            )
        # Gather existing task data for validation
        existing = _tasks_store.get(task_id, {})
        effective_summary = summary or existing.get("summary")
        effective_agent = agent_id or existing.get("agent_id")
        effective_sessions = linked_sessions or existing.get("linked_sessions", [])
        # SRVJ-BUG-002: Pre-compute completed_at — system auto-sets it on DONE
        # transition (line 230), so validation should see the future value
        effective_completed = existing.get("completed_at") or datetime.now().isoformat()
        effective_docs = linked_documents or existing.get("linked_documents", [])
        effective_type = task_type or existing.get("task_type")
        effective_evidence = evidence or existing.get("evidence")

        done_errors = validate_on_complete(
            task_id=task_id,
            summary=effective_summary,
            agent_id=effective_agent,
            completed_at=effective_completed,
            linked_sessions=effective_sessions,
            linked_documents=effective_docs,
            task_type=effective_type,
            evidence=effective_evidence,
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

    client = get_typedb_client()
    task_obj = None
    # SRVJ-FEAT-AUDIT-TRAIL-01 P8 (GAP 1): Capture pre-update status from TypeDB
    # BEFORE update_task_status() overwrites it. When task is NOT in _tasks_store
    # (first update after restart), _tasks_store gets populated from the UPDATED
    # task_obj, so old_status at line ~309 would see the NEW value. This variable
    # preserves the TRUE old status for correct field_changes in audit/auto-comments.
    _pre_update_status = None
    _task_was_new = task_id not in _tasks_store
    if client:
        try:
            task_obj = client.get_task(task_id)
            if not task_obj and task_id not in _tasks_store:
                return None
            # Capture BEFORE any TypeDB writes
            if task_obj:
                _pre_update_status = task_obj.status
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
            # SRVJ-BUG-AGENTID-PERSIST-01 (P6): Don't gate on task_obj alone.
            # If preload fails (task_obj=None) but task exists in _tasks_store,
            # still attempt the TypeDB write — the task likely exists in TypeDB
            # and preload was just a transient failure.
            if (task_obj or task_id in _tasks_store) and (priority or task_type or phase or description or summary or agent_id or resolution_notes or layer or concern or method):
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
                        layer=layer,
                        concern=concern,
                        method=method,
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
                "layer": getattr(task_obj, 'layer', None),
                "concern": getattr(task_obj, 'concern', None),
                "method": getattr(task_obj, 'method', None),
                # SRVJ-BUG-DUAL-WRITE-01: Loaded from TypeDB = persisted
                "persistence_status": "persisted",
            }
        else:
            return None

    # SRVJ-FEAT-AUDIT-TRAIL-01 P8 (GAP 1): When task was freshly loaded from
    # TypeDB (wasn't in _tasks_store), use the pre-update status captured BEFORE
    # update_task_status(). Otherwise _tasks_store already has the correct old value.
    if _task_was_new and _pre_update_status is not None:
        old_status = _pre_update_status
    else:
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
        "layer": layer, "concern": concern, "method": method,
    }

    # SRVJ-FEAT-AUDIT-TRAIL-01 P2: Capture old values BEFORE mutation for field_changes
    _old_snapshot = {k: _tasks_store[task_id].get(k) for k, v in updates.items() if v is not None}
    # P8 (GAP 1): When task was freshly loaded from TypeDB, _tasks_store has the
    # post-update status (populated from updated task_obj). Override with pre-update.
    if _task_was_new and _pre_update_status is not None and "status" in _old_snapshot:
        _old_snapshot["status"] = _pre_update_status

    for field, val in updates.items():
        if val is not None:
            _tasks_store[task_id][field] = val
            if field == "status" and val == "DONE":
                _tasks_store[task_id]["completed_at"] = datetime.now().isoformat()

    # SRVJ-FEAT-AUDIT-TRAIL-01 P2: Build field_changes + enriched metadata
    field_changes = {}
    for field, new_val in updates.items():
        if new_val is not None:
            old_val = _old_snapshot.get(field)
            if old_val != new_val:
                field_changes[field] = {"from": old_val, "to": new_val}

    audit_metadata: Dict[str, Any] = {"phase": phase, "source": source}
    if field_changes:
        audit_metadata["field_changes"] = field_changes
    # Session correlation: include session_id when linked_sessions provided
    if linked_sessions:
        audit_metadata["session_id"] = linked_sessions[0]

    # Fix: new_value always populated — use status if provided, else summary of changed fields
    _audit_new_value = status
    if not _audit_new_value and field_changes:
        _audit_new_value = ", ".join(f"{k}={v['to']}" for k, v in field_changes.items())

    record_audit("UPDATE", "task", task_id,
                 actor_id=agent_id or "system",
                 old_value=old_status, new_value=_audit_new_value,
                 metadata=audit_metadata)
    # SRVJ-FEAT-AUDIT-TRAIL-01 P7: Auto-generate human-readable system comment
    maybe_add_activity_comment(
        task_id=task_id,
        action_type="UPDATE",
        actor_id=agent_id or "system",
        source=source,
        old_value=old_status,
        new_value=_audit_new_value,
        metadata=audit_metadata,
    )
    _monitor("update", task_id, source=source, status=status, phase=phase)
    log_event("task", "update", task_id=task_id, old_status=old_status, status=status, source=source)
    result = dict(_tasks_store[task_id])
    # SRVJ-BUG-DONE-GATE-01 (P5): Propagate validation_source on DONE transitions
    if _done_gate_validation_source:
        result["validation_source"] = _done_gate_validation_source
    return result


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
        # SRVJ-FEAT-AUDIT-TRAIL-01 P7: Auto-comment for DELETE
        maybe_add_activity_comment(
            task_id=task_id,
            action_type="DELETE",
            actor_id="system",
            source=source,
        )
        _monitor("delete", task_id, source=source)
        log_event("task", "delete", task_id=task_id, source=source)
    return deleted
