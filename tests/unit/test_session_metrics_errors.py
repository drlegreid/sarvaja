"""
TDD Test Spec: Session Metrics Error/Retry Tracking
=====================================================
Per GAP-SESSION-METRICS-ERRORS: API error/retry tracking
(isApiErrorMessage detection).

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_session_metrics_errors.py -v
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures: synthetic JSONL with error entries
# ---------------------------------------------------------------------------

@pytest.fixture
def error_log_dir(tmp_path):
    """Log with normal + error + retry entries."""
    entries = [
        # Normal request
        {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
         "sessionId": "sess-001",
         "message": {"role": "user", "content": "hello"}},
        {"type": "assistant", "timestamp": "2026-01-28T10:01:00Z",
         "sessionId": "sess-001",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [{"type": "text", "text": "hi"}]}},
        # API error (500)
        {"type": "assistant", "timestamp": "2026-01-28T10:02:00Z",
         "sessionId": "sess-001",
         "isApiErrorMessage": True,
         "message": {"role": "assistant",
                     "content": "Internal server error (500)"}},
        # Retry succeeds
        {"type": "assistant", "timestamp": "2026-01-28T10:02:30Z",
         "sessionId": "sess-001",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [{"type": "text", "text": "retry succeeded"}]}},
        # Another API error (overloaded)
        {"type": "assistant", "timestamp": "2026-01-28T10:05:00Z",
         "sessionId": "sess-001",
         "isApiErrorMessage": True,
         "message": {"role": "assistant",
                     "content": "Overloaded (529)"}},
        # Normal continued
        {"type": "user", "timestamp": "2026-01-28T10:06:00Z",
         "sessionId": "sess-001",
         "message": {"role": "user", "content": "continue"}},
    ]
    log_file = tmp_path / "error-test.jsonl"
    with open(log_file, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return tmp_path, log_file


# ---------------------------------------------------------------------------
# Tests: Error detection in parser
# ---------------------------------------------------------------------------

class TestErrorDetection:
    """Test that parser detects API error entries."""

    def test_parse_detects_api_errors(self, error_log_dir):
        """Parser identifies entries with isApiErrorMessage=true."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = error_log_dir
        entries = list(parse_log_file(log_file))
        errors = [e for e in entries if e.is_api_error]
        assert len(errors) == 2

    def test_non_error_entries_not_flagged(self, error_log_dir):
        """Normal entries have is_api_error=False."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = error_log_dir
        entries = list(parse_log_file(log_file))
        normal = [e for e in entries if not e.is_api_error]
        assert len(normal) == 4


# ---------------------------------------------------------------------------
# Tests: Error metrics in calculator
# ---------------------------------------------------------------------------

class TestErrorMetrics:
    """Test error counting in calculator output."""

    def test_totals_include_error_count(self, error_log_dir):
        """Calculate metrics includes api_errors in totals."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        _, log_file = error_log_dir
        entries = list(parse_log_file(log_file))
        metrics = calculate_metrics(entries)
        assert metrics.totals.api_errors == 2

    def test_day_metrics_include_errors(self, error_log_dir):
        """Per-day metrics include api_errors count."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        _, log_file = error_log_dir
        entries = list(parse_log_file(log_file))
        metrics = calculate_metrics(entries)
        day = metrics.days[0]
        assert day.api_errors == 2

    def test_error_rate_calculation(self, error_log_dir):
        """Totals include error_rate (errors/total messages)."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        _, log_file = error_log_dir
        entries = list(parse_log_file(log_file))
        metrics = calculate_metrics(entries)
        result = metrics.to_dict()
        # 2 errors / 6 messages = 0.33
        assert 0.3 <= result["totals"]["error_rate"] <= 0.4

    def test_zero_errors_zero_rate(self, tmp_path):
        """No errors produces error_rate=0."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        log_file = tmp_path / "no-errors.jsonl"
        entries_data = [
            {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
             "sessionId": "s1",
             "message": {"role": "user", "content": "hi"}},
            {"type": "assistant", "timestamp": "2026-01-28T10:01:00Z",
             "sessionId": "s1",
             "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                         "content": [{"type": "text", "text": "hello"}]}},
        ]
        with open(log_file, "w") as f:
            for e in entries_data:
                f.write(json.dumps(e) + "\n")
        entries = list(parse_log_file(log_file))
        metrics = calculate_metrics(entries)
        assert metrics.totals.api_errors == 0
        assert metrics.to_dict()["totals"]["error_rate"] == 0.0

    def test_error_serializable(self, error_log_dir):
        """Error metrics are JSON-serializable."""
        from governance.session_metrics.parser import parse_log_file
        from governance.session_metrics.calculator import calculate_metrics
        _, log_file = error_log_dir
        entries = list(parse_log_file(log_file))
        metrics = calculate_metrics(entries)
        result = metrics.to_dict()
        json.dumps(result)  # Should not raise
        assert "api_errors" in result["totals"]
