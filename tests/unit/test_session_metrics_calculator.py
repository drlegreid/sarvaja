"""
Unit tests for Session Metrics Calculator.

Per DOC-SIZE-01-v1: Tests for session_metrics/calculator.py module.
Tests: filter_entries_by_days(), split_sessions(), calculate_metrics().
"""

from datetime import datetime, timedelta

from governance.session_metrics.calculator import (
    filter_entries_by_days,
    split_sessions,
    calculate_metrics,
)
from governance.session_metrics.models import ParsedEntry, ToolUseInfo


def _entry(ts, **kw):
    return ParsedEntry(timestamp=ts, entry_type="assistant", **kw)


class TestFilterEntriesByDays:
    def test_filters_old(self):
        now = datetime(2026, 2, 11, 10, 0, 0)
        old = now - timedelta(days=10)
        entries = [_entry(now), _entry(old)]
        filtered = filter_entries_by_days(entries, days=3)
        assert len(filtered) == 1

    def test_empty(self):
        assert filter_entries_by_days([], days=7) == []

    def test_all_recent(self):
        now = datetime(2026, 2, 11, 10, 0, 0)
        entries = [_entry(now), _entry(now - timedelta(hours=1))]
        filtered = filter_entries_by_days(entries, days=7)
        assert len(filtered) == 2


class TestSplitSessions:
    def test_single_session(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0),
            _entry(t0 + timedelta(minutes=5)),
            _entry(t0 + timedelta(minutes=10)),
        ]
        sessions = split_sessions(entries)
        assert len(sessions) == 1
        assert sessions[0].entry_count == 3

    def test_gap_creates_session(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0),
            _entry(t0 + timedelta(minutes=60)),  # > 30 min gap
        ]
        sessions = split_sessions(entries)
        assert len(sessions) == 2

    def test_empty(self):
        assert split_sessions([]) == []

    def test_custom_threshold(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0),
            _entry(t0 + timedelta(minutes=20)),
        ]
        # With 10 min threshold, this is 2 sessions
        sessions = split_sessions(entries, idle_threshold_min=10)
        assert len(sessions) == 2
        # With 30 min threshold, this is 1 session
        sessions = split_sessions(entries, idle_threshold_min=30)
        assert len(sessions) == 1


class TestCalculateMetrics:
    def test_empty(self):
        result = calculate_metrics([])
        assert result.totals.message_count == 0

    def test_basic(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0, tool_uses=[ToolUseInfo("Read", "{}", False)]),
            _entry(t0 + timedelta(minutes=5),
                   tool_uses=[ToolUseInfo("Write", "{}", False)]),
        ]
        result = calculate_metrics(entries)
        assert result.totals.message_count == 2
        assert result.totals.tool_calls == 2
        assert result.tool_breakdown["Read"] == 1
        assert result.tool_breakdown["Write"] == 1

    def test_compaction_count(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0, is_compaction=True),
            _entry(t0 + timedelta(minutes=1)),
        ]
        result = calculate_metrics(entries)
        d = result.to_dict()
        assert d["days"][0]["compactions"] == 1

    def test_per_day(self):
        d1 = datetime(2026, 2, 10, 10, 0, 0)
        d2 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [_entry(d1), _entry(d2)]
        result = calculate_metrics(entries)
        assert result.totals.days_covered == 2
        assert len(result.days) == 2

    def test_mcp_calls(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0, tool_uses=[
                ToolUseInfo("mcp__gov-core__x", "{}", True),
                ToolUseInfo("Read", "{}", False),
            ]),
        ]
        result = calculate_metrics(entries)
        assert result.totals.mcp_calls == 1
        assert result.totals.tool_calls == 2
