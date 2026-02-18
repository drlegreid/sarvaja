"""
Vector Store Data Models.

Per RULE-032: Modularized from vector_store.py (531 lines).
Contains: VectorDocument and SimilarityResult dataclasses.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class VectorDocument:
    """Vector document entity for TypeDB storage."""
    id: str
    content: str
    embedding: List[float]
    model: str
    dimension: int
    source: str
    source_type: str  # rule, decision, session, document
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_typedb_insert(self) -> str:
        """Generate TypeQL insert statement."""
        embedding_json = json.dumps(self.embedding)
        created_at = self.created_at.isoformat() if self.created_at else datetime.now().isoformat()

        # BUG-279-VMODEL-001: Escape ALL string fields to prevent TypeQL injection
        return f"""
            insert $v isa vector-document,
                has vector-id "{self._escape(self.id)}",
                has vector-content "{self._escape(self.content)}",
                has vector-embedding "{self._escape(embedding_json)}",
                has vector-model "{self._escape(self.model)}",
                has vector-dimension {self.dimension},
                has vector-source "{self._escape(self.source)}",
                has vector-source-type "{self._escape(self.source_type)}",
                has vector-created-at {created_at};
        """

    @staticmethod
    def _escape(text: str) -> str:
        """Escape text for TypeQL string literals."""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


@dataclass
class SimilarityResult:
    """Result from similarity search."""
    vector_id: str
    content: str
    source: str
    source_type: str
    score: float
