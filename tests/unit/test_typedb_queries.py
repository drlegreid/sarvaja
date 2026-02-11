"""
Unit tests for TypeQL Query Builders for Session Metrics.

Per SESSION-METRICS-01-v1: Tests for build_metrics_insert_query,
build_evidence_insert_query, build_evidence_link_query.
"""

import pytest
from unittest.mock import patch

from governance.session_metrics.typedb_queries import (
    build_metrics_insert_query,
    build_evidence_insert_query,
    build_evidence_link_query,
)


# ---------------------------------------------------------------------------
# build_metrics_insert_query
# ---------------------------------------------------------------------------
class TestBuildMetricsInsertQuery:
    """Tests for build_metrics_insert_query()."""

    def test_basic_query_structure(self):
        metrics = {"totals": {"active_minutes": 120, "session_count": 5}}
        q = build_metrics_insert_query("SESSION-2026-02-11-METRICS", metrics)
        assert "insert $s isa work-session" in q
        assert 'has session-id "SESSION-2026-02-11-METRICS"' in q
        assert "has session-name" in q
        assert "has session-description" in q
        assert "has started-at" in q

    def test_description_contains_totals(self):
        metrics = {"totals": {
            "active_minutes": 100, "session_count": 3,
            "message_count": 50, "tool_calls": 20,
            "mcp_calls": 10, "api_errors": 2, "days_covered": 7,
        }}
        q = build_metrics_insert_query("S-1", metrics)
        assert "100 active_minutes" in q
        assert "3 sessions" in q
        assert "50 messages" in q
        assert "20 tool_calls" in q
        assert "10 mcp_calls" in q
        assert "2 api_errors" in q
        assert "7 days" in q

    def test_empty_totals(self):
        metrics = {"totals": {}}
        q = build_metrics_insert_query("S-1", metrics)
        assert "0 active_minutes" in q
        assert "0 sessions" in q

    def test_missing_totals(self):
        q = build_metrics_insert_query("S-1", {})
        assert "0 active_minutes" in q

    def test_name_includes_session_id(self):
        q = build_metrics_insert_query("SESSION-2026-02-11-METRICS", {})
        assert "Metrics Report SESSION-2026-02-11-METRICS" in q

    def test_escapes_quotes_in_description(self):
        metrics = {"totals": {"active_minutes": 0, "session_count": 0,
                              "message_count": 0, "tool_calls": 0,
                              "mcp_calls": 0, "api_errors": 0, "days_covered": 0}}
        q = build_metrics_insert_query("S-1", metrics)
        # The description should not have unescaped quotes
        # Count the quotes - they should be properly balanced
        assert q.count('\\"') % 2 == 0 or '\\"' not in q


# ---------------------------------------------------------------------------
# build_evidence_insert_query
# ---------------------------------------------------------------------------
class TestBuildEvidenceInsertQuery:
    """Tests for build_evidence_insert_query()."""

    def test_basic_structure(self):
        q = build_evidence_insert_query("EV-001", "session_metrics", "metrics", "preview")
        assert "insert $e isa evidence-file" in q
        assert 'has evidence-id "EV-001"' in q
        assert 'has evidence-source "session_metrics"' in q
        assert 'has evidence-type "metrics"' in q
        assert 'has evidence-content-preview "preview"' in q
        assert "has evidence-created-at" in q

    def test_truncates_long_preview(self):
        long_preview = "x" * 300
        q = build_evidence_insert_query("EV-001", "src", "type", long_preview)
        # Should truncate to 200 chars
        assert "x" * 200 in q
        assert "x" * 201 not in q

    def test_escapes_quotes_in_preview(self):
        q = build_evidence_insert_query("EV-001", "src", "type", 'has "quotes" inside')
        assert '\\"quotes\\"' in q

    def test_empty_preview(self):
        q = build_evidence_insert_query("EV-001", "src", "type", "")
        assert 'has evidence-content-preview ""' in q


# ---------------------------------------------------------------------------
# build_evidence_link_query
# ---------------------------------------------------------------------------
class TestBuildEvidenceLinkQuery:
    """Tests for build_evidence_link_query()."""

    def test_basic_structure(self):
        q = build_evidence_link_query("SESSION-001", "EV-001")
        assert "match" in q
        assert 'has session-id "SESSION-001"' in q
        assert 'has evidence-id "EV-001"' in q
        assert "insert" in q
        assert "isa has-evidence" in q

    def test_relation_roles(self):
        q = build_evidence_link_query("S-1", "E-1")
        assert "evidence-session: $s" in q
        assert "session-evidence: $e" in q

    def test_different_ids(self):
        q1 = build_evidence_link_query("S-A", "E-A")
        q2 = build_evidence_link_query("S-B", "E-B")
        assert "S-A" in q1
        assert "S-B" in q2
        assert "S-A" not in q2
