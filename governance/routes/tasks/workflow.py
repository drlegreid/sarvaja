"""
Tasks Workflow Routes.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/routes/tasks.py

Created: 2026-01-04 (GAP-FILE-020)
Updated: 2026-01-17 (GAP-FILE-029) - Extracted helpers to reduce file size
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
)
from governance.task_lifecycle import TaskResolution
from .helpers import (
    enrich_evidence_with_verification,
    determine_resolution,
    validate_promotion,
    combine_evidence,
    try_link_task_to_session,
    record_completion_audit,
    update_agent_metrics_on_claim_fallback,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tasks/available", response_model=List[TaskResponse])
async def list_available_tasks():
    """List tasks available for agents to claim (TypeDB first, in-memory fallback)."""
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
    """Agent claims a task. Sets agent_id and changes status to IN_PROGRESS."""
    client = get_typedb_client()
    CLAIMABLE_STATUSES = {"TODO", "pending", "todo", "PENDING"}
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
                # Non-critical operations - don't fail the claim if these fail
                try:
                    _update_agent_metrics_on_claim(agent_id)
                except Exception as e:
                    logger.warning(f"Agent metrics update failed (non-critical): {e}")
                try:
                    try_link_task_to_session(client, task_id, session_id, "claim")
                except Exception as e:
                    logger.warning(f"Task-session link failed (non-critical): {e}")
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
    update_agent_metrics_on_claim_fallback(
        agent_id, _agents_store, _AGENT_BASE_CONFIG,
        _calculate_trust_score, _load_agent_metrics, _save_agent_metrics
    )

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
    """Mark a task as complete. Resolution auto-determined by evidence quality."""
    client = get_typedb_client()
    resolution = determine_resolution(
        current_resolution=TaskResolution.NONE,
        has_evidence=bool(evidence),
        has_tests=has_tests,
        has_user_feedback=has_user_feedback,
        verification_level=verification_level
    )
    enriched_evidence = enrich_evidence_with_verification(evidence, verification_level)
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
                try_link_task_to_session(client, task_id, session_id, "completion")

                logger.info(f"Task {task_id} completed with resolution={resolution.value}, verification={verification_level}")

                # RD-DEBUG-AUDIT: Record task completion in audit trail
                record_completion_audit(
                    task_id, task_obj.agent_id, task_obj.status, "DONE",
                    resolution.value, verification_level, session_id
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
    record_completion_audit(
        task_id, task.get("agent_id"), old_status, "DONE",
        resolution.value, verification_level, session_id
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
    """Promote a completed task's resolution (IMPLEMENTED→VALIDATED→CERTIFIED)."""
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
    enriched_evidence = enrich_evidence_with_verification(evidence, verification_level, is_promotion=True)

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
            is_valid, error_msg = validate_promotion(current_resolution, target)
            if not is_valid:
                raise HTTPException(status_code=409, detail=error_msg)

            # Append to existing evidence
            combined_evidence_str = combine_evidence(task_obj.evidence, enriched_evidence)

            # Update resolution (status stays DONE/CLOSED)
            updated = client.update_task_status(
                task_id,
                task_obj.status,  # Keep current status
                task_obj.agent_id,
                combined_evidence_str,
                target.value
            )
            if updated:
                # Link to session if provided
                try_link_task_to_session(client, task_id, session_id, "promotion")

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

    is_valid, error_msg = validate_promotion(current, target)
    if not is_valid:
        raise HTTPException(status_code=409, detail=error_msg)

    task["resolution"] = target.value
    task["evidence"] = combine_evidence(task.get("evidence"), enriched_evidence)

    return TaskResponse(**task)
