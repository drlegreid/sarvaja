"""
Unit tests for Session Core MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/sessions_core.py module.
Tests: session_start, session_decision, session_task, session_end,
       session_list, session_tool_call, session_thought, session_test_result.
"""

import json
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest

_P = "governance.mcp_tools.sessions_core"


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def _register(**overrides):
    mcp = _CaptureMCP()
    collector_available = overrides.get("collector", True)
    with patch(f"{_P}.SESSION_COLLECTOR_AVAILABLE", collector_available), \
         patch(f"{_P}.MONITORING_AVAILABLE", overrides.get("monitoring", False)), \
         patch(f"{_P}.TYPEDB_AVAILABLE", overrides.get("typedb", False)):
        from governance.mcp_tools.sessions_core import register_session_core_tools
        register_session_core_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _mock_format():
    with patch(f"{_P}.format_mcp_result", side_effect=lambda x: json.dumps(x)):
        yield


def _mock_collector(session_id="SESSION-2026-01-01-TEST"):
    c = MagicMock()
    c.session_id = session_id
    c.start_time = datetime(2026, 1, 1, 10, 0, 0)
    return c


# ── session_start ────────────────────────────────────────────────


class TestSessionStart:
    def test_success(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_start"](topic="test"))
        assert result["session_id"] == "SESSION-2026-01-01-TEST"
        assert result["topic"] == "test"

    def test_collector_unavailable(self):
        tools = _register(collector=False)
        with patch(f"{_P}.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(tools["session_start"](topic="test"))
        assert "error" in result


# ── session_decision ─────────────────────────────────────────────


class TestSessionDecision:
    def test_success_with_active_session(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["SESSION-2026-01-01-TEST"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_decision"](
                decision_id="D-1", name="Test", context="ctx", rationale="rat",
            ))
        assert result["decision_id"] == "D-1"

    def test_no_active_session_no_topic(self):
        tools = _register()
        with patch(f"{_P}.list_active_sessions", return_value=[]):
            result = json.loads(tools["session_decision"](
                decision_id="D-1", name="Test", context="ctx", rationale="rat",
            ))
        assert "error" in result

    def test_with_topic_override(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=[]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_decision"](
                decision_id="D-1", name="Test", context="ctx",
                rationale="rat", topic="override",
            ))
        assert result["decision_id"] == "D-1"

    def test_collector_unavailable(self):
        tools = _register(collector=False)
        with patch(f"{_P}.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(tools["session_decision"](
                decision_id="D-1", name="Test", context="ctx", rationale="rat",
            ))
        assert "error" in result


# ── session_task ─────────────────────────────────────────────────


class TestSessionTask:
    def test_success(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_task"](
                task_id="T-1", name="Task", description="Desc",
            ))
        assert result["task_id"] == "T-1"
        assert result["status"] == "pending"

    def test_no_active_session(self):
        tools = _register()
        with patch(f"{_P}.list_active_sessions", return_value=[]):
            result = json.loads(tools["session_task"](
                task_id="T-1", name="Task", description="Desc",
            ))
        assert "error" in result


# ── session_end ──────────────────────────────────────────────────


class TestSessionEnd:
    def test_success(self):
        tools = _register()
        with patch(f"{_P}.end_session", return_value="/path/to/log.md"):
            result = json.loads(tools["session_end"](topic="test"))
        assert result["log_path"] == "/path/to/log.md"

    def test_success_includes_session_id(self):
        """Per SESSION-REPORT-01-v1: session_end must return session_id."""
        tools = _register()
        with patch(f"{_P}.end_session", return_value="/path/to/log.md"):
            result = json.loads(tools["session_end"](topic="mywork"))
        assert "session_id" in result
        assert result["session_id"].startswith("SESSION-")
        assert result["session_id"].endswith("-MYWORK")

    def test_success_includes_dashboard_url(self):
        """Per SESSION-REPORT-01-v1: session_end must include dashboard hint."""
        tools = _register()
        with patch(f"{_P}.end_session", return_value="/path/to/log.md"):
            result = json.loads(tools["session_end"](topic="test"))
        assert "dashboard_url" in result
        assert "localhost:8081" in result["dashboard_url"]

    def test_success_message_contains_session_id(self):
        """Per SESSION-REPORT-01-v1: message should mention session_id."""
        tools = _register()
        with patch(f"{_P}.end_session", return_value="/path/to/log.md"):
            result = json.loads(tools["session_end"](topic="test"))
        assert "SESSION-" in result["message"]

    def test_not_found(self):
        tools = _register()
        with patch(f"{_P}.end_session", return_value=None):
            result = json.loads(tools["session_end"](topic="unknown"))
        assert "error" in result
        assert "SESSION-" in result["error"]  # Error now includes expected session_id

    def test_collector_unavailable(self):
        tools = _register(collector=False)
        with patch(f"{_P}.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(tools["session_end"](topic="test"))
        assert "error" in result


# ── session_list ─────────────────────────────────────────────────


class TestSessionList:
    def test_with_sessions(self):
        tools = _register()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1", "S-2"]):
            result = json.loads(tools["session_list"]())
        assert result["count"] == 2

    def test_empty(self):
        tools = _register()
        with patch(f"{_P}.list_active_sessions", return_value=[]):
            result = json.loads(tools["session_list"]())
        assert result["count"] == 0


# ── session_tool_call ────────────────────────────────────────────


class TestSessionToolCall:
    def test_success(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_tool_call"](
                tool_name="read_file", arguments='{"path": "/test"}',
                duration_ms=100, success=True,
            ))
        assert result["tool_name"] == "read_file"
        assert result["duration_ms"] == 100

    def test_invalid_json_arguments(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_tool_call"](
                tool_name="test", arguments="not json",
            ))
        assert result["tool_name"] == "test"

    def test_with_applied_rules(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_tool_call"](
                tool_name="test", applied_rules="RULE-A, RULE-B",
            ))
        assert result["applied_rules"] == ["RULE-A", "RULE-B"]


# ── session_thought ──────────────────────────────────────────────


class TestSessionThought:
    def test_success(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_thought"](
                thought="Analyzing the issue",
            ))
        assert result["thought_type"] == "reasoning"

    def test_with_related_tools(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_thought"](
                thought="test", related_tools="read_file, write_file",
            ))
        assert result["related_tools"] == ["read_file", "write_file"]


# ── session_test_result ──────────────────────────────────────────


class TestSessionTestResult:
    def test_success(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_test_result"](
                test_id="TEST-1", name="Test", category="unit",
                status="PASS", duration_ms=50.0,
            ))
        assert result["test_id"] == "TEST-1"
        assert result["status"] == "PASS"

    def test_with_linked_rules(self):
        tools = _register()
        col = _mock_collector()
        with patch(f"{_P}.list_active_sessions", return_value=["S-1"]), \
             patch(f"{_P}.get_or_create_session", return_value=col):
            result = json.loads(tools["session_test_result"](
                test_id="TEST-1", name="Test", category="unit",
                status="PASS", linked_rules="RULE-A, RULE-B",
            ))
        assert result["linked_rules"] == ["RULE-A", "RULE-B"]

    def test_collector_unavailable(self):
        tools = _register(collector=False)
        with patch(f"{_P}.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(tools["session_test_result"](
                test_id="TEST-1", name="Test", category="unit", status="FAIL",
            ))
        assert "error" in result
