"""
Tasks Workflow Routes.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/routes/tasks.py

Created: 2026-01-04 (GAP-FILE-020)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from governance.models import TaskResponse
from governance.stores import (
    get_typedb_client,
    _tasks_store, _agents_store, _AGENT_BASE_CONFIG,
    _load_agent_metrics, _save_agent_metrics,
    _calculate_trust_score, _update_agent_metrics_on_claim,
    task_to_response
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
async def claim_task(task_id: str, agent_id: str = Query(..., description="Agent ID claiming the task")):
    """
    Agent claims a task.

    Per TODO-6: Agent Task Backlog UI
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
async def complete_task(task_id: str, evidence: Optional[str] = Query(None, description="Evidence/notes")):
    """
    Mark a task as complete.

    Per TODO-6: Agent Task Backlog UI
    Sets status to DONE and records completion timestamp.
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            task_obj = client.get_task(task_id)
            if task_obj is None:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            if task_obj.status in ("DONE", "completed"):
                raise HTTPException(status_code=409, detail=f"Task {task_id} already completed")

            updated = client.update_task_status(task_id, "DONE", task_obj.agent_id, evidence)
            if updated:
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

    task["status"] = "DONE"
    task["completed_at"] = datetime.now().isoformat()
    if evidence:
        task["evidence"] = evidence

    return TaskResponse(**task)
