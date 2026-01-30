"""
Tests for hybrid router data models.

Per RULE-004, GAP-FILE-012: Query routing models.
Covers QueryType, QueryResult, SyncStatus.

Created: 2026-01-30
"""

import pytest

from governance.hybrid.models import QueryType, QueryResult, SyncStatus


class TestQueryType:
    """Test QueryType enum."""

    def test_values(self):
        assert QueryType.INFERENCE.value == "inference"
        assert QueryType.SEMANTIC.value == "semantic"
        assert QueryType.COMBINED.value == "combined"
        assert QueryType.AUTO.value == "auto"

    def test_all_members(self):
        assert len(QueryType) == 4


class TestQueryResult:
    """Test QueryResult dataclass."""

    def test_minimal(self):
        r = QueryResult(
            query="test query", query_type=QueryType.SEMANTIC,
            source="chromadb", results=[], count=0, latency_ms=5.0
        )
        assert r.query == "test query"
        assert r.fallback_used is False
        assert r.error is None

    def test_with_results(self):
        r = QueryResult(
            query="depends on RULE-001", query_type=QueryType.INFERENCE,
            source="typedb", results=[{"type": "dependency", "rule_id": "RULE-002"}],
            count=1, latency_ms=12.5
        )
        assert r.count == 1
        assert r.results[0]["rule_id"] == "RULE-002"

    def test_with_fallback(self):
        r = QueryResult(
            query="q", query_type=QueryType.INFERENCE,
            source="chromadb", results=[], count=0,
            latency_ms=50.0, fallback_used=True,
            error="TypeDB error: timeout. Fell back to ChromaDB."
        )
        assert r.fallback_used is True
        assert "timeout" in r.error

    def test_combined_results(self):
        r = QueryResult(
            query="q", query_type=QueryType.COMBINED,
            source="both", results=[{"typedb": [], "chromadb": []}],
            count=0, latency_ms=25.0
        )
        assert r.source == "both"

    def test_error_result(self):
        r = QueryResult(
            query="bad", query_type=QueryType.AUTO,
            source="error", results=[], count=0,
            latency_ms=1.0, error="Connection refused"
        )
        assert r.source == "error"
        assert r.error == "Connection refused"


class TestSyncStatus:
    """Test SyncStatus dataclass."""

    def test_minimal(self):
        s = SyncStatus(source="typedb", target="chromadb",
                      synced_count=10, skipped_count=2, error_count=0)
        assert s.errors == []
        assert s.last_sync is None

    def test_with_errors(self):
        s = SyncStatus(
            source="gaps", target="typedb",
            synced_count=5, skipped_count=0, error_count=2,
            errors=["Failed GAP-001", "Failed GAP-002"]
        )
        assert len(s.errors) == 2
        assert s.error_count == 2

    def test_with_last_sync(self):
        s = SyncStatus(
            source="a", target="b",
            synced_count=0, skipped_count=0, error_count=0,
            last_sync="2026-01-30T10:00:00"
        )
        assert s.last_sync == "2026-01-30T10:00:00"

    def test_post_init_none_errors(self):
        """Verify __post_init__ converts None errors to empty list."""
        s = SyncStatus(source="a", target="b",
                      synced_count=0, skipped_count=0, error_count=0,
                      errors=None)
        assert s.errors == []
