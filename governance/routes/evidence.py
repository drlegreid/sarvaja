"""
Evidence Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.

Created: 2024-12-28
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime
import os
import re

from governance.models import EvidenceResponse

router = APIRouter(tags=["Evidence"])


def _extract_session_id(filename: str) -> str:
    """Extract session ID from filename pattern SESSION-YYYY-MM-DD-NNN.md."""
    match = re.match(r'(SESSION-\d{4}-\d{2}-\d{2}-\d+)', filename)
    return match.group(1) if match else None


# =============================================================================
# EVIDENCE ENDPOINTS
# =============================================================================

@router.get("/evidence", response_model=List[EvidenceResponse])
async def list_evidence(limit: int = Query(20, description="Max results")):
    """List evidence from evidence/ directory with session linkage."""
    evidence_dir = os.path.join(os.path.dirname(__file__), "..", "..", "evidence")
    evidence_list = []

    if os.path.exists(evidence_dir):
        for filename in os.listdir(evidence_dir)[:limit]:
            if filename.endswith(".md"):
                filepath = os.path.join(evidence_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()[:500]  # First 500 chars

                    session_id = _extract_session_id(filename)

                    evidence_list.append(EvidenceResponse(
                        evidence_id=filename.replace(".md", ""),
                        source=filename,
                        content=content,
                        created_at=datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                        session_id=session_id
                    ))
                except Exception:
                    pass

    return evidence_list


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str):
    """Get specific evidence by ID with session linkage."""
    evidence_dir = os.path.join(os.path.dirname(__file__), "..", "..", "evidence")
    filepath = os.path.join(evidence_dir, f"{evidence_id}.md")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Evidence {evidence_id} not found")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    session_id = _extract_session_id(f"{evidence_id}.md")

    return EvidenceResponse(
        evidence_id=evidence_id,
        source=f"{evidence_id}.md",
        content=content,
        created_at=datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
        session_id=session_id
    )
