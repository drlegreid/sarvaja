"""
Evidence Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-UI-009: Evidence search API endpoint.

Created: 2024-12-28
Updated: 2026-01-10 (added search endpoint)
"""

import glob
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from governance.models import (
    EvidenceResponse,
    EvidenceSearchResponse,
    EvidenceSearchResult
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Evidence"])


def _extract_session_id(filename: str) -> str:
    """Extract session ID from filename pattern SESSION-YYYY-MM-DD-NNN.md."""
    match = re.match(r'(SESSION-\d{4}-\d{2}-\d{2}-\d+)', filename)
    return match.group(1) if match else None


# =============================================================================
# EVIDENCE ENDPOINTS
# =============================================================================

@router.get("/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(20, ge=1, le=200, description="Max results (1-200)"),
):
    """List evidence from evidence/ directory with session linkage."""
    evidence_dir = os.path.join(os.path.dirname(__file__), "..", "..", "evidence")
    evidence_list = []

    if os.path.exists(evidence_dir):
        md_files = sorted(
            [f for f in os.listdir(evidence_dir) if f.endswith(".md")]
        )
        for filename in md_files[offset:offset + limit]:
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
            except Exception as e:
                logger.warning(f"Failed to read evidence file {filename}: {e}")

    return evidence_list


# NOTE: /evidence/search MUST be defined BEFORE /evidence/{evidence_id}
# to avoid FastAPI matching "search" as an evidence_id parameter
@router.get("/evidence/search", response_model=EvidenceSearchResponse)
async def search_evidence(
    query: str = Query(..., min_length=2, description="Search query"),
    top_k: int = Query(5, ge=1, le=20, description="Max results"),
    source_type: Optional[str] = Query(None, description="Filter: session, evidence, rule")
):
    """
    Semantic search across evidence artifacts.

    Per GAP-UI-009: Evidence search functionality.
    Tries vector search first, falls back to keyword search.
    """
    evidence_dir = os.path.join(os.path.dirname(__file__), "..", "..", "evidence")
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "docs")

    # Try vector/semantic search first
    # Per GAP-EMBED-001: Use env-configured embedding generator
    semantic_results = []
    try:
        from governance.vector_store import VectorStore
        from governance.embedding_config import create_embedding_generator

        store = VectorStore()
        generator = create_embedding_generator()

        if store.connect():
            query_embedding = generator.generate(query)
            semantic_results = store.search(query_embedding, top_k=top_k, source_type=source_type)
            store.close()

            if semantic_results:
                return EvidenceSearchResponse(
                    query=query,
                    results=[
                        EvidenceSearchResult(
                            source=r.source,
                            source_type=r.source_type,
                            score=round(r.score, 4),
                            content=r.content[:200] + "..." if len(r.content) > 200 else r.content
                        )
                        for r in semantic_results
                    ],
                    count=len(semantic_results),
                    search_method="semantic_vector"
                )
    except Exception as e:
        logger.debug(f"Semantic search unavailable, falling back to keyword: {e}")

    # Keyword search fallback
    results = []
    query_lower = query.lower()

    # Search evidence files
    search_patterns = [
        (os.path.join(evidence_dir, "*.md"), "evidence"),
        (os.path.join(docs_dir, "rules", "*.md"), "rule"),
    ]

    for pattern, file_type in search_patterns:
        # Skip if source_type filter doesn't match
        if source_type and source_type != file_type:
            continue

        for filepath in glob.glob(pattern):
            try:
                path = Path(filepath)
                content = path.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    # Count occurrences as relevance score
                    score = content.lower().count(query_lower)
                    results.append(EvidenceSearchResult(
                        source=path.stem,
                        source_type=file_type,
                        score=float(score),
                        content=content[:200] + "..." if len(content) > 200 else content
                    ))
            except Exception as e:
                logger.warning(f"Failed to search file {filepath}: {e}")
                continue

    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)

    return EvidenceSearchResponse(
        query=query,
        results=results[:top_k],
        count=len(results[:top_k]),
        search_method="keyword_fallback"
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str):
    """Get specific evidence by ID with session linkage."""
    evidence_dir = os.path.join(os.path.dirname(__file__), "..", "..", "evidence")
    filepath = os.path.join(evidence_dir, f"{evidence_id}.md")

    # Prevent path traversal: resolved path must stay within evidence_dir
    real_path = os.path.realpath(filepath)
    real_evidence_dir = os.path.realpath(evidence_dir)
    if not real_path.startswith(real_evidence_dir + os.sep):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")

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
