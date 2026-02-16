"""Session Detail & Lazy Loading Routes.

Per DATA-LAZY-01-v1: Zoom-level lazy loading for session detail.
Per Phase-2: Paginated tools, thoughts, and markdown rendering.
Created: 2026-02-11
"""

from fastapi import APIRouter, HTTPException, Query
import logging

from governance.services.cc_session_ingestion import (
    get_session_detail,
    render_markdown,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sessions"])


@router.get("/sessions/{session_id}/detail")
def session_detail(
    session_id: str,
    zoom: int = Query(default=1, ge=0, le=3),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    """Get session detail at specified zoom level.

    - zoom=0: Summary metadata only
    - zoom=1: + tool breakdown + thinking summary
    - zoom=2: + individual tool calls with inputs (paginated)
    - zoom=3: + full thinking content (paginated)
    """
    result = get_session_detail(session_id, zoom=zoom, page=page, per_page=per_page)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return result


@router.get("/sessions/{session_id}/tools")
def session_tools(
    session_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    """Get paginated tool calls for a session."""
    result = get_session_detail(session_id, zoom=2, page=page, per_page=per_page)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {
        "session_id": session_id,
        "tool_calls": result.get("tool_calls", []),
        "total": result.get("tool_calls_total", 0),
        "page": page,
        "per_page": per_page,
    }


@router.get("/sessions/{session_id}/thoughts")
def session_thoughts(
    session_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    """Get paginated thinking blocks for a session."""
    result = get_session_detail(session_id, zoom=3, page=page, per_page=per_page)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {
        "session_id": session_id,
        "thinking_blocks": result.get("thinking_blocks", []),
        "total": result.get("thinking_blocks_total", 0),
        "page": page,
        "per_page": per_page,
    }


@router.get("/sessions/{session_id}/evidence/rendered")
def session_evidence_rendered(session_id: str):
    """Get evidence file content rendered as HTML from markdown."""
    from governance.services.sessions import get_session
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    file_path = session.get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="No evidence file for this session")

    import os
    from pathlib import Path

    # BUG-ROUTE-PATH-001: Validate file_path stays within project evidence directory
    project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    evidence_dir = os.path.join(project_root, "evidence")
    real_path = os.path.realpath(file_path)
    real_evidence = os.path.realpath(evidence_dir)
    if not real_path.startswith(real_evidence + os.sep):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")

    p = Path(real_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found on disk")

    content = p.read_text(encoding="utf-8", errors="replace")
    return {"session_id": session_id, "html": render_markdown(content), "raw": content}


@router.get("/ingestion/status/{session_id}")
def ingestion_status(session_id: str):
    """Get ingestion pipeline status for a session.

    Returns checkpoint data including phase, chunks indexed, and links created.
    Per SESSION-METRICS-01-v1.
    """
    from governance.services.ingestion_orchestrator import get_ingestion_status
    return get_ingestion_status(session_id)
