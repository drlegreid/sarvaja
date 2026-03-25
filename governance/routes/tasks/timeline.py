"""Task Timeline Route — Multi-session chronological merge.

Per EPIC-ISSUE-EVIDENCE P18.
Endpoint: GET /api/tasks/{task_id}/timeline
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from governance.services.task_timeline import build_task_timeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tasks/{task_id}/timeline")
async def task_timeline(
    task_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
    entry_types: Optional[str] = Query(
        default=None,
        description="Comma-separated: tool_call,thought,decision,status_change",
    ),
):
    """Get chronological timeline of all session events for a task."""
    types_list = (
        [t.strip() for t in entry_types.split(",") if t.strip()]
        if entry_types
        else None
    )
    try:
        result = build_task_timeline(
            task_id, page=page, per_page=per_page, entry_types=types_list,
        )
    except Exception as e:
        logger.error(
            "Timeline build failed for %s: %s", task_id, type(e).__name__,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Timeline error: {type(e).__name__}")

    if result is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return result
