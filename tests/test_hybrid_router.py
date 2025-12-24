"""
Integration Tests for Hybrid Query Router
Per RULE-004: Executable Specification / TDD

Tests the routing logic between TypeDB (inference) and ChromaDB (semantic).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from governance.hybrid_router import (
    HybridQueryRouter,
    QueryResult,
    QueryType,
    MemorySyncBridge
)


class TestQueryTypeDetection:
    """Test automatic query type detection."""

    def test_inference_query_depends_on(self):
        """Inference: 'depends on' keyword."""
        router = HybridQueryRouter()
        detected = router._detect_query_type("What depends on RULE-001?")
        assert detected == "inference"

    def test_inference_query_conflicts(self):
        """Inference: 'conflicts' keyword."""
        router = HybridQueryRouter()
        detected = router._detect_query_type("Show conflicts between RULE-001 and RULE-002")
        assert detected == "inference"

    def test_inference_query_rule_id(self):
        """Inference: RULE-XXX pattern adds weight."""
        router = HybridQueryRouter()
        detected = router._detect_query_type("Show me RULE-012")
        assert detected == "inference"

    def test_semantic_query_about(self):
        """Semantic: 'about' keyword."""
        router = HybridQueryRouter()
        detected = router._detect_query_type("Tell me about authentication")
        assert detected == "semantic"

    def test_semantic_query_find(self):
        """Semantic: 'find' keyword."""
        router = HybridQueryRouter()
        detected = router._detect_query_type("Find documents about security")
        assert detected == "semantic"

    def test_semantic_query_what_is(self):
        """Semantic: 'what is' + question mark."""
        router = HybridQueryRouter()
        detected = router._detect_query_type("What is the best practice for logging?")
        assert detected == "semantic"

    def test_mixed_query_defaults_to_semantic(self):
        """Ambiguous query defaults to semantic."""
        router = HybridQueryRouter()
        detected = router._detect_query_type("stuff")
        assert detected == "semantic"


class TestRuleIdExtraction:
    """Test RULE-XXX and DECISION-XXX extraction."""

    def test_extract_rule_id(self):
        """Extract RULE-XXX from text."""
        router = HybridQueryRouter()
        assert router._extract_rule_id("What depends on RULE-001?") == "RULE-001"
        assert router._extract_rule_id("See RULE-012 for details") == "RULE-012"
        assert router._extract_rule_id("No rule here") is None

    def test_extract_decision_id(self):
        """Extract DECISION-XXX from text."""
        router = HybridQueryRouter()
        assert router._extract_decision_id("Per DECISION-001") == "DECISION-001"
        assert router._extract_decision_id("No decision here") is None


class TestQueryResultDataclass:
    """Test QueryResult dataclass."""

    def test_query_result_creation(self):
        """QueryResult with all fields."""
        result = QueryResult(
            query="test query",
            query_type=QueryType.SEMANTIC,
            source="chromadb",
            results=[{"doc": "test"}],
            count=1,
            latency_ms=10.5
        )
        assert result.query == "test query"
        assert result.query_type == QueryType.SEMANTIC
        assert result.source == "chromadb"
        assert result.count == 1
        assert result.fallback_used is False
        assert result.error is None

    def test_query_result_with_error(self):
        """QueryResult with error."""
        result = QueryResult(
            query="failed query",
            query_type=QueryType.INFERENCE,
            source="error",
            results=[],
            count=0,
            latency_ms=50.0,
            error="Connection failed"
        )
        assert result.error == "Connection failed"
        assert result.count == 0


class TestRouterConnection:
    """Test connection management."""

    def test_default_config(self):
        """Default configuration from environment."""
        router = HybridQueryRouter()
        assert router.typedb_host == "localhost"
        assert router.typedb_port == 1729
        assert router.chromadb_host == "localhost"
        assert router.chromadb_port == 8001
        assert router.timeout_ms == 5000

    def test_custom_config(self):
        """Custom configuration override."""
        router = HybridQueryRouter(
            typedb_host="typedb.local",
            typedb_port=1730,
            chromadb_host="chroma.local",
            chromadb_port=8002,
            timeout_ms=10000
        )
        assert router.typedb_host == "typedb.local"
        assert router.typedb_port == 1730
        assert router.chromadb_host == "chroma.local"
        assert router.chromadb_port == 8002


class TestSemanticQuery:
    """Test semantic (ChromaDB) queries."""

    def test_semantic_query_no_client(self):
        """Semantic query without ChromaDB client returns error."""
        router = HybridQueryRouter()
        result = router.query("test query", query_type="semantic")
        assert result.error == "ChromaDB not connected"
        assert result.count == 0

    @patch('chromadb.HttpClient')
    def test_semantic_query_with_mock_client(self, mock_http_client):
        """Semantic query with mocked ChromaDB."""
        # Setup mock
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"key": "val1"}, {"key": "val2"}]],
            "distances": [[0.1, 0.2]]
        }
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        mock_http_client.return_value = mock_client

        router = HybridQueryRouter()
        router._chromadb_client = mock_client

        result = router.query("test query", query_type="semantic")

        assert result.source == "chromadb"
        assert result.count == 2
        assert result.error is None


class TestInferenceQuery:
    """Test inference (TypeDB) queries."""

    def test_inference_query_no_client_fallback(self):
        """Inference query without TypeDB falls back to ChromaDB."""
        router = HybridQueryRouter()
        result = router.query("What depends on RULE-001?", query_type="inference")
        # Falls back to ChromaDB, which is also not connected
        assert result.fallback_used is True


class TestHealthCheck:
    """Test health check functionality."""

    def test_health_check_no_connections(self):
        """Health check with no active connections."""
        router = HybridQueryRouter()
        health = router.health_check()
        assert "typedb" in health
        assert "chromadb" in health
        assert health["typedb"]["connected"] is False
        assert health["chromadb"]["connected"] is False


class TestMemorySyncBridge:
    """Test MemorySyncBridge functionality."""

    def test_sync_no_typedb_client(self):
        """Sync returns 0 when TypeDB not connected."""
        router = HybridQueryRouter()
        bridge = MemorySyncBridge(router)
        count = bridge.sync_rules_to_chromadb()
        assert count == 0

    def test_sync_no_chromadb_client(self):
        """Sync returns 0 when ChromaDB not connected."""
        router = HybridQueryRouter()
        router._typedb_client = MagicMock()
        router._typedb_client.get_all_rules.return_value = []
        bridge = MemorySyncBridge(router)
        count = bridge.sync_rules_to_chromadb()
        assert count == 0


# =============================================================================
# INTEGRATION TESTS (Require running services)
# =============================================================================

@pytest.mark.integration
@pytest.mark.skipif(True, reason="Requires TypeDB + ChromaDB services")
class TestIntegrationRouter:
    """Integration tests requiring running services."""

    def test_full_connection(self):
        """Test full connection to both backends."""
        router = HybridQueryRouter()
        status = router.connect()
        assert status["typedb"] is True or status["chromadb"] is True
        router.close()

    def test_real_semantic_query(self):
        """Real semantic query against ChromaDB."""
        router = HybridQueryRouter()
        router.connect()
        result = router.query("governance rules", query_type="semantic")
        assert result.source == "chromadb"
        router.close()

    def test_real_inference_query(self):
        """Real inference query against TypeDB."""
        router = HybridQueryRouter()
        router.connect()
        result = router.query("What depends on RULE-001?", query_type="inference")
        assert result.source in ["typedb", "chromadb"]  # May fallback
        router.close()


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
