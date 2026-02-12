"""
Unit tests for Context Compactor MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/context_compactor.py module.
Tests: _compile_zoom_0/1/2/3, context_compile().
"""

import json
import pytest
from unittest.mock import patch

from governance.mcp_tools.context_compactor import (
    _compile_zoom_0,
    _compile_zoom_1,
    _compile_zoom_2,
    _compile_zoom_3,
    register_context_compactor_tools,
)


def _json_format(data, **kwargs):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        if callable(name):
            self.tools[name.__name__] = name
            return name

        def decorator(fn):
            key = name if name else fn.__name__
            self.tools[key] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_context_compactor_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _force_json():
    with patch(
        "governance.mcp_tools.context_compactor.format_mcp_result",
        side_effect=_json_format,
    ):
        yield


# Sample data for zoom tests
_SESSION = {"session_id": "SESSION-TEST", "status": "ACTIVE", "agent_id": "code-agent", "description": "Test"}
_TASKS = [
    {"task_id": "T-1", "status": "DONE", "description": "Fix bug"},
    {"task_id": "T-2", "status": "TODO", "description": "Add feature"},
]
_TOOLS = [
    {"tool_name": "Read", "result": "ok", "duration_ms": 50},
    {"tool_name": "Write", "result": "error: perm denied", "duration_ms": 100},
]
_THOUGHTS = [{"thought_type": "analysis", "thought": "Found root cause"}]
_DECISIONS = [{"name": "Use TypeDB", "decision_id": "D-1", "rationale": "Better queries"}]


class TestCompileZoom0:
    def test_basic(self):
        result = _compile_zoom_0(_SESSION, _TASKS, _TOOLS, _THOUGHTS, _DECISIONS)
        assert "SESSION-TEST" in result
        assert "2 tasks" in result
        assert "1 done" in result
        assert "ACTIVE" in result

    def test_empty(self):
        result = _compile_zoom_0(_SESSION, [], [], [], [])
        assert "0 tasks" in result


class TestCompileZoom1:
    def test_includes_tasks(self):
        result = _compile_zoom_1(_SESSION, _TASKS, _TOOLS, _THOUGHTS, _DECISIONS)
        assert "Fix bug" in result
        assert "[DONE]" in result

    def test_includes_decisions(self):
        result = _compile_zoom_1(_SESSION, _TASKS, _TOOLS, _THOUGHTS, _DECISIONS)
        assert "Use TypeDB" in result


class TestCompileZoom2:
    def test_includes_tool_calls(self):
        result = _compile_zoom_2(_SESSION, _TASKS, _TOOLS, _THOUGHTS, _DECISIONS)
        assert "Read" in result
        assert "50ms" in result

    def test_includes_errors(self):
        result = _compile_zoom_2(_SESSION, _TASKS, _TOOLS, _THOUGHTS, _DECISIONS)
        assert "error" in result.lower()

    def test_includes_thoughts(self):
        result = _compile_zoom_2(_SESSION, _TASKS, _TOOLS, _THOUGHTS, _DECISIONS)
        assert "Found root cause" in result


class TestCompileZoom3:
    def test_markdown_format(self):
        result = _compile_zoom_3(_SESSION, _TASKS, _TOOLS, _THOUGHTS, _DECISIONS)
        assert result.startswith("# Session:")
        assert "## Tasks" in result
        assert "## Tool Calls" in result
        assert "## Decisions" in result

    def test_includes_all_data(self):
        result = _compile_zoom_3(_SESSION, _TASKS, _TOOLS, _THOUGHTS, _DECISIONS)
        assert "T-1" in result
        assert "T-2" in result
        assert "Read" in result
        assert "Write" in result
        assert "Use TypeDB" in result


class TestRegistration:
    def test_registers_tool(self):
        mcp = _register()
        assert "context_compile" in mcp.tools


class TestContextCompile:
    """Tests for context_compile() MCP tool."""

    @patch("governance.stores._sessions_store", {})
    def test_no_active_session(self):
        mcp = _register()
        result = json.loads(mcp.tools["context_compile"]())
        assert "error" in result

    @patch("governance.stores._sessions_store", {
        "S-1": {"session_id": "S-1", "status": "ACTIVE", "tasks": [], "tool_calls": [],
                "thoughts": [], "decisions": []},
    })
    @patch("governance.mcp_tools.context_compactor._get_session_data",
           return_value={"session_id": "S-1", "status": "ACTIVE"})
    def test_auto_finds_active(self, mock_get):
        mcp = _register()
        result = json.loads(mcp.tools["context_compile"]())
        assert result["session_id"] == "S-1"
        assert result["zoom"] == 1

    @patch("governance.stores._sessions_store", {
        "S-1": {"session_id": "S-1", "status": "ACTIVE",
                "tasks": _TASKS, "tool_calls": _TOOLS,
                "thoughts": _THOUGHTS, "decisions": _DECISIONS},
    })
    @patch("governance.mcp_tools.context_compactor._get_session_data",
           return_value={"session_id": "S-1", "status": "ACTIVE"})
    def test_zoom_0(self, mock_get):
        mcp = _register()
        result = json.loads(mcp.tools["context_compile"](session_id="S-1", zoom=0))
        assert result["zoom"] == 0
        assert "compiled_view" in result
        assert "token_estimate" in result

    @patch("governance.stores._sessions_store", {
        "S-1": {"session_id": "S-1", "status": "ACTIVE",
                "tasks": _TASKS, "tool_calls": [], "thoughts": [], "decisions": []},
    })
    @patch("governance.mcp_tools.context_compactor._get_session_data",
           return_value={"session_id": "S-1", "status": "ACTIVE"})
    def test_zoom_clamped(self, mock_get):
        mcp = _register()
        # Zoom > 3 should be clamped to 3
        result = json.loads(mcp.tools["context_compile"](session_id="S-1", zoom=10))
        assert result["zoom"] == 3

    @patch("governance.mcp_tools.context_compactor._get_session_data",
           return_value={})
    def test_session_not_found(self, mock_get):
        mcp = _register()
        result = json.loads(mcp.tools["context_compile"](session_id="MISSING"))
        assert "error" in result
