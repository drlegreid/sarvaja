"""Session Detail & Lazy Loading Routes.

Per DATA-LAZY-01-v1: Zoom-level lazy loading for session detail.
Created: 2026-02-11
"""

from fastapi import APIRouter, HTTPException, Query
import logging

from governance.services.cc_session_ingestion import get_session_detail

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sessions"])


@router.get("/sessions/{session_id}/detail")
def session_detail(
    session_id: str,
    zoom: int = Query(default=1, ge=0, le=3),
):
    """Get session detail at specified zoom level.

    - zoom=0: Summary metadata only
    - zoom=1: + tool breakdown + thinking summary
    - zoom=2: + individual tool calls with inputs
    - zoom=3: + full tool outputs (from JSONL)
    """
    result = get_session_detail(session_id, zoom=zoom)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return result
