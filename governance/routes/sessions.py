"""
Sessions Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-STUB-003/004: TypeDB is source of truth (in-memory fallback deprecated).

Created: 2024-12-28
Updated: 2025-01-01 (TypeDB-first refactoring)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging
import uuid

from pydantic import BaseModel
from governance.models import SessionResponse, SessionCreate, SessionEnd, SessionUpdate
from governance.stores import (
    get_typedb_client,
    # TypeDB-first wrappers (preferred)
    get_all_sessions_from_typedb,
    get_session_from_typedb,
    TypeDBUnavailable,
    # Legacy stores (deprecated - kept for backward compatibility)
    _sessions_store,
    session_to_response
)


class EvidenceLink(BaseModel):
    """Request model for linking evidence to a session."""
    evidence_source: str

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sessions"])


# =============================================================================
# SESSIONS CRUD
# =============================================================================

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(50, ge=1, le=200, description="Max results (1-200)"),
    sort_by: str = Query("started_at", description="Sort by: started_at, session_id, status"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, COMPLETED"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID")
):
    """
    List sessions with pagination, sorting, and filtering.

    Per GAP-STUB-003/004: TypeDB is source of truth with fallback for resilience.
    Per GAP-UI-036: Pagination support.
    """
    try:
        # Use TypeDB wrapper (handles fallback internally)
        sessions = get_all_sessions_from_typedb(allow_fallback=True)

        # Apply filters
        if status:
            sessions = [s for s in sessions if s.get("status") == status]
        if agent_id:
            sessions = [s for s in sessions if s.get("agent_id") == agent_id]

        # Apply sorting
        valid_sort_fields = ["started_at", "session_id", "status", "start_time"]
        sort_field = sort_by if sort_by in valid_sort_fields else "started_at"
        # Map started_at to start_time for backward compatibility
        if sort_field == "started_at":
            sort_field = "start_time"
        reverse = order.lower() == "desc"
        sessions.sort(key=lambda s: s.get(sort_field) or "", reverse=reverse)

        # Apply pagination
        total = len(sessions)
        sessions = sessions[offset:offset + limit]

        # Add pagination metadata via headers would be ideal, but return in response for now
        return [SessionResponse(**s) for s in sessions]
    except TypeDBUnavailable as e:
        logger.error(f"TypeDB unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(session: SessionCreate):
    """
    Create a new session.

    Per GAP-ARCH-002: Creates in TypeDB if available, otherwise in-memory.
    """
    # Generate session ID if not provided
    session_id = session.session_id
    if not session_id:
        # Use UUID to ensure uniqueness across TypeDB and in-memory
        session_id = f"SESSION-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6].upper()}"

    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            created = client.insert_session(
                session_id=session_id,
                description=session.description,
                agent_id=session.agent_id
            )
            if created:
                return session_to_response(created)
        except Exception as e:
            logger.warning(f"TypeDB session insert failed, using fallback: {e}")

    # Fallback to in-memory
    if session_id in _sessions_store:
        raise HTTPException(status_code=409, detail=f"Session {session_id} already exists")

    session_data = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat(),
        "status": "ACTIVE",
        "tasks_completed": 0,
        "description": session.description,
        "agent_id": session.agent_id
    }
    _sessions_store[session_id] = session_data
    return SessionResponse(**session_data)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    Get a specific session by ID.

    Per GAP-UI-034: Session CRUD operations.
    """
    try:
        session = get_session_from_typedb(session_id, allow_fallback=True)
        if session:
            return SessionResponse(**session)
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except TypeDBUnavailable as e:
        logger.error(f"TypeDB unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, data: SessionUpdate):
    """
    Update a session.

    Per GAP-UI-034: Session CRUD operations.
    """
    client = get_typedb_client()

    if not client:
        # Fallback to in-memory
        if session_id not in _sessions_store:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        session = _sessions_store[session_id]
        if data.description is not None:
            session["description"] = data.description
        if data.status is not None:
            session["status"] = data.status
        if data.tasks_completed is not None:
            session["tasks_completed"] = data.tasks_completed
        if data.agent_id is not None:
            session["agent_id"] = data.agent_id
        return SessionResponse(**session)

    try:
        # Check session exists in TypeDB
        existing = client.get_session(session_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Update session in TypeDB
        updated = client.update_session(
            session_id=session_id,
            description=data.description,
            status=data.status,
            tasks_completed=data.tasks_completed,
            agent_id=data.agent_id
        )
        if updated:
            return session_to_response(updated)
        raise HTTPException(status_code=500, detail="Failed to update session")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """
    Delete a session.

    Per GAP-UI-034: Session CRUD operations.
    """
    client = get_typedb_client()

    if not client:
        # Fallback to in-memory
        if session_id not in _sessions_store:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        del _sessions_store[session_id]
        return None

    try:
        # Check session exists in TypeDB
        existing = client.get_session(session_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Delete session from TypeDB
        deleted = client.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: str, data: Optional[SessionEnd] = None):
    """
    End an active session.

    Per GAP-ARCH-002: Updates TypeDB if available, otherwise in-memory.
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            session = client.get_session(session_id)
            if session:
                # End the session using the correct method
                updated = client.end_session(session_id)
                if updated:
                    return session_to_response(updated)
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to end session {session_id}"
                    )
            # Session not found in TypeDB, fall through to in-memory check
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB session update failed, using fallback: {e}")

    # Fallback to in-memory
    if session_id not in _sessions_store:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    session = _sessions_store[session_id]

    if session.get("status") == "COMPLETED":
        raise HTTPException(status_code=409, detail=f"Session {session_id} already completed")

    session["status"] = "COMPLETED"
    session["end_time"] = datetime.now().isoformat()

    if data:
        if data.tasks_completed is not None:
            session["tasks_completed"] = data.tasks_completed
        if data.evidence_files is not None:
            session["evidence_files"] = data.evidence_files

    return SessionResponse(**session)


# =============================================================================
# SESSION EVIDENCE LINKING (P11.5)
# =============================================================================

@router.post("/sessions/{session_id}/evidence", status_code=201)
async def link_evidence_to_session(session_id: str, data: EvidenceLink):
    """
    Link an evidence file to a session.

    Per P11.5: Session Evidence Attachments.
    Per GAP-DATA-003: Evidence attachment functionality.
    """
    client = get_typedb_client()

    if not client:
        raise HTTPException(
            status_code=503,
            detail="TypeDB not available. Evidence linking requires TypeDB."
        )

    try:
        # Verify session exists
        session = client.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        # Link evidence
        success = client.link_evidence_to_session(session_id, data.evidence_source)
        if success:
            return {
                "message": f"Evidence linked successfully",
                "session_id": session_id,
                "evidence_source": data.evidence_source
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to link evidence"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking evidence to session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/evidence")
async def get_session_evidence(session_id: str):
    """
    Get all evidence files linked to a session.

    Per P11.5: Session Evidence Attachments.
    """
    client = get_typedb_client()

    if not client:
        raise HTTPException(
            status_code=503,
            detail="TypeDB not available"
        )

    try:
        # Verify session exists
        session = client.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        evidence = client.get_session_evidence(session_id)
        return {
            "session_id": session_id,
            "evidence_count": len(evidence),
            "evidence_files": evidence
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))
