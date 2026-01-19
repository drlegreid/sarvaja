"""Tasks CRUD Routes. Per RULE-032: File Size Limit (< 300 lines)."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from governance.models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    PaginatedTaskResponse,
    PaginationMeta,
)
from governance.stores import (
    get_typedb_client,
    get_all_tasks_from_typedb,
    TypeDBUnavailable,
    _tasks_store,
    task_to_response
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/tasks", response_model=PaginatedTaskResponse)
async def list_tasks(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                     sort_by: str = Query("task_id"), order: str = Query("asc"),
                     phase: Optional[str] = None, status: Optional[str] = None, agent_id: Optional[str] = None):
    """List tasks with pagination, sorting, and filtering. Per GAP-UI-036, EPIC-DR-003."""
    try:
        tasks = get_all_tasks_from_typedb(status=status, phase=phase, agent_id=agent_id, allow_fallback=True)
        total = len(tasks)
        sort_field = sort_by if sort_by in ["task_id", "status", "phase", "name"] else "task_id"
        tasks.sort(key=lambda t: t.get(sort_field) or "", reverse=order.lower() == "desc")
        paginated_tasks = tasks[offset:offset + limit]
        returned = len(paginated_tasks)
        pagination = PaginationMeta(total=total, offset=offset, limit=limit, has_more=(offset + returned) < total, returned=returned)
        return PaginatedTaskResponse(items=[TaskResponse(**t) for t in paginated_tasks], pagination=pagination)
    except TypeDBUnavailable as e:
        logger.error(f"TypeDB unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")

@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task. Per GAP-DATA-001, GAP-ARCH-001."""
    client = get_typedb_client()
    if client:
        try:
            if client.get_task(task.task_id):
                raise HTTPException(status_code=409, detail=f"Task {task.task_id} already exists")
            created = client.insert_task(task_id=task.task_id, name=task.description, status=task.status,
                                         phase=task.phase, body=task.body, gap_id=task.gap_id,
                                         linked_rules=task.linked_rules, linked_sessions=task.linked_sessions)
            if created:
                return task_to_response(created)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB task insert failed, using fallback: {e}")
    if task.task_id in _tasks_store:
        raise HTTPException(status_code=409, detail=f"Task {task.task_id} already exists")
    task_data = {"task_id": task.task_id, "description": task.description, "phase": task.phase,
                 "status": task.status, "agent_id": task.agent_id, "body": task.body,
                 "linked_rules": task.linked_rules, "linked_sessions": task.linked_sessions,
                 "gap_id": task.gap_id, "created_at": datetime.now().isoformat()}
    _tasks_store[task.task_id] = task_data
    return TaskResponse(**task_data)

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task by ID. Per GAP-EXPLOR-API-001."""
    client = get_typedb_client()
    if client:
        try:
            task = client.get_task(task_id)
            if task:
                return task_to_response(task)
        except Exception as e:
            logger.warning(f"TypeDB task get failed, using fallback: {e}")
    if task_id in _tasks_store:
        return TaskResponse(**_tasks_store[task_id])
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, update: TaskUpdate):
    """Update task fields. Per GAP-UI-107, GAP-ARCH-001."""
    client, task_obj = get_typedb_client(), None
    if client:
        try:
            task_obj = client.get_task(task_id)
            if not task_obj:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            if update.status or update.evidence:
                updated = client.update_task_status(task_id, update.status or task_obj.status,
                                                    update.agent_id or task_obj.agent_id, evidence=update.evidence)
                task_obj = updated or task_obj
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB task update failed, using fallback: {e}")
    if task_id not in _tasks_store:
        if client and task_obj:
            # Convert Task object to dict for fallback store (proper datetime handling)
            created_at = task_obj.created_at.isoformat() if task_obj.created_at else datetime.now().isoformat()
            _tasks_store[task_id] = {
                "task_id": task_id,
                "description": task_obj.name or task_obj.description or "",
                "phase": task_obj.phase or "",
                "status": task_obj.status or "TODO",
                "resolution": getattr(task_obj, 'resolution', None),
                "agent_id": task_obj.agent_id,
                "created_at": created_at,
                "body": getattr(task_obj, 'body', None),
                "gap_id": getattr(task_obj, 'gap_id', None),
            }
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    for field in ["description", "phase", "status", "agent_id", "body", "linked_rules", "linked_sessions", "gap_id", "evidence"]:
        val = getattr(update, field, None)
        if val is not None:
            _tasks_store[task_id][field] = val if field != "agent_id" or val else None
            if field == "status" and val == "DONE":
                _tasks_store[task_id]["completed_at"] = datetime.now().isoformat()
    return TaskResponse(**_tasks_store[task_id])

@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Delete a task. Per GAP-ARCH-001."""
    client = get_typedb_client()
    if client:
        try:
            if client.get_task(task_id) and client.delete_task(task_id):
                return None
        except Exception as e:
            logger.warning(f"TypeDB task delete failed, using fallback: {e}")
    if task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    del _tasks_store[task_id]
    return None

@router.post("/tasks/{task_id}/rules/{rule_id}", status_code=201)
async def link_task_to_rule(task_id: str, rule_id: str):
    """Link task to rule via implements-rule relation. Per GAP-LINK-002."""
    client = get_typedb_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB unavailable")
    try:
        if not client.get_task(task_id):
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        if client.link_task_to_rule(task_id, rule_id):
            return {"task_id": task_id, "rule_id": rule_id, "linked": True}
        raise HTTPException(status_code=400, detail="Failed to create link")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to link task {task_id} to rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/{task_id}/sessions/{session_id}", status_code=201)
async def link_task_to_session(task_id: str, session_id: str):
    """Link task to session via completed-in relation. Per GAP-LINK-001."""
    client = get_typedb_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB unavailable")
    try:
        if not client.get_task(task_id):
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        if client.link_task_to_session(task_id, session_id):
            return {"task_id": task_id, "session_id": session_id, "linked": True}
        raise HTTPException(status_code=400, detail="Failed to create link")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to link task {task_id} to session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
