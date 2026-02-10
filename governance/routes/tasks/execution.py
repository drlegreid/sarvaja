"""
Tasks Execution Log Routes.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/routes/tasks.py

Created: 2026-01-04 (GAP-FILE-020)
Per ORCH-007: Task execution timeline logging.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import logging
import uuid

from governance.models import TaskExecutionEvent, TaskExecutionResponse
from governance.stores import (
    get_typedb_client,
    _tasks_store, _execution_events_store,
    synthesize_execution_events
)
from governance.stores.audit import record_audit

logger = logging.getLogger(__name__)
router = APIRouter()


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
        except Exception as e:
            logger.debug(f"Failed to check task existence in TypeDB: {e}")

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

    # Store event (cap at 100 per task to prevent unbounded growth)
    if task_id not in _execution_events_store:
        _execution_events_store[task_id] = []
    _execution_events_store[task_id].append(event)
    if len(_execution_events_store[task_id]) > 100:
        _execution_events_store[task_id] = _execution_events_store[task_id][-100:]

    record_audit(event_type.upper(), "task", task_id,
                 actor_id=agent_id or "system",
                 metadata={"message": message, "event_id": event["event_id"]})
    return TaskExecutionEvent(**event)
