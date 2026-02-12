"""Tasks Detail Section Routes.

Per TASK-TECH-01-v1: Technology Solution Documentation.
Per DOC-SIZE-01-v1: Separate module for detail section operations.

Endpoints:
- GET  /tasks/{task_id}/details — Get all detail sections
- PUT  /tasks/{task_id}/details — Update detail sections (batch)
"""
from fastapi import APIRouter, HTTPException
import logging

from governance.models import TaskDetailsUpdate, TaskDetailsResponse
from governance.services import tasks as task_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/tasks/{task_id}/details", response_model=TaskDetailsResponse)
async def get_task_details(task_id: str):
    """Get task detail sections (business, design, architecture, test).

    Per TASK-TECH-01-v1: Technology Solution Documentation.
    """
    result = task_service.get_task_details(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return TaskDetailsResponse(**result)


@router.put("/tasks/{task_id}/details", response_model=TaskDetailsResponse)
async def update_task_details(task_id: str, body: TaskDetailsUpdate):
    """Update task detail sections.

    Per TASK-TECH-01-v1: At least one section must be provided.
    """
    if not any([body.business, body.design, body.architecture, body.test_section]):
        raise HTTPException(
            status_code=422,
            detail="At least one detail section must be provided"
        )
    result = task_service.update_task_details(
        task_id,
        business=body.business,
        design=body.design,
        architecture=body.architecture,
        test_section=body.test_section,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return TaskDetailsResponse(**result)
