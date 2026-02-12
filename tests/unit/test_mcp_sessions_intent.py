"""
Unit tests for Session Intent MCP Tools.

Batch 129: Tests for governance/mcp_tools/sessions_intent.py
- session_capture_intent: goal, source, planned tasks, previous session link
- session_capture_outcome: status, achieved/deferred tasks, reconciliation
"""

import json
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

import pytest


_MOD = "governance.mcp_tools.sessions_intent"


def _json_fmt(data):
    """Simulate format_mcp_result returning JSON."""
    return json.dumps(data, indent=2, default=str)


@dataclass
class FakeIntent:
    goal: str = ""
    source: str = ""
    planned_tasks: list = field(default_factory=list)
    previous_session_id: Optional[str] = None
    initial_prompt: Optional[str] = None
    captured_at: str = field(default_factory=lambda: "2026-02-12T10:00:00")


@dataclass
class FakeOutcome:
    status: str = "COMPLETE"
    achieved_tasks: list = field(default_factory=list)
    deferred_tasks: list = field(default_factory=list)
    handoff_items: list = field(default_factory=list)
    discoveries: list = field(default_factory=list)
    captured_at: str = field(default_factory=lambda: "2026-02-12T11:00:00")


def _import_and_register():
    """Import and register session intent tools."""
    from governance.mcp_tools.sessions_intent import register_session_intent_tools

    mcp = MagicMock()
    tools = {}

    def tool_decorator():
        def wrapper(func):
            tools[func.__name__] = func
            return func
        return wrapper

    mcp.tool = tool_decorator
    register_session_intent_tools(mcp)
    return tools


# ── session_capture_intent ──────────────────────────────


class TestCaptureIntent:

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", False)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_collector_unavailable(self, mock_fmt):
        tools = _import_and_register()
        result = json.loads(tools["session_capture_intent"](
            goal="Fix bugs", source="TODO.md"))
        assert "error" in result
        assert "not available" in result["error"]

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=[])
    def test_no_active_session_no_topic(self, mock_list, mock_get, mock_fmt):
        tools = _import_and_register()
        result = json.loads(tools["session_capture_intent"](
            goal="Fix bugs", source="TODO.md"))
        assert "error" in result
        assert "No active session" in result["error"]

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_successful_intent_capture(self, mock_list, mock_get, mock_fmt):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.capture_intent.return_value = FakeIntent(
            goal="Fix bugs", source="TODO.md")
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_intent"](
            goal="Fix bugs", source="TODO.md", planned_tasks="P1.1,P1.2"))
        assert result["session_id"] == "SESSION-2026-02-12-TEST"
        assert result["goal"] == "Fix bugs"
        assert result["planned_tasks"] == ["P1.1", "P1.2"]

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=[])
    def test_creates_session_with_topic(self, mock_list, mock_get, mock_fmt):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-NEW-TOPIC"
        collector.capture_intent.return_value = FakeIntent()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_intent"](
            goal="Test", source="User", topic="new-topic"))
        assert result["session_id"] == "SESSION-2026-02-12-NEW-TOPIC"
        mock_get.assert_called_once_with("new-topic")

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_previous_session_id_passed(self, mock_list, mock_get, mock_fmt):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.capture_intent.return_value = FakeIntent()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_intent"](
            goal="Continue", source="Handoff",
            previous_session_id="SESSION-2026-02-11-OLD"))
        assert result["previous_session_id"] == "SESSION-2026-02-11-OLD"

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_long_prompt_truncated(self, mock_list, mock_get, mock_fmt):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.capture_intent.return_value = FakeIntent()
        mock_get.return_value = collector

        long_prompt = "x" * 300
        tools = _import_and_register()
        result = json.loads(tools["session_capture_intent"](
            goal="Test", source="User", initial_prompt=long_prompt))
        assert result["initial_prompt"].endswith("...")
        assert len(result["initial_prompt"]) == 203  # 200 + "..."

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.MONITORING_AVAILABLE", True)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_monitoring_called_when_available(self, mock_list, mock_get, mock_fmt, mock_log):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.capture_intent.return_value = FakeIntent()
        mock_get.return_value = collector

        tools = _import_and_register()
        tools["session_capture_intent"](goal="Test", source="User")
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["event_type"] == "session_event"

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_no_planned_tasks(self, mock_list, mock_get, mock_fmt):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.capture_intent.return_value = FakeIntent()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_intent"](
            goal="Test", source="User"))
        assert result["planned_tasks"] == []

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_uses_last_active_session_topic(self, mock_list, mock_get, mock_fmt):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.capture_intent.return_value = FakeIntent()
        mock_get.return_value = collector

        tools = _import_and_register()
        tools["session_capture_intent"](goal="Test", source="User")
        # Last session is "SESSION-2026-02-12-TEST", topic derived = "test"
        mock_get.assert_called_once_with("test")


