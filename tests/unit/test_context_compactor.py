"""
Unit tests for Context Compactor MCP Tools.

Per EPIC-G: Tests for context_compactor.py zoom-level compilation.
Tests: _compile_zoom_0, _compile_zoom_1, _compile_zoom_2, _get_session_data.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.mcp_tools.context_compactor import (
    _compile_zoom_0,
    _compile_zoom_1,
    _compile_zoom_2,
    _get_session_data,
)


def _session_data(**overrides):
    """Create base session data."""
    d = {"session_id": "SESSION-2026-02-11-TEST", "status": "ACTIVE"}
    d.update(overrides)
    return d


class TestCompileZoom0:
    """Tests for _compile_zoom_0() — one-line overview."""

    def test_basic_output(self):
        result = _compile_zoom_0(
            _session_data(), tasks=[], tool_calls=[], thoughts=[], decisions=[]
        )
        assert "SESSION-2026-02-11-TEST" in result
        assert "0 tasks" in result
        assert "Status: ACTIVE" in result

    def test_task_counts(self):
        tasks = [
            {"status": "DONE"}, {"status": "IN_PROGRESS"}, {"status": "COMPLETED"},
        ]
        result = _compile_zoom_0(
            _session_data(), tasks=tasks, tool_calls=[], thoughts=[], decisions=[]
        )
        assert "3 tasks (2 done)" in result

    def test_tool_call_count(self):
        tool_calls = [{"tool_name": "read"}, {"tool_name": "write"}]
        result = _compile_zoom_0(
            _session_data(), tasks=[], tool_calls=tool_calls, thoughts=[], decisions=[]
        )
        assert "2 tool calls" in result

    def test_thought_count(self):
        thoughts = [{"thought": "analysis"}]
        result = _compile_zoom_0(
            _session_data(), tasks=[], tool_calls=[], thoughts=thoughts, decisions=[]
        )
        assert "1 thoughts" in result

    def test_decision_count(self):
        decisions = [{"decision_id": "D-1"}, {"decision_id": "D-2"}]
        result = _compile_zoom_0(
            _session_data(), tasks=[], tool_calls=[], thoughts=[], decisions=decisions
        )
        assert "2 decisions" in result

    def test_unknown_session(self):
        result = _compile_zoom_0(
            {}, tasks=[], tool_calls=[], thoughts=[], decisions=[]
        )
        assert "?" in result
        assert "UNKNOWN" in result


class TestCompileZoom1:
    """Tests for _compile_zoom_1() — task names + decisions."""

    def test_includes_zoom_0(self):
        result = _compile_zoom_1(
            _session_data(), tasks=[], tool_calls=[], thoughts=[], decisions=[]
        )
        assert "SESSION-2026-02-11-TEST" in result

    def test_lists_tasks(self):
        tasks = [
            {"task_id": "T-1", "description": "Fix bug", "status": "DONE"},
            {"task_id": "T-2", "description": "Add feature", "status": "IN_PROGRESS"},
        ]
        result = _compile_zoom_1(
            _session_data(), tasks=tasks, tool_calls=[], thoughts=[], decisions=[]
        )
        assert "Tasks:" in result
        assert "[DONE] Fix bug" in result
        assert "[IN_PROGRESS] Add feature" in result

    def test_lists_decisions(self):
        decisions = [{"name": "Use TypeDB for persistence", "decision_id": "D-1"}]
        result = _compile_zoom_1(
            _session_data(), tasks=[], tool_calls=[], thoughts=[], decisions=decisions
        )
        assert "Decisions:" in result
        assert "Use TypeDB for persistence" in result

    def test_caps_tasks_at_10(self):
        tasks = [{"task_id": f"T-{i}", "status": "OPEN"} for i in range(15)]
        result = _compile_zoom_1(
            _session_data(), tasks=tasks, tool_calls=[], thoughts=[], decisions=[]
        )
        lines = [l for l in result.split("\n") if l.strip().startswith("[")]
        assert len(lines) == 10

    def test_caps_decisions_at_5(self):
        decisions = [{"name": f"Decision {i}"} for i in range(8)]
        result = _compile_zoom_1(
            _session_data(), tasks=[], tool_calls=[], thoughts=[], decisions=decisions
        )
        dec_lines = [l for l in result.split("\n") if l.strip().startswith("- ")]
        assert len(dec_lines) == 5

    def test_no_tasks_no_section(self):
        result = _compile_zoom_1(
            _session_data(), tasks=[], tool_calls=[], thoughts=[], decisions=[]
        )
        assert "Tasks:" not in result

    def test_truncates_long_description(self):
        tasks = [{"task_id": "T-1", "description": "A" * 100, "status": "OPEN"}]
        result = _compile_zoom_1(
            _session_data(), tasks=tasks, tool_calls=[], thoughts=[], decisions=[]
        )
        task_line = [l for l in result.split("\n") if "[OPEN]" in l][0]
        # Description truncated to 60 chars
        assert len(task_line) < 80


class TestCompileZoom2:
    """Tests for _compile_zoom_2() — tool calls + error patterns."""

    def test_includes_zoom_1(self):
        result = _compile_zoom_2(
            _session_data(), tasks=[], tool_calls=[], thoughts=[], decisions=[]
        )
        assert "SESSION-2026-02-11-TEST" in result

    def test_lists_tool_calls(self):
        tool_calls = [
            {"tool_name": "read_file", "result": "success", "duration_ms": 50},
            {"tool_name": "write_file", "result": "ok", "duration_ms": 100},
        ]
        result = _compile_zoom_2(
            _session_data(), tasks=[], tool_calls=tool_calls, thoughts=[], decisions=[]
        )
        assert "Tool Call Sequence:" in result
        assert "read_file" in result
        assert "write_file" in result

    def test_caps_tool_calls_at_20(self):
        tool_calls = [{"tool_name": f"tool_{i}", "result": "ok", "duration_ms": 10}
                      for i in range(30)]
        result = _compile_zoom_2(
            _session_data(), tasks=[], tool_calls=tool_calls, thoughts=[], decisions=[]
        )
        tc_lines = [l for l in result.split("\n")
                     if l.strip().startswith("tool_") or "tool_" in l]
        assert len(tc_lines) <= 20

    def test_error_pattern_detection(self):
        tool_calls = [
            {"tool_name": "api_call", "result": "error: timeout", "duration_ms": 5000},
            {"tool_name": "read_file", "result": "success", "duration_ms": 50},
        ]
        result = _compile_zoom_2(
            _session_data(), tasks=[], tool_calls=tool_calls, thoughts=[], decisions=[]
        )
        assert "Errors: 1 tool calls had errors" in result

    def test_lists_thoughts(self):
        thoughts = [
            {"thought_type": "analysis", "thought": "The issue is in the parser"},
        ]
        result = _compile_zoom_2(
            _session_data(), tasks=[], tool_calls=[], thoughts=thoughts, decisions=[]
        )
        assert "Key Thoughts:" in result
        assert "[analysis]" in result
        assert "parser" in result

    def test_no_tool_calls_no_section(self):
        result = _compile_zoom_2(
            _session_data(), tasks=[], tool_calls=[], thoughts=[], decisions=[]
        )
        assert "Tool Call Sequence:" not in result


class TestGetSessionData:
    """Tests for _get_session_data() with fallback chain."""

    @patch("governance.stores.get_typedb_client", return_value=None)
    def test_in_memory_hit(self, mock_client):
        from governance.stores import _sessions_store
        _sessions_store["SESSION-123"] = {"session_id": "SESSION-123", "status": "ACTIVE"}
        try:
            result = _get_session_data("SESSION-123")
            assert result["session_id"] == "SESSION-123"
            assert result["status"] == "ACTIVE"
        finally:
            _sessions_store.pop("SESSION-123", None)

    @patch("governance.stores.get_typedb_client", return_value=None)
    def test_not_found_returns_empty(self, mock_client):
        result = _get_session_data("SESSION-NONEXISTENT-XYZ")
        assert result == {}

    @patch("governance.stores.get_typedb_client")
    def test_typedb_fallback(self, mock_client_fn):
        mock_session = MagicMock()
        mock_session.id = "SESSION-DB"
        mock_session.status = "COMPLETED"
        mock_session.description = "DB session"
        mock_session.agent_id = "code-agent"

        mock_client = MagicMock()
        mock_client.get_session.return_value = mock_session
        mock_client_fn.return_value = mock_client

        result = _get_session_data("SESSION-DB-UNIQUE-TEST")
        assert result["session_id"] == "SESSION-DB"
        assert result["status"] == "COMPLETED"

    @patch("governance.stores.get_typedb_client")
    def test_typedb_error_returns_empty(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_session.side_effect = Exception("TypeDB down")
        mock_client_fn.return_value = mock_client

        result = _get_session_data("SESSION-ERR-UNIQUE")
        assert result == {}
