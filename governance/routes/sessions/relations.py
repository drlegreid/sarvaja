"""
Session Relations Routes (Evidence, Tasks).

Per RULE-012: DSP Semantic Code Structure.
Per P11.5: Session Evidence Attachments.
Per GAP-DATA-003: Evidence attachment functionality.
Per DOC-SIZE-01-v1: Modularized from sessions.py.

Created: 2024-12-28
Updated: 2026-01-17 - Modularized to package
"""

from fastapi import APIRouter, HTTPException
import logging

from pydantic import BaseModel
from governance.stores import get_typedb_client


class EvidenceLink(BaseModel):
    """Request model for linking evidence to a session."""
    evidence_source: str


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sessions"])


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
                "message": "Evidence linked successfully",
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


@router.get("/sessions/{session_id}/tasks")
async def get_session_tasks(session_id: str):
    """
    Get all tasks linked to a session via completed-in relation.

    Per GAP-DATA-INTEGRITY-001 Phase 3: UI navigation.
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

        tasks = client.get_tasks_for_session(session_id)
        return {
            "session_id": session_id,
            "task_count": len(tasks),
            "tasks": tasks
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/tool_calls")
async def get_session_tool_calls(session_id: str):
    """
    Get tool calls recorded for a session.

    Per B.3: Load session tool calls in detail view.
    Returns tool calls from SessionCollector events stored in TypeDB/memory.
    """
    client = get_typedb_client()

    if not client:
        # Try in-memory session store as fallback
        from governance.stores import _sessions_store
        session_data = _sessions_store.get(session_id, {})
        tool_calls = session_data.get("tool_calls", [])
        return {"session_id": session_id, "tool_call_count": len(tool_calls), "tool_calls": tool_calls}

    try:
        session = client.get_session(session_id)
        if not session:
            from governance.stores import _sessions_store
            session_data = _sessions_store.get(session_id, {})
            tool_calls = session_data.get("tool_calls", [])
            return {"session_id": session_id, "tool_call_count": len(tool_calls), "tool_calls": tool_calls}

        # Try to get tool calls from TypeDB
        tool_calls = []
        if hasattr(client, 'get_session_tool_calls'):
            tool_calls = client.get_session_tool_calls(session_id)
        return {"session_id": session_id, "tool_call_count": len(tool_calls), "tool_calls": tool_calls}
    except Exception as e:
        logger.error(f"Error getting session tool calls: {e}")
        return {"session_id": session_id, "tool_call_count": 0, "tool_calls": []}


@router.get("/sessions/{session_id}/thoughts")
async def get_session_thoughts(session_id: str):
    """
    Get thinking/reasoning items recorded for a session.

    Per B.3: Load session thoughts in detail view.
    Returns thought events from SessionCollector stored in TypeDB/memory.
    """
    client = get_typedb_client()

    if not client:
        from governance.stores import _sessions_store
        session_data = _sessions_store.get(session_id, {})
        thoughts = session_data.get("thoughts", [])
        return {"session_id": session_id, "thought_count": len(thoughts), "thoughts": thoughts}

    try:
        session = client.get_session(session_id)
        if not session:
            from governance.stores import _sessions_store
            session_data = _sessions_store.get(session_id, {})
            thoughts = session_data.get("thoughts", [])
            return {"session_id": session_id, "thought_count": len(thoughts), "thoughts": thoughts}

        thoughts = []
        if hasattr(client, 'get_session_thoughts'):
            thoughts = client.get_session_thoughts(session_id)
        return {"session_id": session_id, "thought_count": len(thoughts), "thoughts": thoughts}
    except Exception as e:
        logger.error(f"Error getting session thoughts: {e}")
        return {"session_id": session_id, "thought_count": 0, "thoughts": []}


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
