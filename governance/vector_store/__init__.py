"""
Vector Store Module.

Per RULE-032: Modularized from vector_store.py (531 lines → 5 modules).

TypeDB Vector Store Bridge (P7.1)
Bridge layer for vector embeddings in TypeDB 2.x (which lacks native vector support).
Stores embeddings as JSON strings and performs similarity computation in Python.

MIGRATION PATH:
When TypeDB 3.x is stable, this module will be refactored to use native vector types:
- vector-embedding: string → double[]
- similarity queries: Python → TypeQL `near` operator

See DECISION-003: TypeDB-First Strategy for full migration plan.
Per RULE-010: Evidence-Based Wisdom - measure before optimize.

Public API (backward compatible):
- VectorDocument, SimilarityResult: Data models
- VectorStore: Main store class
- EmbeddingGenerator, MockEmbeddings, OllamaEmbeddings, LiteLLMEmbeddings: Embeddings
- create_vector_from_*: Convenience functions

Module Structure:
- models.py: VectorDocument, SimilarityResult dataclasses
- store.py: VectorStore class
- embeddings.py: EmbeddingGenerator implementations
- helpers.py: Convenience functions
"""

# Data Models
from .models import VectorDocument, SimilarityResult

# Main Store
from .store import VectorStore

# Embedding Generators
from .embeddings import (
    EmbeddingGenerator,
    MockEmbeddings,
    OllamaEmbeddings,
    LiteLLMEmbeddings,
)

# Convenience Functions
from .helpers import (
    create_vector_from_rule,
    create_vector_from_decision,
    create_vector_from_session,
)

__all__ = [
    # Data Models
    "VectorDocument",
    "SimilarityResult",
    # Main Store
    "VectorStore",
    # Embedding Generators
    "EmbeddingGenerator",
    "MockEmbeddings",
    "OllamaEmbeddings",
    "LiteLLMEmbeddings",
    # Convenience Functions
    "create_vector_from_rule",
    "create_vector_from_decision",
    "create_vector_from_session",
]
