"""
Unit tests for Temporal Queries.

Per DOC-SIZE-01-v1: Tests for session_metrics/temporal.py module.
Tests: _entry_to_dict, query_at_time, query_date_range, activity_timeline.
"""

import pytest
from datetime import datetime, timedelta

from governance.session_metrics.temporal import (
    _entry_to_dict,
    query_at_time,
    query_date_range,
    activity_timeline,
)
from governance.session_metrics.models import ParsedEntry, ToolUseInfo


def _make_entry(ts=None, text=None, tools=None, session_id=None,
                git_branch=None, is_api_error=False):
    return ParsedEntry(
        timestamp=ts or datetime(2026, 2, 11, 10, 0, 0),
        entry_type="assistant",
        tool_uses=tools or [],
        text_content=text,
        session_id=session_id,
        git_branch=git_branch,
        is_api_error=is_api_error,
    )


def _make_tool(name="Read"):
    return ToolUseInfo(name=name, input_summary="")


# ---------------------------------------------------------------------------
# _entry_to_dict
# ---------------------------------------------------------------------------
class TestEntryToDict:
    """Tests for _entry_to_dict()."""

    def test_basic_conversion(self):
        entry = _make_entry(
            ts=datetime(2026, 2, 11, 14, 30, 0),
            text="Hello",
            session_id="S-1",
            git_branch="master",
        )
        d = _entry_to_dict(entry)
        assert d["timestamp"] == "2026-02-11T14:30:00"
        assert d["entry_type"] == "assistant"
        assert d["text_content"] == "Hello"
        assert d["session_id"] == "S-1"
        assert d["git_branch"] == "master"

    def test_tool_names_extracted(self):
        entry = _make_entry(tools=[_make_tool("Read"), _make_tool("Write")])
        d = _entry_to_dict(entry)
        assert d["tool_names"] == ["Read", "Write"]

    def test_api_error_flag(self):
        entry = _make_entry(is_api_error=True)
        d = _entry_to_dict(entry)
        assert d["is_api_error"] is True


# ---------------------------------------------------------------------------
# query_at_time
# ---------------------------------------------------------------------------
class TestQueryAtTime:
    """Tests for query_at_time()."""

    def test_empty_entries(self):
        result = query_at_time([], target=datetime(2026, 2, 11, 10, 0, 0))
        assert result["entries"] == []
        assert "No activity" in result["summary"]

    def test_finds_entries_in_window(self):
        target = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _make_entry(ts=target - timedelta(minutes=10)),
            _make_entry(ts=target + timedelta(minutes=5)),
            _make_entry(ts=target + timedelta(hours=2)),  # outside window
        ]
        result = query_at_time(entries, target=target, window_minutes=30)
        assert len(result["entries"]) == 2

    def test_summary_includes_text(self):
        target = datetime(2026, 2, 11, 10, 0, 0)
        entries = [_make_entry(ts=target, text="Working on TypeDB")]
        result = query_at_time(entries, target=target)
        assert "TypeDB" in result["summary"]

    def test_summary_includes_tools(self):
        target = datetime(2026, 2, 11, 10, 0, 0)
        entries = [_make_entry(ts=target, tools=[_make_tool("Grep")])]
        result = query_at_time(entries, target=target)
        assert "Grep" in result["summary"]

    def test_summary_includes_branch(self):
        target = datetime(2026, 2, 11, 10, 0, 0)
        entries = [_make_entry(ts=target, git_branch="feature-x")]
        result = query_at_time(entries, target=target)
        assert "feature-x" in result["summary"]

    def test_custom_window(self):
        target = datetime(2026, 2, 11, 10, 0, 0)
        entries = [
            _make_entry(ts=target - timedelta(minutes=5)),
            _make_entry(ts=target - timedelta(minutes=15)),  # outside 10-min window
        ]
        result = query_at_time(entries, target=target, window_minutes=10)
        assert len(result["entries"]) == 1

    def test_result_contains_metadata(self):
        target = datetime(2026, 2, 11, 10, 0, 0)
        result = query_at_time([], target=target, window_minutes=15)
        assert result["target_time"] == "2026-02-11T10:00:00"
        assert result["window_minutes"] == 15


