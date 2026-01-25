"""
RF-004: Robot Framework Library for Hybrid Router Tests.

Wraps tests/test_hybrid_router.py for Robot Framework tests.
Tests routing logic between TypeDB (inference) and ChromaDB (semantic).
"""

import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class HybridRouterLibrary:
    """Robot Framework library for Hybrid Router tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_router(self):
        """Get a HybridQueryRouter instance."""
        from governance.hybrid_router import HybridQueryRouter
        return HybridQueryRouter()

    def detect_query_type(self, query: str) -> str:
        """Detect query type for a given query."""
        router = self._get_router()
        return router._detect_query_type(query)

    def test_inference_queries(self) -> Dict[str, str]:
        """Test inference query detection."""
        router = self._get_router()
        return {
            "depends_on": router._detect_query_type("What depends on RULE-001?"),
            "conflicts": router._detect_query_type("Show conflicts between RULE-001 and RULE-002"),
            "rule_id": router._detect_query_type("Show me RULE-012")
        }

    def test_semantic_queries(self) -> Dict[str, str]:
        """Test semantic query detection."""
        router = self._get_router()
        return {
            "about": router._detect_query_type("Tell me about authentication"),
            "find": router._detect_query_type("Find documents about security"),
            "what_is": router._detect_query_type("What is the best practice for logging?"),
            "ambiguous": router._detect_query_type("stuff")
        }

    def extract_rule_id(self, text: str) -> str:
        """Extract RULE-XXX from text."""
        router = self._get_router()
        result = router._extract_rule_id(text)
        return result if result else "None"

    def extract_decision_id(self, text: str) -> str:
        """Extract DECISION-XXX from text."""
        router = self._get_router()
        result = router._extract_decision_id(text)
        return result if result else "None"

    def test_query_result_creation(self) -> Dict[str, Any]:
        """Test QueryResult dataclass creation."""
        from governance.hybrid_router import QueryResult, QueryType
        result = QueryResult(
            query="test query",
            query_type=QueryType.SEMANTIC,
            source="chromadb",
            results=[{"doc": "test"}],
            count=1,
            latency_ms=10.5
        )
        return {
            "query": result.query,
            "query_type": str(result.query_type),
            "source": result.source,
            "count": result.count,
            "fallback_used": result.fallback_used,
            "error": result.error
        }

    def test_query_result_with_error(self) -> Dict[str, Any]:
        """Test QueryResult with error."""
        from governance.hybrid_router import QueryResult, QueryType
        result = QueryResult(
            query="failed query",
            query_type=QueryType.INFERENCE,
            source="error",
            results=[],
            count=0,
            latency_ms=50.0,
            error="Connection failed"
        )
        return {
            "error": result.error,
            "count": result.count
        }

    def test_default_config(self) -> Dict[str, Any]:
        """Test default configuration."""
        router = self._get_router()
        return {
            "typedb_host": router.typedb_host,
            "typedb_port": router.typedb_port,
            "chromadb_host": router.chromadb_host,
            "chromadb_port": router.chromadb_port,
            "timeout_ms": router.timeout_ms
        }

    def test_custom_config(self) -> Dict[str, Any]:
        """Test custom configuration."""
        from governance.hybrid_router import HybridQueryRouter
        router = HybridQueryRouter(
            typedb_host="typedb.local",
            typedb_port=1730,
            chromadb_host="chroma.local",
            chromadb_port=8002,
            timeout_ms=10000
        )
        return {
            "typedb_host": router.typedb_host,
            "typedb_port": router.typedb_port,
            "chromadb_host": router.chromadb_host,
            "chromadb_port": router.chromadb_port
        }

    def test_semantic_query_no_client(self) -> Dict[str, Any]:
        """Test semantic query without ChromaDB client."""
        router = self._get_router()
        result = router.query("test query", query_type="semantic")
        return {
            "error": result.error,
            "count": result.count
        }

    def test_inference_query_fallback(self) -> Dict[str, Any]:
        """Test inference query fallback."""
        router = self._get_router()
        result = router.query("What depends on RULE-001?", query_type="inference")
        return {
            "fallback_used": result.fallback_used
        }

    def test_health_check_no_connections(self) -> Dict[str, Any]:
        """Test health check with no connections."""
        router = self._get_router()
        health = router.health_check()
        return {
            "has_typedb": "typedb" in health,
            "has_chromadb": "chromadb" in health,
            "typedb_connected": health.get("typedb", {}).get("connected", False),
            "chromadb_connected": health.get("chromadb", {}).get("connected", False)
        }

    def test_sync_status_creation(self) -> Dict[str, Any]:
        """Test SyncStatus dataclass creation."""
        from governance.hybrid_router import SyncStatus
        status = SyncStatus(
            source="typedb",
            target="chromadb",
            synced_count=10,
            skipped_count=2,
            error_count=0
        )
        return {
            "source": status.source,
            "synced_count": status.synced_count,
            "errors_empty": len(status.errors) == 0
        }

    def test_memory_sync_bridge(self) -> Dict[str, Any]:
        """Test MemorySyncBridge functionality."""
        from governance.hybrid_router import HybridQueryRouter, MemorySyncBridge
        router = HybridQueryRouter()
        bridge = MemorySyncBridge(router)
        status = bridge.sync_rules_to_chromadb()
        return {
            "synced_count": status.synced_count,
            "has_error": "TypeDB client not connected" in status.errors
        }

    def test_sync_all(self) -> Dict[str, Any]:
        """Test sync_all returns dict with all entity types."""
        from governance.hybrid_router import HybridQueryRouter, MemorySyncBridge
        router = HybridQueryRouter()
        bridge = MemorySyncBridge(router)
        result = bridge.sync_all()
        return {
            "has_rules": "rules" in result,
            "has_decisions": "decisions" in result,
            "has_agents": "agents" in result
        }
