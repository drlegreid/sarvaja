"""Tasks CRUD Routes - Delegates to service layer for MCP compliance.

Per RULE-032: File Size Limit (< 300 lines).
Per MCP enforcement: Uses governance.services.tasks for all operations.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from governance.models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    PaginatedTaskResponse,
    PaginationMeta,
)
from governance.services import tasks as task_service
from governance.stores import TypeDBUnavailable

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tasks", response_model=PaginatedTaskResponse)
async def list_tasks(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("task_id"),
    order: str = Query("asc"),
    phase: Optional[str] = None,
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """List tasks with pagination, sorting, and filtering. Per GAP-UI-036, EPIC-DR-003."""
    try:
        result = task_service.list_tasks(
            status=status, phase=phase, agent_id=agent_id,
            sort_by=sort_by, order=order, offset=offset, limit=limit,
        )
        pagination = PaginationMeta(
            total=result["total"], offset=result["offset"],
            limit=result["limit"], has_more=result["has_more"],
            returned=len(result["items"]),
        )
        return PaginatedTaskResponse(
            items=[TaskResponse(**t) for t in result["items"]],
            pagination=pagination,
        )
    except (TypeDBUnavailable, ConnectionError) as e:
        logger.error(f"TypeDB unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task. Per GAP-DATA-001, GAP-ARCH-001."""
    try:
        result = task_service.create_task(
            task_id=task.task_id, description=task.description,
            status=task.status, phase=task.phase,
            agent_id=task.agent_id, body=task.body,
            gap_id=task.gap_id, linked_rules=task.linked_rules,
            linked_sessions=task.linked_sessions, source="rest-api",
        )
        # Service returns TaskResponse directly (via task_to_response)
        if isinstance(result, TaskResponse):
            return result
        return TaskResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task by ID. Per GAP-EXPLOR-API-001."""
    result = task_service.get_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    # Service returns TaskResponse directly (via task_to_response)
    if isinstance(result, TaskResponse):
        return result
    return TaskResponse(**result)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, update: TaskUpdate):
    """Update task fields. Per GAP-UI-107, GAP-ARCH-001."""
    result = task_service.update_task(
        task_id=task_id,
        description=update.description,
        status=update.status,
        phase=update.phase,
        agent_id=update.agent_id,
        body=update.body,
        evidence=update.evidence,
        linked_rules=update.linked_rules,
        linked_sessions=update.linked_sessions,
        gap_id=update.gap_id,
        source="rest-api",
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    # Service returns TaskResponse directly (via task_to_response)
    if isinstance(result, TaskResponse):
        return result
    return TaskResponse(**result)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Delete a task. Per GAP-ARCH-001."""
    if not task_service.delete_task(task_id, source="rest-api"):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return None


@router.post("/tasks/{task_id}/rules/{rule_id}", status_code=201)
async def link_task_to_rule(task_id: str, rule_id: str):
    """Link task to rule via implements-rule relation. Per GAP-LINK-002."""
    if not task_service.link_task_to_rule(task_id, rule_id, source="rest-api"):
        raise HTTPException(status_code=400, detail="Failed to create link (task not found or TypeDB unavailable)")
    return {"task_id": task_id, "rule_id": rule_id, "linked": True}


@router.post("/tasks/{task_id}/sessions/{session_id}", status_code=201)
async def link_task_to_session(task_id: str, session_id: str):
    """Link task to session via completed-in relation. Per GAP-LINK-001."""
    if not task_service.link_task_to_session(task_id, session_id, source="rest-api"):
        raise HTTPException(status_code=400, detail="Failed to create link (task not found or TypeDB unavailable)")
    return {"task_id": task_id, "session_id": session_id, "linked": True}