# ---------------------------------------------------------------------------
# query_date_range
# ---------------------------------------------------------------------------
class TestQueryDateRange:
    """Tests for query_date_range()."""

    def test_empty_entries(self):
        start = datetime(2026, 2, 11)
        end = datetime(2026, 2, 12)
        assert query_date_range([], start, end) == []

    def test_filters_by_range(self):
        entries = [
            _make_entry(ts=datetime(2026, 2, 10, 12, 0, 0)),
            _make_entry(ts=datetime(2026, 2, 11, 12, 0, 0)),
            _make_entry(ts=datetime(2026, 2, 12, 12, 0, 0)),
            _make_entry(ts=datetime(2026, 2, 13, 12, 0, 0)),
        ]
        result = query_date_range(
            entries,
            start=datetime(2026, 2, 11),
            end=datetime(2026, 2, 12, 23, 59, 59),
        )
        assert len(result) == 2

    def test_returns_dicts(self):
        entries = [_make_entry(ts=datetime(2026, 2, 11, 10, 0, 0), text="test")]
        result = query_date_range(
            entries,
            start=datetime(2026, 2, 11),
            end=datetime(2026, 2, 12),
        )
        assert isinstance(result[0], dict)
        assert result[0]["text_content"] == "test"


# ---------------------------------------------------------------------------
# activity_timeline
# ---------------------------------------------------------------------------
class TestActivityTimeline:
    """Tests for activity_timeline()."""

    def test_empty_entries(self):
        assert activity_timeline([]) == []

    def test_single_day(self):
        entries = [
            _make_entry(ts=datetime(2026, 2, 11, 10, 0, 0)),
            _make_entry(ts=datetime(2026, 2, 11, 14, 0, 0)),
        ]
        result = activity_timeline(entries)
        assert len(result) == 1
        assert result[0]["date"] == "2026-02-11"
        assert result[0]["entry_count"] == 2

    def test_multiple_days_sorted(self):
        entries = [
            _make_entry(ts=datetime(2026, 2, 12, 10, 0, 0)),
            _make_entry(ts=datetime(2026, 2, 10, 10, 0, 0)),
            _make_entry(ts=datetime(2026, 2, 11, 10, 0, 0)),
        ]
        result = activity_timeline(entries)
        assert len(result) == 3
        assert result[0]["date"] == "2026-02-10"
        assert result[1]["date"] == "2026-02-11"
        assert result[2]["date"] == "2026-02-12"

    def test_tools_collected(self):
        entries = [
            _make_entry(ts=datetime(2026, 2, 11, 10, 0, 0),
                        tools=[_make_tool("Read"), _make_tool("Write")]),
        ]
        result = activity_timeline(entries)
        assert "Read" in result[0]["tools_used"]
        assert "Write" in result[0]["tools_used"]

    def test_branches_collected(self):
        entries = [
            _make_entry(ts=datetime(2026, 2, 11, 10, 0), git_branch="master"),
            _make_entry(ts=datetime(2026, 2, 11, 11, 0), git_branch="feature-x"),
        ]
        result = activity_timeline(entries)
        assert sorted(result[0]["branches"]) == ["feature-x", "master"]

    def test_snippets_capped_at_3(self):
        entries = [
            _make_entry(ts=datetime(2026, 2, 11, 10, i, 0), text=f"msg {i}")
            for i in range(5)
        ]
        result = activity_timeline(entries)
        assert len(result[0]["snippets"]) == 3

    def test_snippets_truncated_at_100_chars(self):
        long_text = "A" * 200
        entries = [_make_entry(ts=datetime(2026, 2, 11, 10, 0, 0), text=long_text)]
        result = activity_timeline(entries)
        assert len(result[0]["snippets"][0]) == 100
