"""
Unit tests for Session Metrics Temporal Queries.

Per DOC-SIZE-01-v1: Tests for session_metrics/temporal.py module.
Tests: query_at_time(), query_date_range(), activity_timeline().
"""

from datetime import datetime, timedelta

from governance.session_metrics.temporal import (
    query_at_time,
    query_date_range,
    activity_timeline,
)
from governance.session_metrics.models import ParsedEntry, ToolUseInfo


def _entry(ts, text=None, tool_uses=None, branch=None, session_id=None):
    return ParsedEntry(
        timestamp=ts, entry_type="assistant",
        text_content=text, tool_uses=tool_uses or [],
        git_branch=branch, session_id=session_id,
    )


class TestQueryAtTime:
    def test_finds_entries(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0, text="Working on tests"),
            _entry(t0 + timedelta(hours=2), text="Different"),
        ]
        result = query_at_time(entries, t0, window_minutes=30)
        assert len(result["entries"]) == 1
        assert "tests" in result["summary"]

    def test_no_match(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [_entry(t0)]
        result = query_at_time(entries, t0 + timedelta(hours=5), window_minutes=10)
        assert len(result["entries"]) == 0
        assert "No activity" in result["summary"]

    def test_tool_in_summary(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0, tool_uses=[ToolUseInfo("Read", "{}", False)]),
        ]
        result = query_at_time(entries, t0)
        assert "Read" in result["summary"]

    def test_branch_in_summary(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [_entry(t0, branch="master")]
        result = query_at_time(entries, t0)
        assert "master" in result["summary"]


class TestQueryDateRange:
    def test_filters_range(self):
        t0 = datetime(2026, 2, 10, 10, 0, 0)
        t1 = datetime(2026, 2, 11, 10, 0, 0)
        t2 = datetime(2026, 2, 12, 10, 0, 0)
        entries = [_entry(t0), _entry(t1), _entry(t2)]
        result = query_date_range(entries, t0, t1)
        assert len(result) == 2

    def test_empty(self):
        result = query_date_range([], datetime.now(), datetime.now())
        assert result == []


class TestActivityTimeline:
    def test_basic(self):
        d1 = datetime(2026, 2, 10, 10, 0, 0)
        d2 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(d1, text="Day 1 work"),
            _entry(d2, text="Day 2 work"),
        ]
        timeline = activity_timeline(entries)
        assert len(timeline) == 2
        assert timeline[0]["date"] == "2026-02-10"
        assert timeline[1]["date"] == "2026-02-11"

    def test_tools_aggregated(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0, tool_uses=[ToolUseInfo("Read", "{}", False)]),
            _entry(t0 + timedelta(minutes=1),
                   tool_uses=[ToolUseInfo("Write", "{}", False)]),
        ]
        timeline = activity_timeline(entries)
        assert "Read" in timeline[0]["tools_used"]
        assert "Write" in timeline[0]["tools_used"]

    def test_snippets_limited(self):
        t0 = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _entry(t0 + timedelta(minutes=i), text=f"snippet {i}")
            for i in range(10)
        ]
        timeline = activity_timeline(entries)
        assert len(timeline[0]["snippets"]) <= 3

    def test_empty(self):
        assert activity_timeline([]) == []
