"""
Unit tests for Session Intent MCP Tools.

Per RD-INTENT: Tests for session_capture_intent and session_capture_outcome
tools that track what sessions intend and accomplish.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
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


@dataclass
class _FakeIntent:
    goal: str = "test goal"
    source: str = "test"
    planned_tasks: list = field(default_factory=list)
    previous_session_id: str = None
    initial_prompt: str = None
    captured_at: str = "2026-02-11T10:00:00"


@dataclass
class _FakeOutcome:
    status: str = "COMPLETE"
    achieved_tasks: list = field(default_factory=list)
    deferred_tasks: list = field(default_factory=list)
    handoff_items: list = field(default_factory=list)
    discoveries: list = field(default_factory=list)
    captured_at: str = "2026-02-11T11:00:00"


class _FakeCollector:
    def __init__(self, session_id="SESSION-2026-02-11-TEST", intent=None):
        self.session_id = session_id
        self.intent = intent

    def capture_intent(self, **kwargs):
        self.intent = _FakeIntent(**{k: v for k, v in kwargs.items() if v is not None})
        return self.intent

    def capture_outcome(self, **kwargs):
        return _FakeOutcome(status=kwargs.get("status", "COMPLETE"))


@pytest.fixture(autouse=True)
def _force_json():
    with patch("governance.mcp_tools.sessions_intent.format_mcp_result", side_effect=_json_format):
        yield


@pytest.fixture(autouse=True)
def _disable_monitoring():
    with patch("governance.mcp_tools.sessions_intent.MONITORING_AVAILABLE", False):
        yield


@pytest.fixture
def mcp_tools():
    with patch("governance.mcp_tools.sessions_intent.SESSION_COLLECTOR_AVAILABLE", True):
        mcp = _CaptureMCP()
        from governance.mcp_tools.sessions_intent import register_session_intent_tools
        register_session_intent_tools(mcp)
        return mcp.tools


# ---------------------------------------------------------------------------
# session_capture_intent
# ---------------------------------------------------------------------------
class TestSessionCaptureIntent:
    """Tests for session_capture_intent() tool."""

    def test_unavailable(self, mcp_tools):
        with patch("governance.mcp_tools.sessions_intent.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(mcp_tools["session_capture_intent"](
                goal="test", source="test",
            ))
        assert "error" in result
        assert "not available" in result["error"]

    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_no_active_session_no_topic(self, mock_list, mcp_tools):
        mock_list.return_value = []
        result = json.loads(mcp_tools["session_capture_intent"](
            goal="test", source="test",
        ))
        assert "error" in result
        assert "No active session" in result["error"]

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_captures_intent_with_topic(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = []
        collector = _FakeCollector()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_intent"](
            goal="Fix auth", source="TODO.md", topic="auth-fix",
        ))
        assert result["goal"] == "Fix auth"
        assert result["source"] == "TODO.md"
        assert result["session_id"] == "SESSION-2026-02-11-TEST"
        mock_get.assert_called_once_with("auth-fix")

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_uses_last_active_session(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-FIRST", "SESSION-2026-02-11-SECOND"]
        collector = _FakeCollector()
        mock_get.return_value = collector
        mcp_tools["session_capture_intent"](goal="test", source="test")
        # Uses last segment of last active session, lowercased
        mock_get.assert_called_once_with("second")

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_parses_planned_tasks(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_intent"](
            goal="test", source="test",
            planned_tasks="T-1, T-2, T-3",
        ))
        assert result["planned_tasks"] == ["T-1", "T-2", "T-3"]

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_no_planned_tasks(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_intent"](
            goal="test", source="test",
        ))
        assert result["planned_tasks"] == []

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_truncates_long_prompt(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        mock_get.return_value = collector
        long_prompt = "x" * 300
        result = json.loads(mcp_tools["session_capture_intent"](
            goal="test", source="test", initial_prompt=long_prompt,
        ))
        assert result["initial_prompt"].endswith("...")
        assert len(result["initial_prompt"]) == 203  # 200 + "..."

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_short_prompt_not_truncated(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_intent"](
            goal="test", source="test", initial_prompt="short prompt",
        ))
        assert result["initial_prompt"] == "short prompt"


# ---------------------------------------------------------------------------
# session_capture_outcome
# ---------------------------------------------------------------------------
class TestSessionCaptureOutcome:
    """Tests for session_capture_outcome() tool."""

    def test_unavailable(self, mcp_tools):
        with patch("governance.mcp_tools.sessions_intent.SESSION_COLLECTOR_AVAILABLE", False):
            result = json.loads(mcp_tools["session_capture_outcome"](
                status="COMPLETE",
            ))
        assert "error" in result

    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_no_active_session_no_topic(self, mock_list, mcp_tools):
        mock_list.return_value = []
        result = json.loads(mcp_tools["session_capture_outcome"](
            status="COMPLETE",
        ))
        assert "error" in result

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_captures_outcome(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_outcome"](
            status="COMPLETE",
            achieved_tasks="T-1,T-2",
            deferred_tasks="T-3",
            handoff_items="item1|item2",
            discoveries="GAP-1|GAP-2|GAP-3",
        ))
        assert result["status"] == "COMPLETE"
        assert result["achieved_tasks"] == ["T-1", "T-2"]
        assert result["deferred_tasks"] == ["T-3"]
        assert result["handoff_items"] == ["item1", "item2"]
        assert result["discoveries"] == ["GAP-1", "GAP-2", "GAP-3"]

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_no_optional_fields(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector()
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_outcome"](
            status="PARTIAL",
        ))
        assert result["achieved_tasks"] == []
        assert result["deferred_tasks"] == []
        assert result["handoff_items"] == []
        assert result["discoveries"] == []

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_reconciliation_with_intent(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        intent = _FakeIntent(planned_tasks=["T-1", "T-2", "T-3"])
        collector = _FakeCollector(intent=intent)
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_outcome"](
            status="PARTIAL",
            achieved_tasks="T-1,T-2",
            deferred_tasks="T-3",
        ))
        recon = result["reconciliation"]
        assert recon["planned_count"] == 3
        assert recon["achieved_count"] == 2
        assert recon["deferred_count"] == 1
        assert recon["planned_not_done"] == []  # all accounted for

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_reconciliation_untracked(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        intent = _FakeIntent(planned_tasks=["T-1"])
        collector = _FakeCollector(intent=intent)
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_outcome"](
            status="COMPLETE",
            achieved_tasks="T-1,T-BONUS",
        ))
        recon = result["reconciliation"]
        assert "T-BONUS" in recon["untracked_achieved"]

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_no_reconciliation_without_intent(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        collector = _FakeCollector(intent=None)
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_outcome"](
            status="COMPLETE",
        ))
        assert result["reconciliation"] is None

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_completion_rate(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        intent = _FakeIntent(planned_tasks=["T-1", "T-2", "T-3", "T-4"])
        collector = _FakeCollector(intent=intent)
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_outcome"](
            status="PARTIAL",
            achieved_tasks="T-1",
        ))
        recon = result["reconciliation"]
        assert recon["completion_rate"] == 25.0

    @patch("governance.mcp_tools.sessions_intent.get_or_create_session")
    @patch("governance.mcp_tools.sessions_intent.list_active_sessions")
    def test_completion_rate_no_planned(self, mock_list, mock_get, mcp_tools):
        mock_list.return_value = ["SESSION-2026-02-11-TEST"]
        intent = _FakeIntent(planned_tasks=[])
        collector = _FakeCollector(intent=intent)
        mock_get.return_value = collector
        result = json.loads(mcp_tools["session_capture_outcome"](
            status="COMPLETE",
        ))
        recon = result["reconciliation"]
        assert recon["completion_rate"] == 100
