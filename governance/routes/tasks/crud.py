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
    # BUG-237-SORT-001: Whitelist sort_by to prevent unexpected sort keys
    _valid_sort = {"task_id", "status", "phase", "priority"}
    if sort_by not in _valid_sort:
        raise HTTPException(status_code=422, detail=f"Invalid sort_by: {sort_by}. Must be one of {sorted(_valid_sort)}")
    # BUG-253-INJ-001: Whitelist order direction to prevent injection
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="order must be 'asc' or 'desc'")
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
    # BUG-273-TASKS-001 + BUG-365-RT-001: Log full error, return only type name
    except Exception as e:
        logger.error(f"list_tasks failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {type(e).__name__}")


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task. Per GAP-DATA-001, GAP-ARCH-001."""
    try:
        result = task_service.create_task(
            task_id=task.task_id, description=task.description,
            status=task.status, phase=task.phase,
            priority=task.priority, task_type=task.task_type,
            agent_id=task.agent_id, body=task.body,
            gap_id=task.gap_id, linked_rules=task.linked_rules,
            linked_sessions=task.linked_sessions,
            linked_documents=task.linked_documents, source="rest-api",
        )
        # Service returns TaskResponse directly (via task_to_response)
        if isinstance(result, TaskResponse):
            return result
        return TaskResponse(**result)
    # BUG-381-TSK-001: Log full error but return only type name to prevent info disclosure
    except ValueError as e:
        logger.warning(f"create_task conflict: {e}")
        raise HTTPException(status_code=409, detail=f"Task conflict: {type(e).__name__}")
    except Exception as e:
        logger.error(f"create_task failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create task: {type(e).__name__}")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task by ID. Per GAP-EXPLOR-API-001."""
    # BUG-ROUTE-NOEXCEPT-001: Add try-except matching create_task pattern
    try:
        result = task_service.get_task(task_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        if isinstance(result, TaskResponse):
            return result
        return TaskResponse(**result)
    except HTTPException:
        raise
    # BUG-365-RT-001: Log full error, return only type name to prevent info disclosure
    except Exception as e:
        logger.error(f"get_task failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get task: {type(e).__name__}")


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, update: TaskUpdate):
    """Update task fields. Per GAP-UI-107, GAP-ARCH-001."""
    # BUG-ROUTE-NOEXCEPT-001: Add try-except matching create_task pattern
    try:
        result = task_service.update_task(
            task_id=task_id,
            description=update.description,
            status=update.status,
            phase=update.phase,
            priority=update.priority,
            task_type=update.task_type,
            agent_id=update.agent_id,
            body=update.body,
            evidence=update.evidence,
            linked_rules=update.linked_rules,
            linked_sessions=update.linked_sessions,
            linked_documents=update.linked_documents,
            gap_id=update.gap_id,
            source="rest-api",
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        if isinstance(result, TaskResponse):
            return result
        return TaskResponse(**result)
    except HTTPException:
        raise
    # BUG-365-RT-001: Log full error, return only type name to prevent info disclosure
    except Exception as e:
        logger.error(f"update_task failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update task: {type(e).__name__}")


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Delete a task. Per GAP-ARCH-001."""
    # BUG-ROUTE-NOEXCEPT-001: Add try-except matching create_task pattern
    try:
        if not task_service.delete_task(task_id, source="rest-api"):
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return None
    except HTTPException:
        raise
    # BUG-365-RT-001: Log full error, return only type name to prevent info disclosure
    except Exception as e:
        logger.error(f"delete_task failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {type(e).__name__}")


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


@router.get("/tasks/{task_id}/sessions")
async def get_task_sessions(task_id: str):
    """Get all sessions linked to a task. Reverse query for completed-in relations."""
    # BUG-224-TASK-003: Check task existence BEFORE fetching sessions (was TOCTOU)
    if not task_service.get_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    sessions = task_service.get_sessions_for_task(task_id)
    return {"task_id": task_id, "sessions": sessions, "count": len(sessions)}


# Task Document Management endpoints

@router.post("/tasks/{task_id}/documents", status_code=201)
async def link_task_to_document(task_id: str, body: dict):
    """Link a document to a task via document-references-task relation."""
    document_path = body.get("document_path")
    if not document_path:
        raise HTTPException(status_code=422, detail="document_path is required")
    # BUG-328-TASK-001: Validate document_path length and basic format
    if not isinstance(document_path, str) or len(document_path) > 500:
        raise HTTPException(status_code=422, detail="document_path must be a string under 500 chars")
    if not task_service.link_task_to_document(task_id, document_path, source="rest-api"):
        raise HTTPException(status_code=400, detail="Failed to link document (task not found or TypeDB unavailable)")
    return {"task_id": task_id, "document_path": document_path, "linked": True}


@router.get("/tasks/{task_id}/documents")
async def get_task_documents(task_id: str):
    """Get all documents linked to a task."""
    result = task_service.get_task(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    docs = []
    if isinstance(result, TaskResponse):
        docs = result.linked_documents or []
    elif isinstance(result, dict):
        docs = result.get("linked_documents") or []
    return {"task_id": task_id, "documents": docs, "count": len(docs)}


@router.delete("/tasks/{task_id}/documents/{doc_id:path}", status_code=204)
async def unlink_task_document(task_id: str, doc_id: str):
    """Unlink a document from a task."""
    if not task_service.unlink_task_from_document(task_id, doc_id, source="rest-api"):
        raise HTTPException(status_code=400, detail="Failed to unlink document")
    return None