# ── session_capture_outcome ─────────────────────────────


class TestCaptureOutcome:

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", False)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    def test_collector_unavailable(self, mock_fmt):
        tools = _import_and_register()
        result = json.loads(tools["session_capture_outcome"](status="COMPLETE"))
        assert "error" in result

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=[])
    def test_no_active_session(self, mock_list, mock_get, mock_fmt):
        tools = _import_and_register()
        result = json.loads(tools["session_capture_outcome"](status="COMPLETE"))
        assert "No active session" in result["error"]

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_successful_outcome_no_reconciliation(self, mock_list, mock_get, mock_fmt):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.intent = None  # No intent captured
        collector.capture_outcome.return_value = FakeOutcome()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_outcome"](
            status="COMPLETE", achieved_tasks="P1.1,P1.2"))
        assert result["status"] == "COMPLETE"
        assert result["achieved_tasks"] == ["P1.1", "P1.2"]
        assert result["reconciliation"] is None

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_reconciliation_with_intent(self, mock_list, mock_get, mock_fmt):
        intent = FakeIntent(
            goal="Fix bugs", source="TODO.md",
            planned_tasks=["P1.1", "P1.2", "P1.3"])
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.intent = intent
        collector.capture_outcome.return_value = FakeOutcome()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_outcome"](
            status="PARTIAL",
            achieved_tasks="P1.1,P1.2",
            deferred_tasks="P1.3"))
        recon = result["reconciliation"]
        assert recon["planned_count"] == 3
        assert recon["achieved_count"] == 2
        assert recon["deferred_count"] == 1
        assert recon["completion_rate"] == pytest.approx(66.67, abs=0.1)
        assert recon["planned_not_done"] == []  # All accounted for

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_untracked_achieved(self, mock_list, mock_get, mock_fmt):
        """Task achieved but wasn't in the original plan."""
        intent = FakeIntent(planned_tasks=["P1.1"])
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.intent = intent
        collector.capture_outcome.return_value = FakeOutcome()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_outcome"](
            status="COMPLETE", achieved_tasks="P1.1,P2.1"))
        recon = result["reconciliation"]
        assert "P2.1" in recon["untracked_achieved"]

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_planned_not_done(self, mock_list, mock_get, mock_fmt):
        """Planned task neither achieved nor deferred."""
        intent = FakeIntent(planned_tasks=["P1.1", "P1.2"])
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.intent = intent
        collector.capture_outcome.return_value = FakeOutcome()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_outcome"](
            status="PARTIAL", achieved_tasks="P1.1"))
        recon = result["reconciliation"]
        assert "P1.2" in recon["planned_not_done"]

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_pipe_separated_handoff_and_discoveries(self, mock_list, mock_get, mock_fmt):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.intent = None
        collector.capture_outcome.return_value = FakeOutcome()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_outcome"](
            status="PARTIAL",
            handoff_items="Fix login|Update docs",
            discoveries="GAP-NEW-001|R&D: Performance"))
        assert result["handoff_items"] == ["Fix login", "Update docs"]
        assert result["discoveries"] == ["GAP-NEW-001", "R&D: Performance"]

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.MONITORING_AVAILABLE", True)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_monitoring_called(self, mock_list, mock_get, mock_fmt, mock_log):
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.intent = None
        collector.capture_outcome.return_value = FakeOutcome()
        mock_get.return_value = collector

        tools = _import_and_register()
        tools["session_capture_outcome"](status="COMPLETE")
        mock_log.assert_called_once()

    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.get_or_create_session")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    def test_empty_plan_100_completion(self, mock_list, mock_get, mock_fmt):
        """No planned tasks = 100% completion by default."""
        intent = FakeIntent(planned_tasks=[])
        collector = MagicMock()
        collector.session_id = "SESSION-2026-02-12-TEST"
        collector.intent = intent
        collector.capture_outcome.return_value = FakeOutcome()
        mock_get.return_value = collector

        tools = _import_and_register()
        result = json.loads(tools["session_capture_outcome"](
            status="COMPLETE", achieved_tasks="P1.1"))
        recon = result["reconciliation"]
        assert recon["completion_rate"] == 100
