"""
Hybrid Query Router - TypeDB + ChromaDB Integration
Routes queries to appropriate backend based on query type.

**Refactored: 2024-12-28 per GAP-FILE-012**
Original: 742 lines -> Package with 3 modules (~560 lines total)

Created: 2024-12-24 (P3.1)
Refactored: 2024-12-28 (GAP-FILE-012)
Per: RULE-004 (Executable Spec), RULE-010 (Evidence-Based Wisdom)

Query Routing Logic:
- Inference queries (dependencies, conflicts) → TypeDB
- Semantic queries (natural language search) → ChromaDB
- Combined queries (typed + semantic) → Both, merged results
- Fallback: TypeDB timeout → ChromaDB semantic search

Usage:
    router = HybridQueryRouter()

    # Inference query (TypeDB)
    deps = router.query("What depends on RULE-001?", query_type="inference")

    # Semantic query (ChromaDB)
    results = router.query("authentication rules", query_type="semantic")

    # Auto-detect query type
    results = router.query("Find all governance rules about sessions")
"""

# =============================================================================
# RE-EXPORTS FROM PACKAGE (Backward Compatibility)
# =============================================================================

from governance.hybrid import (
    # Data models
    QueryType,
    QueryResult,
    SyncStatus,
    # Router
    HybridQueryRouter,
    # Sync bridge
    MemorySyncBridge,
)

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Data models
    "QueryType",
    "QueryResult",
    "SyncStatus",
    # Router
    "HybridQueryRouter",
    # Sync bridge
    "MemorySyncBridge",
]

# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Hybrid Query Router Test (Refactored)")
    print("=" * 60)

    router = HybridQueryRouter()
    status = router.connect()
    print(f"\nConnection status: {status}")

    health = router.health_check()
    print(f"Health: {health}")

    # Test queries
    test_queries = [
        ("What depends on RULE-001?", "inference"),
        ("Find governance rules", "semantic"),
        ("RULE-012 DSP protocol", "auto"),
        ("conflicts between rules", "inference"),
    ]

    print("\n--- Query Tests ---")
    for query, qtype in test_queries:
        result = router.query(query, query_type=qtype)
        print(f"\n[{result.query_type.value}] '{query}'")
        print(f"  Source: {result.source}")
        print(f"  Results: {result.count}")
        print(f"  Latency: {result.latency_ms:.1f}ms")
        if result.fallback_used:
            print(f"  Fallback: Yes")
        if result.error:
            print(f"  Error: {result.error}")

    router.close()
    print("\n[OK] Router test complete!")
