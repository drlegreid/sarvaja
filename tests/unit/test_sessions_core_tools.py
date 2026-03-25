"""
Unit tests for Session Core MCP Tools.

Per RULE-012: Tests for session_start, session_decision, session_task,
session_end, session_list, session_tool_call, session_thought,
session_test_result.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


def _json_format(data, **kw):
    return json.dumps(data, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


class _FakeCollector:
    def __init__(self, session_id="SESSION-2026-02-11-TEST"):
        self.session_id = session_id
        self.start_time = datetime(2026, 2, 11, 9, 0, 0)

    def capture_decision(self, **kwargs):
        return MagicMock(id=kwargs["decision_id"])

    def capture_task(self, **kwargs):
        return MagicMock(id=kwargs["task_id"])

    def capture_tool_call(self, **kwargs):
        pass

    def capture_thought(self, **kwargs):
        pass

    def capture_test_result(self, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _force_json():
    with patch("governance.mcp_tools.sessions_core.format_mcp_result", side_effect=_json_format):
        yield


@pytest.fixture(autouse=True)
def _disable_monitoring():
    with patch("governance.mcp_tools.sessions_core.MONITORING_AVAILABLE", False):
        yield


@pytest.fixture
def mcp_tools():
    with patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", True):
        mcp = _CaptureMCP()
        from governance.mcp_tools.sessions_core import register_session_core_tools
        register_session_core_tools(mcp)
        return mcp.tools


# ---------------------------------------------------------------------------
# session_start
# ---------------------------------------------------------------------------
class TestSessionStart:
    """Tests for session_start tool."""

    def test_unavailable(self, mcp_tools):
        with patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(mcp_tools["session_start"](topic="test"))
        assert "error" in result

    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    def test_starts_session(self, mock_get, mcp_tools):
        mock_get.return_value = _FakeCollector()
        result = json.loads(mcp_tools["session_start"](topic="my-topic", session_type="dev"))
        assert result["session_id"] == "SESSION-2026-02-11-TEST"
        assert result["topic"] == "my-topic"
        assert result["session_type"] == "dev"
        mock_get.assert_called_once_with("my-topic", "dev")


# ---------------------------------------------------------------------------
# session_decision
# ---------------------------------------------------------------------------
class TestSessionDecision:
    """Tests for session_decision tool."""

    def test_unavailable(self, mcp_tools):
        with patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(mcp_tools["session_decision"](
                decision_id="D-1", name="Test", context="ctx", rationale="why",
            ))
        assert "error" in result

    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    def test_no_active_session(self, mock_list, mcp_tools):
        mock_list.return_value = []
        result = json.loads(mcp_tools["session_decision"](
            decision_id="D-1", name="Test", context="ctx", rationale="why",
        ))
        assert "error" in result

    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    def test_records_decision(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        mock_get.return_value = _FakeCollector()
        result = json.loads(mcp_tools["session_decision"](
            decision_id="D-1", name="Use TypeDB", context="DB choice", rationale="Better",
        ))
        assert result["decision_id"] == "D-1"
        assert result["name"] == "Use TypeDB"


# ---------------------------------------------------------------------------
# session_task
# ---------------------------------------------------------------------------
class TestSessionTask:
    """Tests for session_task tool."""

    def test_unavailable(self, mcp_tools):
        with patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(mcp_tools["session_task"](
                task_id="T-1", name="Fix", description="desc",
            ))
        assert "error" in result

    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    def test_records_task(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        mock_get.return_value = _FakeCollector()
        result = json.loads(mcp_tools["session_task"](
            task_id="T-1", name="Fix bug", description="Fix the auth bug",
            status="in_progress", priority="HIGH",
        ))
        assert result["task_id"] == "T-1"
        assert result["status"] == "in_progress"


# ---------------------------------------------------------------------------
# session_end
# ---------------------------------------------------------------------------
class TestSessionEnd:
    """Tests for session_end tool."""

    def test_unavailable(self, mcp_tools):
        with patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(mcp_tools["session_end"](topic="test"))
        assert "error" in result

    @patch("governance.mcp_tools.sessions_core.end_session")
    def test_ends_session(self, mock_end, mcp_tools):
        mock_end.return_value = "/evidence/SESSION-2026-02-11-TEST.md"
        result = json.loads(mcp_tools["session_end"](topic="test"))
        assert result["log_path"] == "/evidence/SESSION-2026-02-11-TEST.md"
        assert result["topic"] == "test"

    @patch("governance.mcp_tools.sessions_core.end_session")
    def test_session_not_found(self, mock_end, mcp_tools):
        mock_end.return_value = None
        result = json.loads(mcp_tools["session_end"](topic="nonexistent"))
        assert "error" in result


# ---------------------------------------------------------------------------
# session_list
# ---------------------------------------------------------------------------
class TestSessionList:
    """Tests for session_list tool."""

    def test_unavailable(self, mcp_tools):
        with patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(mcp_tools["session_list"]())
        assert "error" in result

    @patch("governance.session_collector.registry.list_all_active_sessions")
    def test_lists_sessions(self, mock_merge, mcp_tools):
        mock_merge.return_value = [
            {"session_id": "SESSION-A", "source": "memory"},
            {"session_id": "SESSION-B", "source": "typedb"},
        ]
        result = json.loads(mcp_tools["session_list"]())
        assert result["count"] == 2
        assert result["active_sessions"] == ["SESSION-A", "SESSION-B"]

    @patch("governance.session_collector.registry.list_all_active_sessions")
    def test_empty_list(self, mock_merge, mcp_tools):
        mock_merge.return_value = []
        result = json.loads(mcp_tools["session_list"]())
        assert result["count"] == 0

    @patch("governance.session_collector.registry.list_all_active_sessions")
    def test_merged_sources(self, mock_merge, mcp_tools):
        """FEAT-009: session_list returns merged sources."""
        mock_merge.return_value = [
            {"session_id": "SESSION-MEM", "source": "memory"},
            {"session_id": "SESSION-TDB", "source": "typedb"},
        ]
        result = json.loads(mcp_tools["session_list"]())
        assert result["count"] == 2
        assert "SESSION-MEM" in result["active_sessions"]
        assert "SESSION-TDB" in result["active_sessions"]
        assert "sources" in result

    @patch("governance.session_collector.registry.list_all_active_sessions")
    def test_backward_compat_string_list(self, mock_merge, mcp_tools):
        """FEAT-009: active_sessions is still a list of strings."""
        mock_merge.return_value = [
            {"session_id": "SESSION-A", "source": "cc_jsonl"},
        ]
        result = json.loads(mcp_tools["session_list"]())
        assert isinstance(result["active_sessions"], list)
        assert all(isinstance(s, str) for s in result["active_sessions"])

    @patch("governance.session_collector.registry.list_all_active_sessions",
           side_effect=Exception("boom"))
    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    def test_fallback_on_merge_error(self, mock_list, mock_merge, mcp_tools):
        """FEAT-009: Falls back to memory-only on merge error."""
        mock_list.return_value = ["SESSION-FALLBACK"]
        result = json.loads(mcp_tools["session_list"]())
        assert result["count"] == 1
        assert result["active_sessions"] == ["SESSION-FALLBACK"]


# ---------------------------------------------------------------------------
# session_tool_call
# ---------------------------------------------------------------------------
class TestSessionToolCall:
    """Tests for session_tool_call tool."""

    def test_unavailable(self, mcp_tools):
        with patch("governance.mcp_tools.sessions_core.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(mcp_tools["session_tool_call"](tool_name="test"))
        assert "error" in result

    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    def test_records_tool_call(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        collector.capture_tool_call = MagicMock()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_tool_call"](
            tool_name="health_check", arguments='{"key": "val"}',
            duration_ms=50, success=True,
            applied_rules="RULE-001,RULE-002",
        ))
        assert result["tool_name"] == "health_check"
        assert result["duration_ms"] == 50
        assert result["applied_rules"] == ["RULE-001", "RULE-002"]

    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    def test_invalid_json_arguments(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        collector.capture_tool_call = MagicMock()
        mock_get.return_value = collector
        # Invalid JSON should be wrapped as {"raw": ...}
        mcp_tools["session_tool_call"](
            tool_name="test", arguments="not-valid-json",
        )
        call_args = collector.capture_tool_call.call_args
        assert call_args[1]["arguments"] == {"raw": "not-valid-json"}


# ---------------------------------------------------------------------------
# session_thought
# ---------------------------------------------------------------------------
class TestSessionThought:
    """Tests for session_thought tool."""

    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    def test_records_thought(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        collector.capture_thought = MagicMock()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_thought"](
            thought="I think we should fix auth first",
            thought_type="analysis",
            related_tools="read_file,grep",
            confidence=0.85,
        ))
        assert result["thought_type"] == "analysis"
        assert result["related_tools"] == ["read_file", "grep"]
        collector.capture_thought.assert_called_once()


# ---------------------------------------------------------------------------
# session_test_result
# ---------------------------------------------------------------------------
class TestSessionTestResult:
    """Tests for session_test_result tool."""

    @patch("governance.mcp_tools.sessions_core.get_or_create_session")
    @patch("governance.mcp_tools.sessions_core.list_active_sessions")
    def test_records_test_result(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        collector.capture_test_result = MagicMock()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_test_result"](
            test_id="TST-001", name="Test auth", category="unit",
            status="passed", duration_ms=15.5,
            linked_rules="RULE-001", linked_gaps="GAP-AUTH-001",
        ))
        assert result["test_id"] == "TST-001"
        assert result["status"] == "passed"
        assert result["linked_rules"] == ["RULE-001"]
        assert result["linked_gaps"] == ["GAP-AUTH-001"]
