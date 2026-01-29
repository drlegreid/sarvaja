"""
TDD Test Spec: Session Metrics Platform Integration
====================================================
Per GAP-SESSION-METRICS-PLATFORM: TypeDB queries + evidence generation.

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_session_metrics_platform.py -v
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_metrics_dict():
    """A realistic MetricsResult.to_dict() output."""
    return {
        "days": [
            {
                "date": "2026-01-28",
                "active_minutes": 120,
                "wall_clock_minutes": 180,
                "session_count": 3,
                "message_count": 45,
                "tool_calls": 89,
                "mcp_calls": 12,
                "compactions": 2,
                "api_errors": 1,
            },
            {
                "date": "2026-01-29",
                "active_minutes": 95,
                "wall_clock_minutes": 140,
                "session_count": 2,
                "message_count": 30,
                "tool_calls": 55,
                "mcp_calls": 8,
                "compactions": 1,
                "api_errors": 0,
            },
        ],
        "totals": {
            "active_minutes": 215,
            "session_count": 5,
            "message_count": 75,
            "tool_calls": 144,
            "mcp_calls": 20,
            "thinking_chars": 50000,
            "days_covered": 2,
            "api_errors": 1,
            "error_rate": 0.01,
        },
        "tool_breakdown": {
            "Read": 40,
            "Edit": 25,
            "Bash": 30,
            "mcp__gov-core__health_check": 12,
        },
    }


@pytest.fixture
def evidence_dir(tmp_path):
    """Temp directory for evidence output."""
    edir = tmp_path / "evidence"
    edir.mkdir()
    return edir


# ---------------------------------------------------------------------------
# Tests: Evidence Generation
# ---------------------------------------------------------------------------

class TestEvidenceGeneration:
    """Test evidence markdown generation from metrics."""

    def test_generate_returns_string(self, sample_metrics_dict):
        """generate_evidence_markdown returns a non-empty string."""
        from governance.session_metrics.evidence import generate_evidence_markdown
        md = generate_evidence_markdown(sample_metrics_dict)
        assert isinstance(md, str)
        assert len(md) > 0

    def test_evidence_has_title(self, sample_metrics_dict):
        """Evidence contains a markdown title."""
        from governance.session_metrics.evidence import generate_evidence_markdown
        md = generate_evidence_markdown(sample_metrics_dict)
        assert md.startswith("# ")

    def test_evidence_has_totals_section(self, sample_metrics_dict):
        """Evidence contains totals summary."""
        from governance.session_metrics.evidence import generate_evidence_markdown
        md = generate_evidence_markdown(sample_metrics_dict)
        assert "active_minutes" in md or "Active Minutes" in md
        assert "215" in md  # total active_minutes

    def test_evidence_has_per_day_table(self, sample_metrics_dict):
        """Evidence contains per-day breakdown table."""
        from governance.session_metrics.evidence import generate_evidence_markdown
        md = generate_evidence_markdown(sample_metrics_dict)
        assert "2026-01-28" in md
        assert "2026-01-29" in md

    def test_evidence_has_tool_breakdown(self, sample_metrics_dict):
        """Evidence contains tool usage breakdown."""
        from governance.session_metrics.evidence import generate_evidence_markdown
        md = generate_evidence_markdown(sample_metrics_dict)
        assert "Read" in md
        assert "Edit" in md

    def test_evidence_has_error_rate(self, sample_metrics_dict):
        """Evidence includes error rate information."""
        from governance.session_metrics.evidence import generate_evidence_markdown
        md = generate_evidence_markdown(sample_metrics_dict)
        assert "error" in md.lower()

    def test_evidence_has_rule_reference(self, sample_metrics_dict):
        """Evidence references SESSION-METRICS-01-v1."""
        from governance.session_metrics.evidence import generate_evidence_markdown
        md = generate_evidence_markdown(sample_metrics_dict)
        assert "SESSION-METRICS-01-v1" in md

    def test_evidence_empty_metrics(self):
        """Empty metrics produces minimal valid evidence."""
        from governance.session_metrics.evidence import generate_evidence_markdown
        empty = {
            "days": [],
            "totals": {
                "active_minutes": 0,
                "session_count": 0,
                "message_count": 0,
                "tool_calls": 0,
                "mcp_calls": 0,
                "thinking_chars": 0,
                "days_covered": 0,
                "api_errors": 0,
                "error_rate": 0.0,
            },
            "tool_breakdown": {},
        }
        md = generate_evidence_markdown(empty)
        assert isinstance(md, str)
        assert "# " in md


class TestEvidenceFileWrite:
    """Test writing evidence to file."""

    def test_write_evidence_creates_file(self, sample_metrics_dict, evidence_dir):
        """write_evidence_file creates a markdown file."""
        from governance.session_metrics.evidence import write_evidence_file
        path = write_evidence_file(
            sample_metrics_dict,
            output_dir=evidence_dir,
        )
        assert path.exists()
        assert path.suffix == ".md"

    def test_evidence_filename_pattern(self, sample_metrics_dict, evidence_dir):
        """Evidence filename follows SESSION-YYYY-MM-DD-METRICS pattern."""
        from governance.session_metrics.evidence import write_evidence_file
        path = write_evidence_file(
            sample_metrics_dict,
            output_dir=evidence_dir,
        )
        assert path.name.startswith("SESSION-")
        assert "METRICS" in path.name

    def test_evidence_file_content_valid(self, sample_metrics_dict, evidence_dir):
        """Written evidence file has valid markdown content."""
        from governance.session_metrics.evidence import write_evidence_file
        path = write_evidence_file(
            sample_metrics_dict,
            output_dir=evidence_dir,
        )
        content = path.read_text()
        assert content.startswith("# ")
        assert "215" in content  # total active_minutes


# ---------------------------------------------------------------------------
# Tests: TypeDB Query Builder
# ---------------------------------------------------------------------------

class TestTypeDBQueryBuilder:
    """Test TypeQL query generation for session metrics."""

    def test_build_insert_query_returns_string(self, sample_metrics_dict):
        """build_metrics_insert_query returns a TypeQL string."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        query = build_metrics_insert_query(
            session_id="SESSION-2026-01-29-METRICS",
            metrics=sample_metrics_dict,
        )
        assert isinstance(query, str)
        assert "insert" in query

    def test_insert_query_has_entity_type(self, sample_metrics_dict):
        """Insert query creates a session-metrics entity."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        query = build_metrics_insert_query(
            session_id="SESSION-2026-01-29-METRICS",
            metrics=sample_metrics_dict,
        )
        assert "isa work-session" in query

    def test_insert_query_has_session_id(self, sample_metrics_dict):
        """Insert query includes session-id attribute."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        query = build_metrics_insert_query(
            session_id="SESSION-2026-01-29-METRICS",
            metrics=sample_metrics_dict,
        )
        assert "SESSION-2026-01-29-METRICS" in query

    def test_insert_query_has_description(self, sample_metrics_dict):
        """Insert query includes metrics summary in description."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        query = build_metrics_insert_query(
            session_id="SESSION-2026-01-29-METRICS",
            metrics=sample_metrics_dict,
        )
        assert "session-description" in query
        assert "215" in query  # active_minutes in description

    def test_insert_query_has_name(self, sample_metrics_dict):
        """Insert query includes session-name."""
        from governance.session_metrics.typedb_queries import build_metrics_insert_query
        query = build_metrics_insert_query(
            session_id="SESSION-2026-01-29-METRICS",
            metrics=sample_metrics_dict,
        )
        assert "session-name" in query

    def test_build_evidence_link_query(self, sample_metrics_dict):
        """build_evidence_link_query creates a has-evidence relation."""
        from governance.session_metrics.typedb_queries import build_evidence_link_query
        query = build_evidence_link_query(
            session_id="SESSION-2026-01-29-METRICS",
            evidence_id="EVIDENCE-METRICS-2026-01-29",
        )
        assert "has-evidence" in query
        assert "SESSION-2026-01-29-METRICS" in query
        assert "EVIDENCE-METRICS-2026-01-29" in query

    def test_build_evidence_insert_query(self, sample_metrics_dict):
        """build_evidence_insert_query creates an evidence-file entity."""
        from governance.session_metrics.typedb_queries import build_evidence_insert_query
        query = build_evidence_insert_query(
            evidence_id="EVIDENCE-METRICS-2026-01-29",
            source="session_metrics",
            evidence_type="metrics",
            content_preview="Active: 215min, Sessions: 5",
        )
        assert "evidence-file" in query
        assert "EVIDENCE-METRICS-2026-01-29" in query
        assert "session_metrics" in query
