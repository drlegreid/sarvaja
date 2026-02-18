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
    Fills required defaults for malformed memory-only sessions.
    """
    if isinstance(result, SessionResponse):
        return result
    if isinstance(result, dict):
        # BUG-294-SES-002: Copy to avoid mutating source dict; use sentinel, not datetime.now()
        data = dict(result)
        if not data.get("start_time"):
            data["start_time"] = "1970-01-01T00:00:00"
        data.setdefault("status", "ACTIVE")
        return SessionResponse(**data)
    return SessionResponse(**result)


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
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    date_from: Optional[str] = Query(None, description="Filter sessions starting from YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="Filter sessions up to YYYY-MM-DD"),
    exclude_test: bool = Query(False, description="Exclude test artifact sessions"),
    search: Optional[str] = Query(None, description="Keyword search across session_id, description, agent_id"),
):
    """List sessions with pagination, sorting, and filtering. Per GAP-UI-036."""
    # BUG-237-SORT-001: Whitelist sort_by to prevent unexpected sort keys
    _valid_sort = {"started_at", "session_id", "status"}
    if sort_by not in _valid_sort:
        raise HTTPException(status_code=422, detail=f"Invalid sort_by: {sort_by}. Must be one of {sorted(_valid_sort)}")
    # BUG-253-INJ-001: Whitelist order direction to prevent injection
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="order must be 'asc' or 'desc'")
    # BUG-294-SES-001: Validate date_from/date_to format to prevent silent filter corruption
    from datetime import date as _date_type
    for _dval, _dname in [(date_from, "date_from"), (date_to, "date_to")]:
        if _dval is not None:
            try:
                _date_type.fromisoformat(_dval)
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Invalid {_dname}: must be YYYY-MM-DD format")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")
    try:
        result = session_service.list_sessions(
            status=status, agent_id=agent_id,
            sort_by=sort_by, order=order, offset=offset, limit=limit,
            date_from=date_from, date_to=date_to,
            exclude_test=exclude_test,
            search=search,
        )
        pagination = PaginationMeta(
            total=result["total"], offset=result["offset"],
            limit=result["limit"], has_more=result["has_more"],
            returned=len(result["items"]),
        )
        items = []
        for s in result["items"]:
            try:
                items.append(_ensure_response(s))
            except Exception as e:
                sid = s.get("session_id", "?") if isinstance(s, dict) else "?"
                # BUG-414-CRD-001: Add exc_info for stack trace preservation
                # BUG-467-SCR-001: Sanitize logger message — exc_info=True already captures full stack
                logger.warning(f"Skipping malformed session {sid}: {type(e).__name__}", exc_info=True)
        pagination.returned = len(items)
        return PaginatedSessionResponse(
            items=items,
            pagination=pagination,
        )
    except (TypeDBUnavailable, ConnectionError) as e:
        # BUG-403-CRD-001: Add exc_info for stack trace preservation
        # BUG-467-SCR-002: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"TypeDB unavailable: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database service unavailable")
    # BUG-381-SES-003: Catch-all for unexpected exceptions (e.g. TypeError from malformed data)
    except Exception as e:
        # BUG-467-SCR-003: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"list_sessions failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {type(e).__name__}")


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(session: SessionCreate):
    """Create a new session. Per GAP-ARCH-002."""
    # BUG-197-001: Add broad exception handler matching other CRUD endpoints
    try:
        result = session_service.create_session(
            session_id=session.session_id,
            description=session.description,
            agent_id=session.agent_id,
            source="rest-api",
            cc_session_uuid=session.cc_session_uuid,
            cc_project_slug=session.cc_project_slug,
            cc_git_branch=session.cc_git_branch,
            cc_tool_count=session.cc_tool_count,
            cc_thinking_chars=session.cc_thinking_chars,
            cc_compaction_count=session.cc_compaction_count,
        )
        return _ensure_response(result)
    # BUG-381-SES-001: Log full error but return only type name to prevent info disclosure
    except ValueError as e:
        # BUG-403-CRD-001: Add exc_info for stack trace preservation
        # BUG-467-SCR-004: Sanitize logger message — exc_info=True already captures full stack
        logger.warning(f"create_session conflict: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=409, detail=f"Session conflict: {type(e).__name__}")
    except (TypeDBUnavailable, ConnectionError) as e:
        # BUG-403-CRD-001: Add exc_info for stack trace preservation
        # BUG-467-SCR-005: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"TypeDB unavailable during session create: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database service unavailable")
    except Exception as e:
        # BUG-352-INF-001: Log full error but return generic message to prevent info disclosure
        # BUG-467-SCR-006: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to create session: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session by ID. Per GAP-UI-034."""
    try:
        session = session_service.get_session(session_id)
        if session:
            return _ensure_response(session)
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except (TypeDBUnavailable, ConnectionError) as e:
        # BUG-403-CRD-001: Add exc_info for stack trace preservation
        # BUG-467-SCR-007: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"TypeDB unavailable: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database service unavailable")
    # BUG-403-CRD-002: Add catch-all for unexpected exceptions (matches other handlers)
    except Exception as e:
        # BUG-467-SCR-008: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"get_session failed: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session: {type(e).__name__}")


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, data: SessionUpdate):
    """Update a session. Per GAP-UI-034."""
    # BUG-ROUTE-MISSING-EXCEPT-002: Add try-except matching get_session pattern
    try:
        result = session_service.update_session(
            session_id=session_id,
            description=data.description,
            status=data.status,
            tasks_completed=data.tasks_completed,
            agent_id=data.agent_id,
            start_time=data.start_time,
            end_time=data.end_time,
            source="rest-api",
            cc_session_uuid=data.cc_session_uuid,
            cc_project_slug=data.cc_project_slug,
            cc_git_branch=data.cc_git_branch,
            cc_tool_count=data.cc_tool_count,
            cc_thinking_chars=data.cc_thinking_chars,
            cc_compaction_count=data.cc_compaction_count,
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return _ensure_response(result)
    except HTTPException:
        raise
    except Exception as e:
        # BUG-352-INF-001: Log full error but return generic message to prevent info disclosure
        # BUG-467-SCR-009: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to update session {session_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update session")


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """Delete a session. Per GAP-UI-034."""
    # BUG-190-004: Add try-except matching other session CRUD endpoints
    try:
        if not session_service.delete_session(session_id, source="rest-api"):
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        # BUG-352-INF-001: Log full error but return generic message to prevent info disclosure
        # BUG-467-SCR-010: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to delete session {session_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.put("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: str, data: Optional[SessionEnd] = None):
    """End an active session. Per GAP-ARCH-002."""
    # BUG-197-002: Add broad exception handler matching other CRUD endpoints
    try:
        result = session_service.end_session(
            session_id=session_id,
            tasks_completed=data.tasks_completed if data else None,
            evidence_files=data.evidence_files if data else None,
            source="rest-api",
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return _ensure_response(result)
    except HTTPException:
        raise
    # BUG-381-SES-002: Log full error but return only type name to prevent info disclosure
    except ValueError as e:
        # BUG-414-CRD-002: Add exc_info for stack trace preservation
        # BUG-467-SCR-011: Sanitize logger message — exc_info=True already captures full stack
        logger.warning(f"end_session conflict: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=409, detail="Session conflict")
    except Exception as e:
        # BUG-352-INF-001: Log full error but return generic message to prevent info disclosure
        # BUG-467-SCR-012: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to end session {session_id}: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to end session")
