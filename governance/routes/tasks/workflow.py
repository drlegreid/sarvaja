"""
Tasks Workflow Routes.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/routes/tasks.py

Created: 2026-01-04 (GAP-FILE-020)
Updated: 2026-01-17 (GAP-UI-LINKED-SESSIONS-001) - Added verification_level parameter
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Literal
from datetime import datetime
import logging

from governance.models import TaskResponse
from governance.stores import (
    get_typedb_client,
    _tasks_store, _agents_store, _AGENT_BASE_CONFIG,
    _load_agent_metrics, _save_agent_metrics,
    _calculate_trust_score, _update_agent_metrics_on_claim,
    task_to_response,
    record_audit, generate_correlation_id  # RD-DEBUG-AUDIT
)
from governance.task_lifecycle import (
    TaskResolution,
    get_resolution_for_close,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tasks/available", response_model=List[TaskResponse])
async def list_available_tasks():
    """
    List tasks available for agents to claim.

    Per TODO-6: Agent Task Backlog UI
    Per GAP-ARCH-001: Queries TypeDB first, falls back to in-memory.
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            tasks = client.get_available_tasks()
            if tasks:
                return [task_to_response(t) for t in tasks]
        except Exception as e:
            logger.warning(f"TypeDB available tasks query failed, using fallback: {e}")

    # Fallback to in-memory
    AVAILABLE_STATUSES = {"TODO", "pending", "todo", "PENDING"}
    available = [
        t for t in _tasks_store.values()
        if t.get("status") in AVAILABLE_STATUSES and not t.get("agent_id")
    ]
    return [TaskResponse(**t) for t in available]


@router.put("/tasks/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: str,
    agent_id: str = Query(..., description="Agent ID claiming the task"),
    session_id: Optional[str] = Query(None, description="Session ID for task context (EPIC-DR-006)")
):
    """
    Agent claims a task.

    Per TODO-6: Agent Task Backlog UI
    Per EPIC-DR-006: Accepts session_id to establish session→task traceability.
    Sets agent_id and changes status to IN_PROGRESS.
    """
    client = get_typedb_client()
    CLAIMABLE_STATUSES = {"TODO", "pending", "todo", "PENDING"}

    # Try TypeDB first
    if client:
        try:
            task_obj = client.get_task(task_id)
            if task_obj is None:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            if task_obj.agent_id:
                raise HTTPException(
                    status_code=409,
                    detail=f"Task {task_id} already claimed by {task_obj.agent_id}"
                )

            if task_obj.status not in CLAIMABLE_STATUSES:
                raise HTTPException(
                    status_code=409,
                    detail=f"Task {task_id} has status {task_obj.status}, not available for claim"
                )

            updated = client.update_task_status(task_id, "IN_PROGRESS", agent_id)
            if updated:
                _update_agent_metrics_on_claim(agent_id)
                # EPIC-DR-006: Link task to session for traceability
                if session_id:
                    try:
                        client.link_task_to_session(task_id, session_id)
                        logger.info(f"Linked claimed task {task_id} to session {session_id}")
                    except Exception as link_err:
                        logger.warning(f"Failed to link task {task_id} to session {session_id}: {link_err}")
                return task_to_response(updated)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB claim_task failed, using fallback: {e}")

    # Fallback to in-memory
    if task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = _tasks_store[task_id]

    if task.get("agent_id"):
        raise HTTPException(
            status_code=409,
            detail=f"Task {task_id} already claimed by {task.get('agent_id')}"
        )

    if task.get("status") not in CLAIMABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Task {task_id} has status {task.get('status')}, not available for claim"
        )

    # Claim the task
    task["agent_id"] = agent_id
    task["status"] = "IN_PROGRESS"
    task["claimed_at"] = datetime.now().isoformat()

    # Update agent metrics
    if agent_id in _agents_store:
        _agents_store[agent_id]["tasks_executed"] += 1
        _agents_store[agent_id]["last_active"] = datetime.now().isoformat()

        base_trust = _AGENT_BASE_CONFIG.get(agent_id, {}).get("base_trust", 0.85)
        _agents_store[agent_id]["trust_score"] = _calculate_trust_score(
            agent_id, _agents_store[agent_id]["tasks_executed"], base_trust
        )

        metrics = _load_agent_metrics()
        metrics[agent_id] = {
            "tasks_executed": _agents_store[agent_id]["tasks_executed"],
            "last_active": _agents_store[agent_id]["last_active"]
        }
        _save_agent_metrics(metrics)

    return TaskResponse(**task)


