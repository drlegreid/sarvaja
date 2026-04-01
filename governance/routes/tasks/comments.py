"""Task Comments Route — Resolution comment thread.

Per EPIC-ISSUE-EVIDENCE P19.
Endpoints: GET/POST /api/tasks/{task_id}/comments
           DELETE /api/tasks/{task_id}/comments/{comment_id}
"""

import logging
from fastapi import APIRouter, HTTPException

from governance.models.task import TaskCommentCreate
from governance.services.task_comments import (
    add_comment,
    list_comments,
    delete_comment,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tasks/{task_id}/comments")
async def get_task_comments(
    task_id: str,
    offset: int = 0,
    limit: int = None,
):
    """Get comments for a task (chronological order).

    Per SRVJ-FEAT-AUDIT-TRAIL-01 P7: Supports pagination via offset/limit.
    """
    comments = list_comments(task_id, offset=offset, limit=limit)
    # Total is full count (before pagination) for UI paging controls
    all_count = len(list_comments(task_id))
    return {
        "task_id": task_id,
        "comments": comments,
        "total": all_count,
        "offset": offset,
        "limit": limit,
    }


@router.post("/tasks/{task_id}/comments", status_code=201)
async def post_task_comment(task_id: str, payload: TaskCommentCreate):
    """Add a comment to a task."""
    try:
        comment = add_comment(task_id, body=payload.body, author=payload.author)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return comment


@router.delete("/tasks/{task_id}/comments/{comment_id}")
async def remove_task_comment(task_id: str, comment_id: str):
    """Delete a comment from a task."""
    deleted = delete_comment(task_id, comment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")
    return {"deleted": True, "comment_id": comment_id}
