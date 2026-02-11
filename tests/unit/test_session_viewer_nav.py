"""
Unit tests for Session Viewer Navigation Mixin.

Per DOC-SIZE-01-v1: Tests for extracted session_viewer_nav.py module.
Tests: search_in_session, search_all_sessions, get_adjacent_sessions,
       get_sessions_by_phase, get_sessions_by_date.
"""

import pytest
from typing import Any, Dict, List, Optional

from agent.session_viewer_nav import SessionNavigationMixin


class MockSessionViewer(SessionNavigationMixin):
    """Host class for mixin testing."""

    def __init__(self, sessions=None, detail_content=""):
        self._sessions = sessions or []
        self._detail_content = detail_content
        self._mcp_results = {}

    def get_session_detail(self, session_id):
        if session_id == "ERROR":
            return {"error": "not found"}
        return {"content": self._detail_content}

    def get_sessions_timeline(self, limit=100):
        return self._sessions[:limit]

    def parse_session_id(self, session_id):
        parts = session_id.split("-")
        if len(parts) >= 5:
            return {"phase": parts[4] if len(parts) > 4 else "Unknown"}
        return {"phase": "Unknown"}

    def _call_mcp_tool(self, tool_name, **kwargs):
        return self._mcp_results.get(tool_name, {"error": "not configured"})


class TestSearchInSession:
    """Tests for search_in_session()."""

    def test_empty_content(self):
        viewer = MockSessionViewer(detail_content="")
        result = viewer.search_in_session("S-1", "test")
        assert result == []

    def test_finds_match(self):
        content = "line 1\nline 2 test here\nline 3"
        viewer = MockSessionViewer(detail_content=content)
        result = viewer.search_in_session("S-1", "test")
        assert len(result) == 1
        assert result[0]["line"] == 2
        assert "test here" in result[0]["match"]

    def test_case_insensitive(self):
        content = "line 1\nTEST found\nline 3"
        viewer = MockSessionViewer(detail_content=content)
        result = viewer.search_in_session("S-1", "test")
        assert len(result) == 1

    def test_multiple_matches(self):
        content = "test 1\nother\ntest 2\nmore\ntest 3"
        viewer = MockSessionViewer(detail_content=content)
        result = viewer.search_in_session("S-1", "test")
        assert len(result) == 3

    def test_error_session_returns_empty(self):
        viewer = MockSessionViewer()
        result = viewer.search_in_session("ERROR", "query")
        assert result == []

    def test_context_window(self):
        content = "a\nb\nc test\nd\ne"
        viewer = MockSessionViewer(detail_content=content)
        result = viewer.search_in_session("S-1", "test")
        assert "context" in result[0]


class TestSearchAllSessions:
    """Tests for search_all_sessions()."""

    def test_error_returns_empty(self):
        viewer = MockSessionViewer()
        result = viewer.search_all_sessions("query")
        assert result == []

    def test_filters_session_results(self):
        viewer = MockSessionViewer()
        viewer._mcp_results["governance_evidence_search"] = {
            "results": [
                {"source": "SESSION-2026-02-11-TEST", "content": "match text", "score": 0.9},
                {"source": "RULE-01", "content": "not a session", "score": 0.8},
                {"source": "SESSION-2026-02-10-OTHER", "content": "other match", "score": 0.7},
            ]
        }
        result = viewer.search_all_sessions("query")
        assert len(result) == 2
        assert all("session_id" in r for r in result)

    def test_truncates_content(self):
        viewer = MockSessionViewer()
        viewer._mcp_results["governance_evidence_search"] = {
            "results": [
                {"source": "SESSION-X", "content": "A" * 300, "score": 0.5},
            ]
        }
        result = viewer.search_all_sessions("query")
        assert len(result[0]["match"]) <= 200


class TestGetAdjacentSessions:
    """Tests for get_adjacent_sessions()."""

    def test_middle_session(self):
        sessions = [
            {"session_id": "S-3"},
            {"session_id": "S-2"},
            {"session_id": "S-1"},
        ]
        viewer = MockSessionViewer(sessions=sessions)
        result = viewer.get_adjacent_sessions("S-2")
        assert result["next"] == "S-3"
        assert result["previous"] == "S-1"

    def test_first_session(self):
        sessions = [
            {"session_id": "S-2"},
            {"session_id": "S-1"},
        ]
        viewer = MockSessionViewer(sessions=sessions)
        result = viewer.get_adjacent_sessions("S-2")
        assert result["next"] is None
        assert result["previous"] == "S-1"

    def test_last_session(self):
        sessions = [
            {"session_id": "S-2"},
            {"session_id": "S-1"},
        ]
        viewer = MockSessionViewer(sessions=sessions)
        result = viewer.get_adjacent_sessions("S-1")
        assert result["next"] == "S-2"
        assert result["previous"] is None

    def test_not_found(self):
        viewer = MockSessionViewer(sessions=[{"session_id": "S-1"}])
        result = viewer.get_adjacent_sessions("S-NOPE")
        assert result["next"] is None
        assert result["previous"] is None


class TestGetSessionsByPhase:
    """Tests for get_sessions_by_phase()."""

    def test_groups_by_phase(self):
        sessions = [
            {"session_id": "SESSION-2026-02-11-PHASE1-X"},
            {"session_id": "SESSION-2026-02-11-PHASE2-Y"},
            {"session_id": "SESSION-2026-02-11-PHASE1-Z"},
        ]
        viewer = MockSessionViewer(sessions=sessions)
        result = viewer.get_sessions_by_phase()
        assert len(result) >= 1

    def test_empty(self):
        viewer = MockSessionViewer(sessions=[])
        assert viewer.get_sessions_by_phase() == {}


class TestGetSessionsByDate:
    """Tests for get_sessions_by_date()."""

    def test_groups_by_date(self):
        sessions = [
            {"session_id": "S-1", "date": "2026-02-11"},
            {"session_id": "S-2", "date": "2026-02-10"},
            {"session_id": "S-3", "date": "2026-02-11"},
        ]
        viewer = MockSessionViewer(sessions=sessions)
        result = viewer.get_sessions_by_date()
        assert len(result["2026-02-11"]) == 2
        assert len(result["2026-02-10"]) == 1

    def test_empty(self):
        viewer = MockSessionViewer(sessions=[])
        assert viewer.get_sessions_by_date() == {}
