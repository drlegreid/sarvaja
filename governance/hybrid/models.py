"""
Hybrid Router Data Models
=========================
Dataclasses and enums for hybrid query routing.

Per RULE-004: Executable Spec
Per GAP-FILE-012: Extracted from hybrid_router.py

Created: 2024-12-28
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """Query type for routing."""
    INFERENCE = "inference"   # TypeDB: dependencies, conflicts, relations
    SEMANTIC = "semantic"     # ChromaDB: natural language search
    COMBINED = "combined"     # Both: typed entities + semantic context
    AUTO = "auto"             # Auto-detect based on query content


@dataclass
class QueryResult:
    """Unified result from hybrid query."""
    query: str
    query_type: QueryType
    source: str  # "typedb", "chromadb", "both"
    results: List[Dict[str, Any]]
    count: int
    latency_ms: float
    fallback_used: bool = False
    error: Optional[str] = None


@dataclass
class SyncStatus:
    """Status of sync operation."""
    source: str
    target: str
    synced_count: int
    skipped_count: int
    error_count: int
    last_sync: Optional[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


__all__ = [
    "QueryType",
    "QueryResult",
    "SyncStatus",
]
