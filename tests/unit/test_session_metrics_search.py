"""
TDD Test Spec: Session Metrics Content Search
===============================================
Per GAP-SESSION-METRICS-CONTENT: Deliberate content/decision search
+ session ID + git branch filtering.

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_session_metrics_search.py -v
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures: synthetic JSONL with searchable content
# ---------------------------------------------------------------------------

def _make_entries():
    """Create a rich set of searchable entries."""
    return [
        # Session 1, branch main
        {"type": "user", "timestamp": "2026-01-28T10:00:00Z",
         "sessionId": "sess-001", "gitBranch": "main",
         "message": {"role": "user", "content": "fix the authentication bug"}},
        {"type": "assistant", "timestamp": "2026-01-28T10:01:00Z",
         "sessionId": "sess-001", "gitBranch": "main",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "thinking", "thinking": "I need to check the auth module"},
                         {"type": "text", "text": "I'll fix the authentication issue in login.py"},
                         {"type": "tool_use", "id": "tu1", "name": "Read",
                          "input": {"file_path": "/src/auth/login.py"}},
                     ]}},
        {"type": "user", "timestamp": "2026-01-28T10:01:30Z",
         "sessionId": "sess-001", "gitBranch": "main",
         "message": {"role": "user",
                     "content": [{"type": "tool_result", "tool_use_id": "tu1",
                                  "content": "def authenticate(user, pw): ..."}]}},
        {"type": "assistant", "timestamp": "2026-01-28T10:03:00Z",
         "sessionId": "sess-001", "gitBranch": "main",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "Found the bug. The password hash comparison was wrong."},
                         {"type": "tool_use", "id": "tu2", "name": "Edit",
                          "input": {"file_path": "/src/auth/login.py"}},
                     ]}},
        # Session 2, branch feature/dashboard
        {"type": "user", "timestamp": "2026-01-29T14:00:00Z",
         "sessionId": "sess-002", "gitBranch": "feature/dashboard",
         "message": {"role": "user", "content": "add the metrics dashboard view"}},
        {"type": "assistant", "timestamp": "2026-01-29T14:02:00Z",
         "sessionId": "sess-002", "gitBranch": "feature/dashboard",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text", "text": "I'll create a new dashboard component with metrics cards."},
                         {"type": "tool_use", "id": "tu3",
                          "name": "mcp__gov-sessions__session_start",
                          "input": {"description": "dashboard work"}},
                     ]}},
        # Decision entry
        {"type": "assistant", "timestamp": "2026-01-29T14:05:00Z",
         "sessionId": "sess-002", "gitBranch": "feature/dashboard",
         "message": {"role": "assistant", "model": "claude-opus-4-5-20251101",
                     "content": [
                         {"type": "text",
                          "text": "DECISION: Using React for the dashboard instead of plain HTML."},
                     ]}},
    ]


@pytest.fixture
def search_log_dir(tmp_path):
    """Create a log dir with rich searchable content."""
    entries = _make_entries()
    log_file = tmp_path / "search-test.jsonl"
    with open(log_file, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return tmp_path, log_file


# ---------------------------------------------------------------------------
# Tests: Full-text content search
# ---------------------------------------------------------------------------

class TestContentSearch:
    """Test searching session content by text."""

    def test_search_finds_text_match(self, search_log_dir):
        """Search for 'authentication' finds matching entries."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file
        _, log_file = search_log_dir
        entries = list(parse_log_file(log_file, include_thinking=True))
        results = search_entries(entries, query="authentication")
        assert len(results) >= 1

    def test_search_case_insensitive(self, search_log_dir):
        """Search is case-insensitive."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file
        _, log_file = search_log_dir
        entries = list(parse_log_file(log_file, include_thinking=True))
        lower = search_entries(entries, query="decision")
        upper = search_entries(entries, query="DECISION")
        assert len(lower) == len(upper)
        assert len(lower) >= 1

    def test_search_in_tool_names(self, search_log_dir):
        """Search finds tool names (e.g., 'Edit')."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file
        _, log_file = search_log_dir
        entries = list(parse_log_file(log_file, include_thinking=True))
        results = search_entries(entries, query="Edit")
        assert len(results) >= 1

    def test_search_in_thinking(self, search_log_dir):
        """Search finds content in thinking blocks when included."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file
        _, log_file = search_log_dir
        entries = list(parse_log_file(log_file, include_thinking=True))
        results = search_entries(entries, query="auth module")
        assert len(results) >= 1

    def test_search_empty_query_returns_all(self, search_log_dir):
        """Empty query returns all entries."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file
        _, log_file = search_log_dir
        entries = list(parse_log_file(log_file, include_thinking=True))
        results = search_entries(entries, query="")
        assert len(results) == len(entries)

    def test_search_no_matches(self, search_log_dir):
        """Non-matching query returns empty list."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file
        _, log_file = search_log_dir
        entries = list(parse_log_file(log_file, include_thinking=True))
        results = search_entries(entries, query="zzz_nonexistent_term_zzz")
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Tests: Session ID filter
# ---------------------------------------------------------------------------

class TestSessionFilter:
    """Test filtering by session ID."""

    def test_filter_by_session_id(self, search_log_dir):
        """Filter to specific session ID returns only that session."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(entries, session_id="sess-001")
        assert len(results) >= 1
        for r in results:
            assert r.session_id == "sess-001"

    def test_filter_by_session_id_other(self, search_log_dir):
        """Filter to sess-002 returns only dashboard session."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(entries, session_id="sess-002")
        assert len(results) >= 1
        for r in results:
            assert r.session_id == "sess-002"


# ---------------------------------------------------------------------------
# Tests: Git branch filter
# ---------------------------------------------------------------------------

class TestBranchFilter:
    """Test filtering by git branch."""

    def test_filter_by_branch(self, search_log_dir):
        """Filter to 'main' branch returns only main branch entries."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(entries, git_branch="main")
        assert len(results) >= 1
        for r in results:
            assert r.git_branch == "main"

    def test_filter_by_feature_branch(self, search_log_dir):
        """Filter to feature branch returns correct entries."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(entries, git_branch="feature/dashboard")
        assert len(results) >= 1
        for r in results:
            assert r.git_branch == "feature/dashboard"


# ---------------------------------------------------------------------------
# Tests: Combined filters
# ---------------------------------------------------------------------------

class TestCombinedFilters:
    """Test combining search + session + branch filters."""

    def test_search_with_session_filter(self, search_log_dir):
        """Search 'bug' within sess-001 only."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(entries, query="bug", session_id="sess-001")
        assert len(results) >= 1
        for r in results:
            assert r.session_id == "sess-001"

    def test_search_with_branch_filter(self, search_log_dir):
        """Search 'dashboard' on feature/dashboard branch only."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(
            entries, query="dashboard", git_branch="feature/dashboard",
        )
        assert len(results) >= 1
        for r in results:
            assert r.git_branch == "feature/dashboard"

    def test_no_match_on_wrong_branch(self, search_log_dir):
        """Search 'dashboard' on main branch returns nothing."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(
            entries, query="dashboard", git_branch="main",
        )
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Tests: Extended parser (session_id, git_branch extraction)
# ---------------------------------------------------------------------------

