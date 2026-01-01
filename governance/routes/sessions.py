"""
Sessions Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-ARCH-002: TypeDB-first with in-memory fallback.

Created: 2024-12-28
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import logging
import uuid

from pydantic import BaseModel
from governance.models import SessionResponse, SessionCreate, SessionEnd
from governance.stores import (
    get_typedb_client,
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
async def list_sessions():
    """
    List all sessions.

    Per GAP-ARCH-002: Queries TypeDB first, falls back to in-memory.
    """
    client = get_typedb_client()

    # Try TypeDB first
    if client:
        try:
            sessions = client.get_all_sessions()
            if sessions:
                return [session_to_response(s) for s in sessions]
        except Exception as e:
            logger.warning(f"TypeDB sessions query failed, using fallback: {e}")

    # Fallback to in-memory
    return [SessionResponse(**s) for s in _sessions_store.values()]


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