@router.put("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    evidence: Optional[str] = Query(None, description="Evidence/notes describing what was done"),
    session_id: Optional[str] = Query(None, description="Session ID to link task completion (EPIC-DR-006)"),
    verification_level: Optional[Literal["L1", "L2", "L3"]] = Query(
        None,
        description="Verification level per WORKFLOW-SEQ-01-v1: L1=Technical fix, L2=E2E functionality, L3=User flow complete"
    ),
    has_tests: bool = Query(False, description="Tests pass for this fix"),
    has_user_feedback: bool = Query(False, description="User/stakeholder acceptance received")
):
    """
    Mark a task as complete with verification evidence.

    Per TODO-6: Agent Task Backlog UI
    Per EPIC-DR-006: Accepts session_id to establish session→task traceability.
    Per WORKFLOW-SEQ-01-v1: Verification hierarchy (L1→L2→L3) must be tracked.
    Per GAP-UI-046: Resolution (IMPLEMENTED→VALIDATED→CERTIFIED) determined by evidence.

    Resolution is automatically determined:
    - IMPLEMENTED: Evidence provided but no tests
    - VALIDATED: Tests pass (has_tests=True or verification_level=L2/L3)
    - CERTIFIED: User feedback received (has_user_feedback=True)
    """
    client = get_typedb_client()

    # Determine resolution based on evidence quality
    # L2/L3 verification implies tests pass
    effective_has_tests = has_tests or verification_level in ("L2", "L3")
    # L3 verification implies user acceptance
    effective_has_feedback = has_user_feedback or verification_level == "L3"

    resolution = get_resolution_for_close(
        current_resolution=TaskResolution.NONE,
        has_evidence=bool(evidence),
        has_tests=effective_has_tests,
        has_user_feedback=effective_has_feedback
    )

    # Enrich evidence with verification metadata
    enriched_evidence = evidence or ""
    if verification_level:
        verification_info = f"[Verification: {verification_level}]"
        if verification_level == "L1":
            verification_info += " Technical fix verified"
        elif verification_level == "L2":
            verification_info += " E2E functionality verified"
        elif verification_level == "L3":
            verification_info += " Full user flow verified"
        enriched_evidence = f"{verification_info} {enriched_evidence}".strip()

    # Try TypeDB first
    if client:
        try:
            task_obj = client.get_task(task_id)
            if task_obj is None:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            if task_obj.status in ("DONE", "completed", "CLOSED"):
                raise HTTPException(status_code=409, detail=f"Task {task_id} already completed")

            # Pass resolution to TypeDB update
            updated = client.update_task_status(
                task_id, "DONE",
                task_obj.agent_id,
                enriched_evidence if enriched_evidence else None,
                resolution.value
            )
            if updated:
                # EPIC-DR-006: Link task to session for traceability
                if session_id:
                    try:
                        client.link_task_to_session(task_id, session_id)
                        logger.info(f"Linked task {task_id} to session {session_id}")
                    except Exception as link_err:
                        logger.warning(f"Failed to link task {task_id} to session {session_id}: {link_err}")

                logger.info(f"Task {task_id} completed with resolution={resolution.value}, verification={verification_level}")

                # RD-DEBUG-AUDIT: Record task completion in audit trail
                record_audit(
                    action_type="COMPLETE",
                    entity_type="task",
                    entity_id=task_id,
                    actor_id=task_obj.agent_id or "unknown",
                    old_value=task_obj.status,
                    new_value="DONE",
                    applied_rules=["WORKFLOW-SEQ-01-v1"],
                    metadata={
                        "resolution": resolution.value,
                        "verification_level": verification_level,
                        "session_id": session_id
                    }
                )

                return task_to_response(updated)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB complete_task failed, using fallback: {e}")

    # Fallback to in-memory
    if task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = _tasks_store[task_id]

    if task.get("status") == "DONE":
        raise HTTPException(status_code=409, detail=f"Task {task_id} already completed")

    old_status = task.get("status", "TODO")
    task["status"] = "DONE"
    task["completed_at"] = datetime.now().isoformat()
    task["resolution"] = resolution.value
    if enriched_evidence:
        task["evidence"] = enriched_evidence

    # RD-DEBUG-AUDIT: Record task completion in audit trail
    record_audit(
        action_type="COMPLETE",
        entity_type="task",
        entity_id=task_id,
        actor_id=task.get("agent_id", "unknown"),
        old_value=old_status,
        new_value="DONE",
        applied_rules=["WORKFLOW-SEQ-01-v1"],
        metadata={
            "resolution": resolution.value,
            "verification_level": verification_level,
            "session_id": session_id
        }
    )

    return TaskResponse(**task)


