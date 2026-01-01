"""
Tasks Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-STUB-001/002: TypeDB is source of truth (in-memory fallback deprecated).

Created: 2024-12-28
Updated: 2025-01-01 (TypeDB-first refactoring)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging
import uuid

from governance.models import (
    TaskCreate, TaskUpdate, TaskResponse,
    TaskExecutionEvent, TaskExecutionResponse
)
from governance.stores import (
    get_typedb_client,
    # TypeDB-first wrappers (preferred)
    get_all_tasks_from_typedb,
    get_task_from_typedb,
    TypeDBUnavailable,
    # Legacy stores (deprecated - kept for backward compatibility)
    _tasks_store, _execution_events_store,
    _agents_store, _AGENT_BASE_CONFIG,
    _load_agent_metrics, _save_agent_metrics,
    _calculate_trust_score, _update_agent_metrics_on_claim,
    task_to_response, synthesize_execution_events
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tasks"])


# =============================================================================
# TASKS CRUD
# =============================================================================

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    phase: Optional[str] = Query(None, description="Filter by phase"),
    status: Optional[str] = Query(None, description="Filter by status"),
    agent_id: Optional[str] = Query(None, description="Filter by agent")
):
    """
    List all tasks.

    Per GAP-STUB-001/002: TypeDB is source of truth with fallback for resilience.
    """
    try:
        # Use TypeDB wrapper (handles fallback internally)
        tasks = get_all_tasks_from_typedb(
            status=status,
            phase=phase,
            agent_id=agent_id,
            allow_fallback=True  # Keep fallback during migration
        )
        return [TaskResponse(**t) for t in tasks]
    except TypeDBUnavailable as e:
        logger.error(f"TypeDB unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """
    Create a new task with enriched content.

    Per GAP-DATA-001: Tasks have full content.
    Per GAP-ARCH-001: Writes to TypeDB, with in-memory fallback.
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            # Check if exists
            existing = client.get_task(task.task_id)
            if existing:
                raise HTTPException(status_code=409, detail=f"Task {task.task_id} already exists")

            created = client.insert_task(
                task_id=task.task_id,
                name=task.description,
                status=task.status,
                phase=task.phase,
                body=task.body,
                gap_id=task.gap_id,
                linked_rules=task.linked_rules,
                linked_sessions=task.linked_sessions
            )
            if created:
                return task_to_response(created)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB task insert failed, using fallback: {e}")

    # Fallback to in-memory
    if task.task_id in _tasks_store:
        raise HTTPException(status_code=409, detail=f"Task {task.task_id} already exists")

    task_data = {
        "task_id": task.task_id,
        "description": task.description,
        "phase": task.phase,
        "status": task.status,
        "agent_id": task.agent_id,
        "body": task.body,
        "linked_rules": task.linked_rules,
        "linked_sessions": task.linked_sessions,
        "gap_id": task.gap_id,
        "created_at": datetime.now().isoformat()
    }
    _tasks_store[task.task_id] = task_data
    return TaskResponse(**task_data)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, update: TaskUpdate):
    """
    Update task fields.

    Per GAP-UI-107: Full task edit support.
    Per GAP-ARCH-001: Updates TypeDB first, falls back to in-memory.
    """
    client = get_typedb_client()
    task_obj = None

    # Try TypeDB first for status/agent_id updates
    if client:
        try:
            task_obj = client.get_task(task_id)
            if not task_obj:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            # Update status if provided
            if update.status:
                updated = client.update_task_status(
                    task_id,
                    update.status,
                    update.agent_id or task_obj.agent_id
                )
                task_obj = updated or task_obj
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB task update failed, using fallback: {e}")

    # Update in-memory store
    if task_id not in _tasks_store:
        if client and task_obj:
            # Initialize in-memory from TypeDB data
            _tasks_store[task_id] = {
                "task_id": task_id,
                "description": task_obj.description or "",
                "phase": task_obj.phase or "",
                "status": task_obj.status or "TODO",
                "agent_id": task_obj.agent_id,
                "created_at": task_obj.created_at or datetime.now().isoformat(),
            }
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Update provided fields
    if update.description is not None:
        _tasks_store[task_id]["description"] = update.description
    if update.phase is not None:
        _tasks_store[task_id]["phase"] = update.phase
    if update.status is not None:
        _tasks_store[task_id]["status"] = update.status
        if update.status == "DONE":
            _tasks_store[task_id]["completed_at"] = datetime.now().isoformat()
    if update.agent_id is not None:
        _tasks_store[task_id]["agent_id"] = update.agent_id if update.agent_id else None
    if update.body is not None:
        _tasks_store[task_id]["body"] = update.body
    if update.linked_rules is not None:
        _tasks_store[task_id]["linked_rules"] = update.linked_rules
    if update.linked_sessions is not None:
        _tasks_store[task_id]["linked_sessions"] = update.linked_sessions
    if update.gap_id is not None:
        _tasks_store[task_id]["gap_id"] = update.gap_id

    return TaskResponse(**_tasks_store[task_id])


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


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """
    Delete a task.

    Per GAP-ARCH-001: Deletes from TypeDB first, falls back to in-memory.
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            if client.get_task(task_id):
                if client.delete_task(task_id):
                    return None
        except Exception as e:
            logger.warning(f"TypeDB task delete failed, using fallback: {e}")

    # Fallback to in-memory
    if task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    del _tasks_store[task_id]
    return None


# =============================================================================
# TASK EXECUTION LOG (ORCH-007)
# =============================================================================

@router.get("/tasks/{task_id}/execution", response_model=TaskExecutionResponse)
async def get_task_execution(task_id: str):
    """
    Get task execution history (ORCH-007).

    Returns timeline of execution events: claimed, started, progress, completed, etc.
    """
    client = get_typedb_client()
    task = None

    if client:
        try:
            task = client.get_task(task_id)
        except Exception as e:
            logger.warning(f"TypeDB task query failed: {e}")

    if not task and task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Get or create execution events
    events = _execution_events_store.get(task_id, [])

    # If no events, synthesize from task data
    if not events:
        task_data = task if task else _tasks_store.get(task_id, {})
        events = synthesize_execution_events(task_id, task_data)

    # Determine current status
    current_status = "pending"
    current_agent = None
    started_at = None
    completed_at = None

    if task:
        current_status = task.status
        current_agent = task.agent_id
        started_at = task.claimed_at.isoformat() if task.claimed_at else None
        completed_at = task.completed_at.isoformat() if task.completed_at else None
    elif task_id in _tasks_store:
        task_data = _tasks_store[task_id]
        current_status = task_data.get("status", "pending")
        current_agent = task_data.get("agent_id")
        started_at = task_data.get("claimed_at")
        completed_at = task_data.get("completed_at")

    return TaskExecutionResponse(
        task_id=task_id,
        events=[TaskExecutionEvent(**e) for e in events],
        current_status=current_status,
        current_agent=current_agent,
        started_at=started_at,
        completed_at=completed_at
    )


@router.post("/tasks/{task_id}/execution", response_model=TaskExecutionEvent, status_code=201)
async def add_task_execution_event(
    task_id: str,
    event_type: str = Query(..., description="Event type: claimed, started, progress, delegated, completed, failed, evidence"),
    message: str = Query("", description="Event message"),
    agent_id: Optional[str] = Query(None, description="Agent ID for this event")
):
    """
    Add execution event to task (ORCH-007).

    Used by orchestrator agents to log execution progress.
    """
    client = get_typedb_client()
    task_exists = False

    if client:
        try:
            if client.get_task(task_id):
                task_exists = True
        except Exception:
            pass

    if not task_exists and task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Create event
    event = {
        "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
        "task_id": task_id,
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent_id,
        "message": message,
        "details": None
    }

    # Store event
    if task_id not in _execution_events_store:
        _execution_events_store[task_id] = []
    _execution_events_store[task_id].append(event)

    return TaskExecutionEvent(**event)
