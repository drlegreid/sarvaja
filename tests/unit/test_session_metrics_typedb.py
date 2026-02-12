"""
Unit tests for Session Metrics TypeDB Query Builders.

Per DOC-SIZE-01-v1: Tests for governance/session_metrics/typedb_queries.py.
Tests: build_metrics_insert_query, build_evidence_insert_query,
       build_evidence_link_query.
"""

from governance.session_metrics.typedb_queries import (
    build_metrics_insert_query,
    build_evidence_insert_query,
    build_evidence_link_query,
)


# ── build_metrics_insert_query ─────────────────────────


class TestBuildMetricsInsertQuery:
    def test_basic_query(self):
        metrics = {
            "totals": {
                "active_minutes": 60,
                "session_count": 3,
                "message_count": 20,
                "tool_calls": 50,
                "mcp_calls": 10,
                "api_errors": 0,
                "days_covered": 2,
            }
        }
        result = build_metrics_insert_query("SESSION-2026-02-11-METRICS", metrics)
        assert 'isa work-session' in result
        assert 'has session-id "SESSION-2026-02-11-METRICS"' in result
        assert 'has session-name "Metrics Report SESSION-2026-02-11-METRICS"' in result
        assert '60 active_minutes' in result
        assert '3 sessions' in result

    def test_empty_totals(self):
        result = build_metrics_insert_query("S-1", {})
        assert 'has session-id "S-1"' in result
        assert '0 active_minutes' in result

    def test_description_escaping(self):
        metrics = {"totals": {"active_minutes": 0, "session_count": 0,
                              "message_count": 0, "tool_calls": 0,
                              "mcp_calls": 0, "api_errors": 0, "days_covered": 0}}
        result = build_metrics_insert_query("S-1", metrics)
        assert '\\"' not in result  # No quotes in the metrics description

    def test_has_started_at(self):
        result = build_metrics_insert_query("S-1", {})
        assert 'has started-at' in result


# ── build_evidence_insert_query ────────────────────────


class TestBuildEvidenceInsertQuery:
    def test_basic_query(self):
        result = build_evidence_insert_query(
            "EV-001", "session_metrics", "metrics", "Session report content...")
        assert 'isa evidence-file' in result
        assert 'has evidence-id "EV-001"' in result
        assert 'has evidence-source "session_metrics"' in result
        assert 'has evidence-type "metrics"' in result
        assert 'Session report content' in result

    def test_truncates_preview(self):
        long_content = "x" * 500
        result = build_evidence_insert_query("E-1", "src", "type", long_content)
        # Preview should be truncated to 200 chars
        assert 'x' * 200 in result
        assert 'x' * 201 not in result

    def test_escapes_quotes(self):
        result = build_evidence_insert_query(
            "E-1", "src", "type", 'contains "quotes" here')
        assert '\\"quotes\\"' in result

    def test_has_created_at(self):
        result = build_evidence_insert_query("E-1", "src", "type", "content")
        assert 'has evidence-created-at' in result


# ── build_evidence_link_query ──────────────────────────


class TestBuildEvidenceLinkQuery:
    def test_basic_query(self):
        result = build_evidence_link_query("S-1", "E-1")
        assert 'match' in result
        assert 'has session-id "S-1"' in result
        assert 'has evidence-id "E-1"' in result
        assert 'isa has-evidence' in result

    def test_includes_roles(self):
        result = build_evidence_link_query("S-1", "E-1")
        assert 'evidence-session: $s' in result
        assert 'session-evidence: $e' in result

    def test_insert_keyword(self):
        result = build_evidence_link_query("S-1", "E-1")
        assert 'insert' in result
