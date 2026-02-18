"""Deep scan batch 183: Session metrics layer.

Batch 183 findings: 20 total, 1 confirmed fix, 19 rejected/deferred.
- BUG-183-007: Negative latency_ms from out-of-order JSONL entries.
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta


# ── Correlation latency defense ──────────────


class TestCorrelationLatencyDefense:
    """Verify correlation.py guards against negative latency."""

    def test_latency_uses_max_zero(self):
        """correlate_tool_calls uses max(0, ...) for latency."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/session_metrics/correlation.py").read_text()
        assert "max(0," in src

    def test_no_dead_code_loop(self):
        """correlation.py has no dead code loop with pass body."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/session_metrics/correlation.py").read_text()
        # Previous BUG-CORR-DEAD-CODE-001 removed the dead loop
        lines = src.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "pass" and i > 0:
                prev = lines[i - 1].strip()
                if prev.startswith("for "):
                    assert False, f"Dead loop at line {i+1}"


# ── Parser timezone defense ──────────────


class TestParserTimezoneDefense:
    """Verify parser handles timestamps."""

    def test_parse_timestamp_function_exists(self):
        """_parse_timestamp function exists in parser.py."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/session_metrics/parser.py").read_text()
        assert "def _parse_timestamp" in src

    def test_parse_log_file_exists(self):
        """parse_log_file function exists."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/session_metrics/parser.py").read_text()
        assert "def parse_log_file" in src


# ── Calculator defense ──────────────


class TestCalculatorDefense:
    """Verify calculator functions handle edge cases."""

    def test_filter_entries_by_days_exists(self):
        """filter_entries_by_days function exists."""
        from governance.session_metrics.calculator import filter_entries_by_days
        assert callable(filter_entries_by_days)

    def test_split_sessions_exists(self):
        """split_sessions function exists."""
        from governance.session_metrics.calculator import split_sessions
        assert callable(split_sessions)

    def test_split_sessions_empty_list(self):
        """split_sessions returns [] for empty input."""
        from governance.session_metrics.calculator import split_sessions
        result = split_sessions([])
        assert result == []


# ── Temporal defense ──────────────


class TestTemporalDefense:
    """Verify temporal query functions."""

    def test_temporal_module_importable(self):
        """temporal module is importable."""
        from governance.session_metrics import temporal
        assert temporal is not None

    def test_query_at_time_exists(self):
        """query_at_time function exists."""
        from governance.session_metrics.temporal import query_at_time
        assert callable(query_at_time)


# ── Session scanner defense ──────────────


class TestSessionScannerDefense:
    """Verify CC session scanner structure."""

    def test_discover_cc_projects_importable(self):
        """discover_cc_projects is importable."""
        from governance.services.cc_session_scanner import discover_cc_projects
        assert callable(discover_cc_projects)

    def test_scan_jsonl_metadata_importable(self):
        """scan_jsonl_metadata is importable."""
        from governance.services.cc_session_scanner import scan_jsonl_metadata
        assert callable(scan_jsonl_metadata)

    def test_derive_project_slug_importable(self):
        """derive_project_slug is importable."""
        from governance.services.cc_session_scanner import derive_project_slug
        assert callable(derive_project_slug)


# ── Session repair defense ──────────────


class TestSessionRepairDefense:
    """Verify session repair module."""

    def test_parse_session_date_importable(self):
        """parse_session_date is importable."""
        from governance.services.session_repair import parse_session_date
        assert callable(parse_session_date)

    def test_parse_session_date_valid(self):
        """parse_session_date extracts date from session ID."""
        from governance.services.session_repair import parse_session_date
        result = parse_session_date("SESSION-2026-01-15-TOPIC")
        assert result == "2026-01-15"

    def test_parse_session_date_invalid(self):
        """parse_session_date returns None for invalid session IDs."""
        from governance.services.session_repair import parse_session_date
        result = parse_session_date("INVALID-ID")
        assert result is None