class TestExtendedParser:
    """Test that extended parser extracts session_id and git_branch."""

    def test_extended_parser_extracts_session_id(self, search_log_dir):
        """Extended parser populates session_id field."""
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        session_ids = {e.session_id for e in entries if e.session_id}
        assert "sess-001" in session_ids
        assert "sess-002" in session_ids

    def test_extended_parser_extracts_git_branch(self, search_log_dir):
        """Extended parser populates git_branch field."""
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        branches = {e.git_branch for e in entries if e.git_branch}
        assert "main" in branches
        assert "feature/dashboard" in branches

    def test_extended_parser_extracts_text_content(self, search_log_dir):
        """Extended parser populates text_content for assistant entries."""
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        assistant_entries = [e for e in entries if e.entry_type == "assistant"]
        with_text = [e for e in assistant_entries if e.text_content]
        assert len(with_text) >= 1
        assert any("authentication" in e.text_content for e in with_text)


# ---------------------------------------------------------------------------
# Tests: Search result format
# ---------------------------------------------------------------------------

class TestSearchResultFormat:
    """Test search results are properly formatted."""

    def test_result_has_timestamp(self, search_log_dir):
        """Search results include timestamp."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(entries, query="authentication")
        for r in results:
            assert r.timestamp is not None

    def test_result_to_dict_serializable(self, search_log_dir):
        """Search results can be serialized to JSON."""
        from governance.session_metrics.search import search_entries, results_to_dicts
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(entries, query="authentication")
        dicts = results_to_dicts(results)
        json.dumps(dicts)  # Should not raise

    def test_result_max_results(self, search_log_dir):
        """Search respects max_results limit."""
        from governance.session_metrics.search import search_entries
        from governance.session_metrics.parser import parse_log_file_extended
        _, log_file = search_log_dir
        entries = list(parse_log_file_extended(log_file))
        results = search_entries(entries, query="", max_results=2)
        assert len(results) <= 2
