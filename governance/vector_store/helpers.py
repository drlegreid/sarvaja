"""
Vector Store Convenience Functions.

Per RULE-032: Modularized from vector_store.py (531 lines).
Contains: Helper functions to create VectorDocuments from different sources.
"""

import uuid

from .models import VectorDocument
from .embeddings import EmbeddingGenerator


def create_vector_from_rule(rule_id: str, rule_text: str, generator: EmbeddingGenerator) -> VectorDocument:
    """Create vector document from a governance rule."""
    embedding = generator.generate(rule_text)
    return VectorDocument(
        id=str(uuid.uuid4()),
        content=rule_text,
        embedding=embedding,
        model=generator.model_name,
        dimension=generator.dimension,
        source=rule_id,
        source_type="rule"
    )


def create_vector_from_decision(decision_id: str, decision_text: str, generator: EmbeddingGenerator) -> VectorDocument:
    """Create vector document from a strategic decision."""
    embedding = generator.generate(decision_text)
    return VectorDocument(
        id=str(uuid.uuid4()),
        content=decision_text,
        embedding=embedding,
        model=generator.model_name,
        dimension=generator.dimension,
        source=decision_id,
        source_type="decision"
    )


def create_vector_from_session(session_id: str, session_text: str, generator: EmbeddingGenerator) -> VectorDocument:
    """Create vector document from a session evidence file."""
    embedding = generator.generate(session_text)
    return VectorDocument(
        id=str(uuid.uuid4()),
        content=session_text,
        embedding=embedding,
        model=generator.model_name,
        dimension=generator.dimension,
        source=session_id,
        source_type="session"
    )
