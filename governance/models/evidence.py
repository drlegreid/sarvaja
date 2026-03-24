"""Evidence models. Per GAP-UI-009, GAP-DATA-003."""

from pydantic import BaseModel
from typing import List, Optional


class EvidenceResponse(BaseModel):
    """Response model for evidence."""
    evidence_id: str
    source: str
    content: str
    created_at: str
    session_id: Optional[str] = None

class EvidenceSearchResult(BaseModel):
    """Single search result for evidence search (GAP-UI-009)."""
    source: str
    source_type: str
    score: float
    content: str

class EvidenceSearchResponse(BaseModel):
    """Response model for evidence search (GAP-UI-009)."""
    query: str
    results: List[EvidenceSearchResult]
    count: int
    search_method: str

class FileContentResponse(BaseModel):
    """Response model for file content (GAP-DATA-003)."""
    path: str
    content: str
    size: int
    modified_at: str
    exists: bool = True
    rendered_html: Optional[str] = None
