"""
Tasks CRUD Routes.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/routes/tasks.py

Created: 2026-01-04 (GAP-FILE-020)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from governance.models import TaskCreate, TaskUpdate, TaskResponse
from governance.stores import (
    get_typedb_client,
    get_all_tasks_from_typedb,
    TypeDBUnavailable,
    _tasks_store,
    task_to_response
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(50, ge=1, le=200, description="Max results (1-200)"),
    sort_by: str = Query("task_id", description="Sort by: task_id, status, phase"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    phase: Optional[str] = Query(None, description="Filter by phase"),
    status: Optional[str] = Query(None, description="Filter by status"),
    agent_id: Optional[str] = Query(None, description="Filter by agent")
):
    """
    List tasks with pagination, sorting, and filtering.

    Per GAP-STUB-001/002: TypeDB is source of truth with fallback for resilience.
    Per GAP-UI-036: Pagination support.
    """
    try:
        # Use TypeDB wrapper (handles fallback internally)
        tasks = get_all_tasks_from_typedb(
            status=status,
            phase=phase,
            agent_id=agent_id,
            allow_fallback=True  # Keep fallback during migration
        )

        # Apply sorting
        valid_sort_fields = ["task_id", "status", "phase", "name"]
        sort_field = sort_by if sort_by in valid_sort_fields else "task_id"
        reverse = order.lower() == "desc"
        tasks.sort(key=lambda t: t.get(sort_field) or "", reverse=reverse)

        # Apply pagination
        tasks = tasks[offset:offset + limit]

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
