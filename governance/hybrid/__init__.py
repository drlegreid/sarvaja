"""
Hybrid Query Router Package
===========================
TypeDB + ChromaDB hybrid query routing and sync.

Per RULE-004: Executable Spec
Per RULE-010: Evidence-Based Wisdom
Per GAP-FILE-012: Extracted from hybrid_router.py

Original: 742 lines -> Package with 3 modules (~560 lines total)

Usage:
    from governance.hybrid import HybridQueryRouter, MemorySyncBridge

    router = HybridQueryRouter()
    router.connect()

    # Inference query (TypeDB)
    result = router.query("What depends on RULE-001?", query_type="inference")

    # Semantic query (ChromaDB)
    result = router.query("authentication rules", query_type="semantic")

    # Sync to ChromaDB
    bridge = MemorySyncBridge(router)
    bridge.sync_all()

Created: 2024-12-28
"""

# Data models
from .models import QueryType, QueryResult, SyncStatus

# Router
from .router import HybridQueryRouter

# Sync bridge
from .sync import MemorySyncBridge


__all__ = [
    # Data models
    "QueryType",
    "QueryResult",
    "SyncStatus",
    # Router
    "HybridQueryRouter",
    # Sync
    "MemorySyncBridge",
]
