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
    # BUG-197-DETAIL-001: Wrap in try/except to prevent raw 500 on parse/IO errors
    try:
        result = get_session_detail(session_id, zoom=zoom, page=page, per_page=per_page)
    # BUG-366-DET-001: Log full error but return only type name to prevent info disclosure
    except Exception as e:
        # BUG-467-SDT-001: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Session detail failed for {session_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load session detail: {type(e).__name__}")
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
    # BUG-197-DETAIL-001: Wrap in try/except
    try:
        result = get_session_detail(session_id, zoom=2, page=page, per_page=per_page)
    # BUG-366-DET-001: Log full error but return only type name to prevent info disclosure
    except Exception as e:
        # BUG-467-SDT-002: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Session tools failed for {session_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load session tools: {type(e).__name__}")
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
    # BUG-197-DETAIL-001: Wrap in try/except
    try:
        result = get_session_detail(session_id, zoom=3, page=page, per_page=per_page)
    # BUG-366-DET-001: Log full error but return only type name to prevent info disclosure
    except Exception as e:
        # BUG-467-SDT-003: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Session thoughts failed for {session_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load session thoughts: {type(e).__name__}")
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
    # BUG-392-ERR-001: Wrap get_session in try/except — TypeDB errors can raise raw 500
    try:
        session = get_session(session_id)
    except Exception as e:
        # BUG-467-SDT-004: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"get_session failed for {session_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load session: {type(e).__name__}")
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

    # BUG-277-DETAIL-002: Cap file read to 512KB to prevent memory exhaustion
    file_size = p.stat().st_size
    if file_size > 512 * 1024:
        raise HTTPException(status_code=413, detail="Evidence file too large to render")

    content = p.read_text(encoding="utf-8", errors="replace")
    return {"session_id": session_id, "html": render_markdown(content), "raw": content}


@router.get("/ingestion/status/{session_id}")
def ingestion_status(session_id: str):
    """Get ingestion pipeline status for a session.

    Returns checkpoint data including phase, chunks indexed, and links created.
    Per SESSION-METRICS-01-v1.
    """
    # BUG-277-DETAIL-001: Wrap in try/except to prevent raw 500
    try:
        from governance.services.ingestion_orchestrator import get_ingestion_status
        return get_ingestion_status(session_id)
    except Exception as e:
        # BUG-392-ERR-002: Add exc_info=True for proper stack trace in logs
        # BUG-467-SDT-005: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Ingestion status failed for {session_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve ingestion status")
