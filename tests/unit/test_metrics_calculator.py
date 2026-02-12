"""
Unit tests for Session Metrics Calculator.

Per DOC-SIZE-01-v1: Tests for session_metrics/calculator.py module.
Tests: filter_entries_by_days, split_sessions, calculate_metrics.
"""

import pytest
from datetime import datetime, timedelta

from governance.session_metrics.calculator import (
    filter_entries_by_days,
    split_sessions,
    calculate_metrics,
)
from governance.session_metrics.models import ParsedEntry, ToolUseInfo


def _make_entry(ts_offset_hours=0, tools=None, is_mcp_flags=None,
                thinking_chars=0, is_compaction=False, is_api_error=False):
    tool_list = []
    if tools:
        for i, name in enumerate(tools):
            is_mcp = is_mcp_flags[i] if is_mcp_flags else False
            tool_list.append(ToolUseInfo(name=name, input_summary="", is_mcp=is_mcp))
    return ParsedEntry(
        timestamp=datetime(2026, 2, 11, 10, 0, 0) + timedelta(hours=ts_offset_hours),
        entry_type="assistant",
        tool_uses=tool_list,
        thinking_chars=thinking_chars,
        is_compaction=is_compaction,
        is_api_error=is_api_error,
    )


# ---------------------------------------------------------------------------
# filter_entries_by_days
# ---------------------------------------------------------------------------
class TestFilterEntriesByDays:
    """Tests for filter_entries_by_days()."""

    def test_empty_entries(self):
        assert filter_entries_by_days([], days=7) == []

    def test_all_within_range(self):
        entries = [
            _make_entry(ts_offset_hours=0),
            _make_entry(ts_offset_hours=1),
        ]
        result = filter_entries_by_days(entries, days=7)
        assert len(result) == 2

    def test_filters_old_entries(self):
        entries = [
            _make_entry(ts_offset_hours=-240),  # 10 days ago
            _make_entry(ts_offset_hours=-48),   # 2 days ago
            _make_entry(ts_offset_hours=0),     # today
        ]
        result = filter_entries_by_days(entries, days=3)
        assert len(result) == 2  # last 3 days: today + 2 days ago

    def test_single_day(self):
        entries = [
            _make_entry(ts_offset_hours=-24),
            _make_entry(ts_offset_hours=0),
        ]
        result = filter_entries_by_days(entries, days=1)
        assert len(result) == 1  # only today


# ---------------------------------------------------------------------------
# split_sessions
# ---------------------------------------------------------------------------
class TestSplitSessions:
    """Tests for split_sessions()."""

    def test_empty_entries(self):
        assert split_sessions([]) == []

    def test_single_entry(self):
        sessions = split_sessions([_make_entry()])
        assert len(sessions) == 1
        assert sessions[0].entry_count == 1

    def test_continuous_activity(self):
        entries = [_make_entry(ts_offset_hours=i * 0.1) for i in range(5)]
        sessions = split_sessions(entries, idle_threshold_min=30)
        assert len(sessions) == 1
        assert sessions[0].entry_count == 5

    def test_split_on_idle_gap(self):
        entries = [
            _make_entry(ts_offset_hours=0),
            _make_entry(ts_offset_hours=0.1),
            # 2-hour gap
            _make_entry(ts_offset_hours=2),
            _make_entry(ts_offset_hours=2.1),
        ]
        sessions = split_sessions(entries, idle_threshold_min=30)
        assert len(sessions) == 2
        assert sessions[0].entry_count == 2
        assert sessions[1].entry_count == 2

    def test_custom_threshold(self):
        entries = [
            _make_entry(ts_offset_hours=0),
            _make_entry(ts_offset_hours=0.25),  # 15 min gap
            _make_entry(ts_offset_hours=0.5),
        ]
        # With 10-min threshold, 15-min gap splits
        sessions = split_sessions(entries, idle_threshold_min=10)
        assert len(sessions) == 3  # each entry is its own session

    def test_active_minutes_calculated(self):
        entries = [
            _make_entry(ts_offset_hours=0),
            _make_entry(ts_offset_hours=1),  # 60 min later
        ]
        sessions = split_sessions(entries, idle_threshold_min=120)
        assert sessions[0].active_minutes == 60

    def test_unsorted_entries_handled(self):
        entries = [
            _make_entry(ts_offset_hours=2),
            _make_entry(ts_offset_hours=0),
            _make_entry(ts_offset_hours=1),
        ]
        sessions = split_sessions(entries, idle_threshold_min=120)
        assert sessions[0].entry_count == 3


# ---------------------------------------------------------------------------
# calculate_metrics
# ---------------------------------------------------------------------------
class TestCalculateMetrics:
    """Tests for calculate_metrics()."""

    def test_empty_entries(self):
        result = calculate_metrics([])
        assert result.totals.message_count == 0
        assert result.days == []

    def test_counts_messages(self):
        entries = [_make_entry() for _ in range(5)]
        result = calculate_metrics(entries)
        assert result.totals.message_count == 5

    def test_counts_tool_calls(self):
        entries = [
            _make_entry(tools=["Read", "Write"]),
            _make_entry(tools=["Grep"]),
        ]
        result = calculate_metrics(entries)
        assert result.totals.tool_calls == 3
        assert result.tool_breakdown["Read"] == 1
        assert result.tool_breakdown["Write"] == 1
        assert result.tool_breakdown["Grep"] == 1

    def test_counts_mcp_calls(self):
        entries = [
            _make_entry(
                tools=["mcp__rules", "Read"],
                is_mcp_flags=[True, False],
            ),
        ]
        result = calculate_metrics(entries)
        assert result.totals.mcp_calls == 1

    def test_counts_thinking_chars(self):
        entries = [
            _make_entry(thinking_chars=100),
            _make_entry(thinking_chars=200),
        ]
        result = calculate_metrics(entries)
        assert result.totals.thinking_chars == 300

    def test_counts_compactions(self):
        entries = [
            _make_entry(is_compaction=True),
            _make_entry(is_compaction=False),
            _make_entry(is_compaction=True),
        ]
        result = calculate_metrics(entries)
        assert result.days[0].compactions == 2

    def test_counts_api_errors(self):
        entries = [
            _make_entry(is_api_error=True),
            _make_entry(is_api_error=False),
        ]
        result = calculate_metrics(entries)
        assert result.totals.api_errors == 1

    def test_per_day_breakdown(self):
        entries = [
            _make_entry(ts_offset_hours=0),
            _make_entry(ts_offset_hours=0.5),
            _make_entry(ts_offset_hours=24),  # next day
        ]
        result = calculate_metrics(entries)
        assert result.totals.days_covered == 2
        assert len(result.days) == 2

    def test_session_count(self):
        entries = [
            _make_entry(ts_offset_hours=0),
            _make_entry(ts_offset_hours=0.1),
            # 2-hour gap
            _make_entry(ts_offset_hours=2),
        ]
        result = calculate_metrics(entries, idle_threshold_min=30)
        assert result.totals.session_count == 2
