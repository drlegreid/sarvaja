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



@router.get("/sessions/{session_id}/evidence")
async def get_session_evidence(session_id: str):
    """
    Get all evidence files linked to a session.

    Per P11.5: Session Evidence Attachments.
    Per H-SESSION-002: Fallback to filesystem scan when TypeDB has no links.
    """
    client = get_typedb_client()
    evidence = []

    if client:
        try:
            session = client.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found"
                )
            evidence = client.get_session_evidence(session_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"TypeDB evidence query failed, using fallback: {e}")

    # H-SESSION-002: Filesystem fallback — scan evidence/ for matching files
    if not evidence:
        evidence = _scan_evidence_filesystem(session_id)

    # Deduplicate while preserving order (BUG-EVIDENCE-DEDUP-001)
    evidence = list(dict.fromkeys(evidence))

    return {
        "session_id": session_id,
        "evidence_count": len(evidence),
        "evidence_files": evidence
    }


def _scan_evidence_filesystem(session_id: str) -> list:
    """Scan evidence/ directory for files matching session ID.

    Per H-SESSION-002: Provides fallback when TypeDB evidence links are missing.
    """
    import os
    evidence_dir = os.path.join(os.getcwd(), "evidence")
    if not os.path.isdir(evidence_dir):
        return []

    matches = []
    for filename in os.listdir(evidence_dir):
        if not filename.endswith(".md"):
            continue
        # Match SESSION-{id}.md or DSM-{date} patterns
        if session_id in filename:
            matches.append(f"evidence/{filename}")

    return sorted(matches)
