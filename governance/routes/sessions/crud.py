"""Sessions CRUD Routes - Delegates to service layer for MCP compliance.

Per RULE-012: DSP Semantic Code Structure.
Per MCP enforcement: Uses governance.services.sessions for all operations.
Per DOC-SIZE-01-v1: Modularized from sessions.py.

Created: 2024-12-28
Updated: 2026-02-01 - Refactored to service layer delegation
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from governance.models import (
    SessionResponse, SessionCreate, SessionEnd, SessionUpdate,
    PaginatedSessionResponse, PaginationMeta
)
from governance.services import sessions as session_service
from governance.stores import TypeDBUnavailable

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sessions"])


def _ensure_response(result) -> SessionResponse:
    """Normalize service result to SessionResponse.

    Service layer may return a SessionResponse (from TypeDB path)
    or a dict (from in-memory fallback). Handle both.
    """
    return _ensure_response(result)


# =============================================================================
# SESSIONS CRUD
# =============================================================================

@router.get("/sessions", response_model=PaginatedSessionResponse)
async def list_sessions(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(50, ge=1, le=200, description="Max results (1-200)"),
    sort_by: str = Query("started_at", description="Sort by: started_at, session_id, status"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, COMPLETED"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID")
):
    """List sessions with pagination, sorting, and filtering. Per GAP-UI-036."""
    try:
        result = session_service.list_sessions(
            status=status, agent_id=agent_id,
            sort_by=sort_by, order=order, offset=offset, limit=limit,
        )
        pagination = PaginationMeta(
            total=result["total"], offset=result["offset"],
            limit=result["limit"], has_more=result["has_more"],
            returned=len(result["items"]),
        )
        return PaginatedSessionResponse(
            items=[_ensure_response(s) for s in result["items"]],
            pagination=pagination,
        )
    except (TypeDBUnavailable, ConnectionError) as e:
        logger.error(f"TypeDB unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(session: SessionCreate):
    """Create a new session. Per GAP-ARCH-002."""
    try:
        result = session_service.create_session(
            session_id=session.session_id,
            description=session.description,
            agent_id=session.agent_id,
            source="rest-api",
        )
        return _ensure_response(result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session by ID. Per GAP-UI-034."""
    try:
        session = session_service.get_session(session_id)
        if session:
            return _ensure_response(session)
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except (TypeDBUnavailable, ConnectionError) as e:
        logger.error(f"TypeDB unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, data: SessionUpdate):
    """Update a session. Per GAP-UI-034."""
    result = session_service.update_session(
        session_id=session_id,
        description=data.description,
        status=data.status,
        tasks_completed=data.tasks_completed,
        agent_id=data.agent_id,
        source="rest-api",
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return _ensure_response(result)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """Delete a session. Per GAP-UI-034."""
    if not session_service.delete_session(session_id, source="rest-api"):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return None


@router.put("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: str, data: Optional[SessionEnd] = None):
    """End an active session. Per GAP-ARCH-002."""
    try:
        result = session_service.end_session(
            session_id=session_id,
            tasks_completed=data.tasks_completed if data else None,
            evidence_files=data.evidence_files if data else None,
            source="rest-api",
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        if isinstance(result, SessionResponse):
            return result
        return SessionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
