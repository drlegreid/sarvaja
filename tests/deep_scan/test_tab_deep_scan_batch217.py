"""Batch 217 — Session evidence + ingestion defense tests.

Validates fixes for:
- BUG-217-EVD-001: Duration parsing handles +00:00 timestamps
- BUG-217-EVD-002: Negative delta returns 'unknown'
- BUG-217-ING-001: Fallback pagination uses max(0,...) guard
"""
from pathlib import Path
from unittest.mock import patch, MagicMock

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-217-EVD-001: Duration parsing handles timezone formats ───────

class TestEvidenceDurationParsing:
    """compute_duration must handle both Z and +00:00 timestamps."""

    def test_duration_with_z_suffix(self):
        from governance.services.session_evidence import _compute_duration as compute_duration
        result = compute_duration(
            "2026-01-15T09:00:00Z",
            "2026-01-15T10:30:00Z",
        )
        assert result == "1h 30m"

    def test_duration_with_offset_suffix(self):
        """This was previously returning 'unknown' due to .replace('Z','')."""
        from governance.services.session_evidence import _compute_duration as compute_duration
        result = compute_duration(
            "2026-01-15T09:00:00+00:00",
            "2026-01-15T10:30:00+00:00",
        )
        assert result == "1h 30m"

    def test_duration_plain_iso(self):
        from governance.services.session_evidence import _compute_duration as compute_duration
        result = compute_duration(
            "2026-01-15T09:00:00",
            "2026-01-15T09:45:00",
        )
        assert result == "45m"

    def test_duration_unknown_on_none(self):
        from governance.services.session_evidence import _compute_duration as compute_duration
        assert compute_duration(None, None) == "unknown"
        assert compute_duration("", "") == "unknown"


# ── BUG-217-EVD-002: Negative delta guard ────────────────────────────

class TestEvidenceNegativeDuration:
    """Negative duration must return 'unknown', not nonsense string."""

    def test_negative_returns_unknown(self):
        from governance.services.session_evidence import _compute_duration as compute_duration
        result = compute_duration(
            "2026-01-15T10:00:00",
            "2026-01-15T09:00:00",  # end before start
        )
        assert result == "unknown"

    def test_negative_guard_in_source(self):
        src = (SRC / "governance/services/session_evidence.py").read_text()
        assert "total_seconds() < 0" in src


# ── BUG-217-ING-001: Fallback pagination guard ──────────────────────

class TestIngestionPaginationGuard:
    """Fallback path must use max(0,...) for page calculation."""

    def test_max_guard_in_source(self):
        """Source must use max(0, (page - 1) * per_page) in fallback path."""
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        # Count max(0 occurrences in get_session_detail
        import re
        matches = re.findall(r'max\(0,\s*\(page\s*-\s*1\)', src)
        assert len(matches) >= 2, \
            f"Expected 2+ max(0,...) guards in fallback, found {len(matches)}"


# ── Session evidence defense ─────────────────────────────────────────

class TestSessionEvidenceDefense:
    """Defense tests for session evidence module."""

    def test_compute_duration_callable(self):
        from governance.services.session_evidence import _compute_duration as compute_duration
        assert callable(compute_duration)

    def test_generate_session_evidence_callable(self):
        from governance.services.session_evidence import generate_session_evidence
        assert callable(generate_session_evidence)

    def test_render_evidence_markdown_callable(self):
        from governance.services.session_evidence import render_evidence_markdown
        assert callable(render_evidence_markdown)

    def test_compute_duration_short(self):
        from governance.services.session_evidence import _compute_duration as compute_duration
        result = compute_duration("2026-01-15T09:00:00", "2026-01-15T09:05:00")
        assert result == "5m"

    def test_compute_duration_multi_hour(self):
        from governance.services.session_evidence import _compute_duration as compute_duration
        result = compute_duration("2026-01-15T08:00:00", "2026-01-15T11:15:00")
        assert result == "3h 15m"


# ── CC session ingestion defense ─────────────────────────────────────

class TestIngestionDefense:
    """Defense tests for cc_session_ingestion module."""

    def test_ingest_session_callable(self):
        from governance.services.cc_session_ingestion import ingest_session
        assert callable(ingest_session)

    def test_ingest_all_callable(self):
        from governance.services.cc_session_ingestion import ingest_all
        assert callable(ingest_all)

    def test_get_session_detail_callable(self):
        from governance.services.cc_session_ingestion import get_session_detail
        assert callable(get_session_detail)


# ── Session repair defense ───────────────────────────────────────────

class TestSessionRepairDefense:
    """Defense tests for session repair module."""

    def test_parse_session_date_callable(self):
        from governance.services.session_repair import parse_session_date
        assert callable(parse_session_date)

    def test_parse_session_date_valid(self):
        from governance.services.session_repair import parse_session_date
        result = parse_session_date("SESSION-2026-02-15-MY-TOPIC")
        assert result == "2026-02-15"

    def test_parse_session_date_invalid(self):
        from governance.services.session_repair import parse_session_date
        result = parse_session_date("RANDOM-STRING")
        assert result is None

    def test_build_repair_plan_callable(self):
        from governance.services.session_repair import build_repair_plan
        assert callable(build_repair_plan)

    def test_generate_timestamps_callable(self):
        from governance.services.session_repair import generate_timestamps
        assert callable(generate_timestamps)

    def test_generate_timestamps_produces_iso(self):
        from governance.services.session_repair import generate_timestamps
        from datetime import datetime
        start, end = generate_timestamps("2026-02-15")
        # Should produce valid ISO timestamps
        datetime.fromisoformat(start)
        datetime.fromisoformat(end)
