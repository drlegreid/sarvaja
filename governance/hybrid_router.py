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

import logging

logger = logging.getLogger(__name__)

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
    logging.basicConfig(level=logging.INFO)
    logger.info("Hybrid Query Router Test (Refactored)")

    router = HybridQueryRouter()
    status = router.connect()
    logger.info(f"Connection status: {status}")

    health = router.health_check()
    logger.info(f"Health: {health}")

    # Test queries
    test_queries = [
        ("What depends on RULE-001?", "inference"),
        ("Find governance rules", "semantic"),
        ("RULE-012 DSP protocol", "auto"),
        ("conflicts between rules", "inference"),
    ]

    logger.info("Query Tests")
    for query, qtype in test_queries:
        result = router.query(query, query_type=qtype)
        logger.info(f"[{result.query_type.value}] '{query}'")
        logger.info(f"  Source: {result.source}")
        logger.info(f"  Results: {result.count}")
        logger.info(f"  Latency: {result.latency_ms:.1f}ms")
        if result.fallback_used:
            logger.info("  Fallback: Yes")
        if result.error:
            logger.error(f"  Error: {result.error}")

    router.close()
    logger.info("Router test complete!")
