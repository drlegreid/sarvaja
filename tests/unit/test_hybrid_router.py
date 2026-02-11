"""
Unit tests for Hybrid Query Router.

Per RULE-004, RULE-010: Tests for HybridQueryRouter query type detection,
routing logic, and helper methods using mock backends.
"""

import pytest
from unittest.mock import MagicMock, patch

from governance.hybrid.models import QueryType, QueryResult, SyncStatus


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class TestQueryType:
    """Tests for QueryType enum."""

    def test_values(self):
        assert QueryType.INFERENCE.value == "inference"
        assert QueryType.SEMANTIC.value == "semantic"
        assert QueryType.COMBINED.value == "combined"
        assert QueryType.AUTO.value == "auto"


class TestQueryResult:
    """Tests for QueryResult dataclass."""

    def test_basic(self):
        qr = QueryResult(
            query="test", query_type=QueryType.INFERENCE,
            source="typedb", results=[{"a": 1}], count=1, latency_ms=5.0,
        )
        assert qr.fallback_used is False
        assert qr.error is None

    def test_with_error(self):
        qr = QueryResult(
            query="test", query_type=QueryType.SEMANTIC,
            source="chromadb", results=[], count=0, latency_ms=0.0,
            error="connection refused",
        )
        assert qr.error == "connection refused"


class TestSyncStatus:
    """Tests for SyncStatus dataclass."""

    def test_default_errors(self):
        ss = SyncStatus(source="typedb", target="chromadb",
                        synced_count=5, skipped_count=1, error_count=0)
        assert ss.errors == []

    def test_with_errors(self):
        ss = SyncStatus(source="a", target="b", synced_count=0,
                        skipped_count=0, error_count=1, errors=["fail"])
        assert ss.errors == ["fail"]


# ---------------------------------------------------------------------------
# HybridQueryRouter
# ---------------------------------------------------------------------------
class TestHybridQueryRouter:
    """Tests for HybridQueryRouter class."""

    def _make_router(self):
        """Create router with mocked clients."""
        from governance.hybrid.router import HybridQueryRouter
        router = HybridQueryRouter.__new__(HybridQueryRouter)
        router.typedb_host = "localhost"
        router.typedb_port = 1729
        router.chromadb_host = "localhost"
        router.chromadb_port = 8001
        router.timeout_ms = 5000
        router._typedb_client = None
        router._chromadb_client = None
        return router

    # -- _detect_query_type --
    def test_detect_inference_keywords(self):
        router = self._make_router()
        assert router._detect_query_type("what depends on RULE-001?") == "inference"

    def test_detect_semantic_keywords(self):
        router = self._make_router()
        assert router._detect_query_type("what is authentication?") == "semantic"

    def test_detect_rule_id_boosts_inference(self):
        router = self._make_router()
        assert router._detect_query_type("RULE-001") == "inference"

    def test_detect_decision_id_boosts_inference(self):
        router = self._make_router()
        assert router._detect_query_type("DECISION-003") == "inference"

    def test_detect_default_semantic(self):
        router = self._make_router()
        # No keywords at all — defaults to semantic
        assert router._detect_query_type("hello world") == "semantic"

    def test_detect_question_boosts_semantic(self):
        router = self._make_router()
        result = router._detect_query_type("what is this?")
        assert result == "semantic"

    # -- _extract_rule_id --
    def test_extract_rule_id(self):
        router = self._make_router()
        assert router._extract_rule_id("Show RULE-001 details") == "RULE-001"

    def test_extract_rule_id_none(self):
        router = self._make_router()
        assert router._extract_rule_id("no rule here") is None

    def test_extract_rule_id_multiple(self):
        router = self._make_router()
        # Returns first match
        assert router._extract_rule_id("RULE-001 and RULE-002") == "RULE-001"

    # -- _extract_decision_id --
    def test_extract_decision_id(self):
        router = self._make_router()
        assert router._extract_decision_id("DECISION-003") == "DECISION-003"

    def test_extract_decision_id_none(self):
        router = self._make_router()
        assert router._extract_decision_id("no decision") is None

    # -- query with no backends --
    def test_query_chromadb_not_connected(self):
        router = self._make_router()
        result = router.query("test query", query_type="semantic")
        assert isinstance(result, QueryResult)
        assert result.error == "ChromaDB not connected"
        assert result.count == 0

    def test_query_inference_fallback_to_chromadb(self):
        router = self._make_router()
        # TypeDB not connected, should fall back to chromadb (which also not connected)
        result = router.query("depends on RULE-001", query_type="inference")
        assert isinstance(result, QueryResult)
        assert result.fallback_used is True

    def test_query_auto_routes(self):
        router = self._make_router()
        # Auto detection should route to inference for RULE-XXX
        result = router.query("RULE-001", query_type="auto")
        assert isinstance(result, QueryResult)

    def test_query_error_handling(self):
        router = self._make_router()
        # Combined with no backends — should return without crash
        result = router.query("test", query_type="combined")
        assert isinstance(result, QueryResult)

    # -- health_check --
    @patch("governance.hybrid.router.quick_health", return_value=False)
    def test_health_check_no_backends(self, mock_health):
        router = self._make_router()
        health = router.health_check()
        assert health["typedb"]["connected"] is False
        assert health["chromadb"]["connected"] is False

    # -- close --
    def test_close_with_client(self):
        router = self._make_router()
        mock_client = MagicMock()
        router._typedb_client = mock_client
        router.close()
        mock_client.close.assert_called_once()

    def test_close_without_client(self):
        router = self._make_router()
        router.close()  # Should not raise
