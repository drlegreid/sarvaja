"""
Unit tests for Session Metrics Content Search.

Per DOC-SIZE-01-v1: Tests for session_metrics/search.py module.
Tests: _entry_matches_query, search_entries, results_to_dicts.
"""

import pytest
from datetime import datetime

from governance.session_metrics.search import (
    _entry_matches_query,
    search_entries,
    results_to_dicts,
)
from governance.session_metrics.models import ParsedEntry, ToolUseInfo


def _make_entry(**kw):
    defaults = {
        "timestamp": datetime(2026, 2, 11, 10, 0, 0),
        "entry_type": "assistant",
        "tool_uses": [],
        "text_content": None,
        "thinking_content": None,
        "session_id": None,
        "git_branch": None,
        "model": None,
        "thinking_chars": 0,
    }
    defaults.update(kw)
    return ParsedEntry(**defaults)


def _make_tool(name="Read", input_summary="file.py"):
    return ToolUseInfo(name=name, input_summary=input_summary)


# ---------------------------------------------------------------------------
# _entry_matches_query
# ---------------------------------------------------------------------------
class TestEntryMatchesQuery:
    """Tests for _entry_matches_query()."""

    def test_matches_text_content(self):
        entry = _make_entry(text_content="Fixed the authentication bug")
        assert _entry_matches_query(entry, "authentication") is True

    def test_case_insensitive(self):
        entry = _make_entry(text_content="TypeDB schema change")
        assert _entry_matches_query(entry, "typedb") is True

    def test_matches_thinking_content(self):
        entry = _make_entry(thinking_content="Let me analyze the code")
        assert _entry_matches_query(entry, "analyze") is True

    def test_matches_tool_name(self):
        entry = _make_entry(tool_uses=[_make_tool(name="Grep")])
        assert _entry_matches_query(entry, "grep") is True

    def test_matches_tool_input(self):
        entry = _make_entry(tool_uses=[_make_tool(input_summary="pattern: TODO")])
        assert _entry_matches_query(entry, "todo") is True

    def test_no_match(self):
        entry = _make_entry(text_content="Hello world")
        assert _entry_matches_query(entry, "nonexistent") is False

    def test_none_text_fields(self):
        entry = _make_entry(text_content=None, thinking_content=None)
        assert _entry_matches_query(entry, "anything") is False

    def test_empty_tool_uses(self):
        entry = _make_entry(tool_uses=[])
        assert _entry_matches_query(entry, "tool") is False


# ---------------------------------------------------------------------------
# search_entries
# ---------------------------------------------------------------------------
class TestSearchEntries:
    """Tests for search_entries()."""

    def test_empty_entries(self):
        assert search_entries([], query="test") == []

    def test_empty_query_returns_all(self):
        entries = [_make_entry(), _make_entry(), _make_entry()]
        result = search_entries(entries, query="")
        assert len(result) == 3

    def test_text_query_filters(self):
        e1 = _make_entry(text_content="TypeDB fix")
        e2 = _make_entry(text_content="Dashboard update")
        e3 = _make_entry(text_content="TypeDB query")
        result = search_entries([e1, e2, e3], query="typedb")
        assert len(result) == 2

    def test_session_id_filter(self):
        e1 = _make_entry(session_id="S-1")
        e2 = _make_entry(session_id="S-2")
        e3 = _make_entry(session_id="S-1")
        result = search_entries([e1, e2, e3], session_id="S-1")
        assert len(result) == 2

    def test_git_branch_filter(self):
        e1 = _make_entry(git_branch="master")
        e2 = _make_entry(git_branch="feature-x")
        result = search_entries([e1, e2], git_branch="master")
        assert len(result) == 1

    def test_combined_filters(self):
        e1 = _make_entry(text_content="fix bug", session_id="S-1", git_branch="master")
        e2 = _make_entry(text_content="fix bug", session_id="S-2", git_branch="master")
        e3 = _make_entry(text_content="add test", session_id="S-1", git_branch="master")
        result = search_entries([e1, e2, e3], query="fix", session_id="S-1")
        assert len(result) == 1

    def test_max_results(self):
        entries = [_make_entry(text_content=f"item {i}") for i in range(10)]
        result = search_entries(entries, query="item", max_results=3)
        assert len(result) == 3

    def test_max_results_zero_means_unlimited(self):
        entries = [_make_entry(text_content=f"item {i}") for i in range(10)]
        result = search_entries(entries, query="item", max_results=0)
        assert len(result) == 10

    def test_whitespace_query_matches_all(self):
        entries = [_make_entry(), _make_entry()]
        result = search_entries(entries, query="  ")
        assert len(result) == 2


# ---------------------------------------------------------------------------
# results_to_dicts
# ---------------------------------------------------------------------------
class TestResultsToDicts:
    """Tests for results_to_dicts()."""

    def test_empty_list(self):
        assert results_to_dicts([]) == []

    def test_converts_entry(self):
        entry = _make_entry(
            entry_type="assistant",
            session_id="S-1",
            git_branch="master",
            text_content="Hello",
            model="claude-opus",
            thinking_chars=100,
        )
        result = results_to_dicts([entry])
        assert len(result) == 1
        d = result[0]
        assert d["entry_type"] == "assistant"
        assert d["session_id"] == "S-1"
        assert d["git_branch"] == "master"
        assert d["text_content"] == "Hello"
        assert d["model"] == "claude-opus"
        assert d["thinking_chars"] == 100

    def test_timestamp_is_iso_string(self):
        entry = _make_entry(timestamp=datetime(2026, 2, 11, 14, 30, 0))
        result = results_to_dicts([entry])
        assert result[0]["timestamp"] == "2026-02-11T14:30:00"

    def test_tool_uses_are_names(self):
        entry = _make_entry(tool_uses=[
            _make_tool(name="Read"),
            _make_tool(name="Write"),
        ])
        result = results_to_dicts([entry])
        assert result[0]["tool_uses"] == ["Read", "Write"]

    def test_multiple_entries(self):
        entries = [_make_entry(text_content=f"msg {i}") for i in range(3)]
        result = results_to_dicts(entries)
        assert len(result) == 3