@router.put("/tasks/{task_id}/promote-resolution", response_model=TaskResponse)
async def promote_task_resolution(
    task_id: str,
    target_resolution: Literal["VALIDATED", "CERTIFIED"] = Query(
        ...,
        description="Target resolution: VALIDATED (tests pass) or CERTIFIED (user approved)"
    ),
    evidence: str = Query(..., description="Evidence supporting the promotion"),
    verification_level: Optional[Literal["L2", "L3"]] = Query(
        None,
        description="Verification level achieved: L2=E2E tested, L3=User flow verified"
    ),
    session_id: Optional[str] = Query(None, description="Session ID for traceability")
):
    """
    Promote a completed task's resolution level.

    Per WORKFLOW-SEQ-01-v1: Allows incremental verification (L1→L2→L3).
    Per Directive 2: Verification subtasks can call this to upgrade resolution.

    Valid promotions:
    - IMPLEMENTED → VALIDATED (requires tests passing evidence)
    - VALIDATED → CERTIFIED (requires user feedback evidence)

    This endpoint is separate from complete_task to support:
    1. Verification subtasks that run after initial completion
    2. QA review workflows
    3. User acceptance testing phases
    """
    from governance.task_lifecycle import validate_resolution_transition

    client = get_typedb_client()

    # Validate target resolution
    try:
        target = TaskResolution(target_resolution)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resolution: {target_resolution}. Must be VALIDATED or CERTIFIED."
        )

    # Enrich evidence with verification metadata
    enriched_evidence = evidence
    if verification_level:
        verification_info = f"[Promotion: {verification_level}]"
        if verification_level == "L2":
            verification_info += " E2E functionality verified"
        elif verification_level == "L3":
            verification_info += " Full user flow verified"
        enriched_evidence = f"{verification_info} {evidence}"

    if client:
        try:
            task_obj = client.get_task(task_id)
            if task_obj is None:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            # Task must be completed (DONE/CLOSED) to promote resolution
            if task_obj.status not in ("DONE", "CLOSED", "completed"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Task {task_id} must be completed before resolution can be promoted. Current status: {task_obj.status}"
                )

            # Validate resolution transition
            current_resolution = TaskResolution(task_obj.resolution) if task_obj.resolution else TaskResolution.IMPLEMENTED
            if not validate_resolution_transition(current_resolution, target):
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot promote from {current_resolution.value} to {target.value}. Valid transitions: {current_resolution.value} → VALIDATED/CERTIFIED"
                )

            # Append to existing evidence
            combined_evidence = task_obj.evidence or ""
            if combined_evidence:
                combined_evidence = f"{combined_evidence}\n---\n{enriched_evidence}"
            else:
                combined_evidence = enriched_evidence

            # Update resolution (status stays DONE/CLOSED)
            updated = client.update_task_status(
                task_id,
                task_obj.status,  # Keep current status
                task_obj.agent_id,
                combined_evidence,
                target.value
            )
            if updated:
                # Link to session if provided
                if session_id:
                    try:
                        client.link_task_to_session(task_id, session_id)
                        logger.info(f"Linked resolution promotion to session {session_id}")
                    except Exception as link_err:
                        logger.warning(f"Failed to link to session: {link_err}")

                logger.info(f"Task {task_id} promoted from {current_resolution.value} to {target.value}")
                return task_to_response(updated)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB promote_resolution failed, using fallback: {e}")

    # Fallback to in-memory
    if task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = _tasks_store[task_id]
    current = TaskResolution(task.get("resolution", "IMPLEMENTED"))

    if not validate_resolution_transition(current, target):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot promote from {current.value} to {target.value}"
        )

    task["resolution"] = target.value
    existing = task.get("evidence", "")
    task["evidence"] = f"{existing}\n---\n{enriched_evidence}" if existing else enriched_evidence

    return TaskResponse(**task)
