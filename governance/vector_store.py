"""
TypeDB Vector Store Bridge - Backward Compatibility Wrapper.

Per RULE-032: This file was modularized into governance/vector_store/ module.
Original: 531 lines → Now: ~50 lines (90% reduction).

The actual implementation is in:
- governance/vector_store/models.py     (VectorDocument, SimilarityResult)
- governance/vector_store/store.py      (VectorStore class)
- governance/vector_store/embeddings.py (EmbeddingGenerator implementations)
- governance/vector_store/helpers.py    (create_vector_from_* functions)

This file re-exports all public symbols for backward compatibility.

PURPOSE:
Bridge layer for vector embeddings in TypeDB 2.x (which lacks native vector support).
Stores embeddings as JSON strings and performs similarity computation in Python.

MIGRATION PATH:
When TypeDB 3.x is stable, this module will be refactored to use native vector types.
See DECISION-003: TypeDB-First Strategy for full migration plan.
"""

# Re-export all public symbols from the module
from governance.vector_store import (
    # Data Models
    VectorDocument,
    SimilarityResult,
    # Main Store
    VectorStore,
    # Embedding Generators
    EmbeddingGenerator,
    MockEmbeddings,
    OllamaEmbeddings,
    LiteLLMEmbeddings,
    # Convenience Functions
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


# =============================================================================
# CLI FOR TESTING (preserved from original)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TypeDB Vector Store Test (P7.1)")
    print("=" * 60)

    # Test with mock embeddings
    generator = MockEmbeddings(dimension=384)
    print(f"\nUsing: {generator.model_name} ({generator.dimension} dims)")

    # Create test vectors
    docs = [
        create_vector_from_rule(
            "RULE-001",
            "Session Evidence Logging: All sessions must produce evidence artifacts",
            generator
        ),
        create_vector_from_rule(
            "RULE-011",
            "Multi-Agent Governance: Trust-weighted voting for rule changes",
            generator
        ),
        create_vector_from_decision(
            "DECISION-003",
            "TypeDB-First Strategy: Unify semantic and logical queries",
            generator
        ),
    ]

    print(f"\nCreated {len(docs)} test vectors")

    # Test similarity search (without TypeDB connection)
    store = VectorStore()
    store._cache = {doc.id: doc for doc in docs}

    query = generator.generate("evidence and logging requirements")
    results = store.search(query, top_k=3)

    print("\n--- Similarity Search Results ---")
    for r in results:
        print(f"  [{r.score:.4f}] {r.source}: {r.content[:50]}...")

    print("\n[OK] Vector store test complete!")
