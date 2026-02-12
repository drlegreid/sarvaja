"""
Unit tests for Session Intent MCP Tools.

Batch 122: Tests for governance/mcp_tools/sessions_intent.py
- session_capture_intent() — goal, source, planned tasks, previous session
- session_capture_outcome() — status, reconciliation, handoff items
"""

import json
from unittest.mock import patch, MagicMock

import pytest


_MOD = "governance.mcp_tools.sessions_intent"
_FMT = f"{_MOD}.format_mcp_result"


def _json_fmt(data):
    """Test-friendly format_mcp_result replacement returning JSON."""
    return json.dumps(data, default=str)


def _make_mock_collector(session_id="SESSION-2026-02-12-TEST"):
    collector = MagicMock()
    collector.session_id = session_id
    collector.intent = None
    return collector


def _make_mock_intent(captured_at="2026-02-12T10:00:00", planned_tasks=None):
    intent = MagicMock()
    intent.captured_at = captured_at
    intent.planned_tasks = planned_tasks or []
    return intent


def _make_mock_outcome(captured_at="2026-02-12T11:00:00"):
    outcome = MagicMock()
    outcome.captured_at = captured_at
    return outcome


def _register_and_get(tool_name):
    from governance.mcp_tools.sessions_intent import register_session_intent_tools
    mcp = MagicMock()
    tools = {}

    def tool_decorator():
        def wrapper(fn):
            tools[fn.__name__] = fn
            return fn
        return wrapper

    mcp.tool = tool_decorator
    register_session_intent_tools(mcp)
    return tools[tool_name]


# ── session_capture_intent ──────────────────────────────────


class TestSessionCaptureIntent:
    """Tests for session_capture_intent MCP tool."""

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", False)
    def test_no_collector_returns_error(self, mock_fmt):
        fn = _register_and_get("session_capture_intent")
        result = fn(goal="Test", source="unit-test")
        data = json.loads(result)
        assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.list_active_sessions", return_value=[])
    def test_no_active_session_no_topic_error(self, mock_list, mock_fmt):
        fn = _register_and_get("session_capture_intent")
        result = fn(goal="Test", source="unit-test")
        data = json.loads(result)
        assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_captures_intent_from_active_session(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.capture_intent.return_value = _make_mock_intent()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_intent")
        result = fn(goal="Fix bug", source="TODO.md")
        data = json.loads(result)
        assert data["goal"] == "Fix bug"
        assert data["source"] == "TODO.md"
        collector.capture_intent.assert_called_once()

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=[])
    @patch(f"{_MOD}.get_or_create_session")
    def test_topic_creates_new_session(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.capture_intent.return_value = _make_mock_intent()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_intent")
        fn(goal="Test", source="manual", topic="my-topic")
        mock_get.assert_called_once_with("my-topic")

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_planned_tasks_parsed(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.capture_intent.return_value = _make_mock_intent()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_intent")
        result = fn(goal="Test", source="plan", planned_tasks="P1.1, P1.2, P1.3")
        data = json.loads(result)
        assert data["planned_tasks"] == ["P1.1", "P1.2", "P1.3"]

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_previous_session_id_passed(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.capture_intent.return_value = _make_mock_intent()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_intent")
        fn(goal="Continue", source="handoff", previous_session_id="SESSION-OLD")
        call_kwargs = collector.capture_intent.call_args[1]
        assert call_kwargs["previous_session_id"] == "SESSION-OLD"

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_initial_prompt_truncated(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.capture_intent.return_value = _make_mock_intent()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_intent")
        long_prompt = "x" * 500
        result = fn(goal="Test", source="user", initial_prompt=long_prompt)
        data = json.loads(result)
        assert len(data["initial_prompt"]) <= 203  # 200 + "..."

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", True)
    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_monitoring_instrumented(self, mock_get, mock_list, mock_log, mock_fmt):
        collector = _make_mock_collector()
        collector.capture_intent.return_value = _make_mock_intent()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_intent")
        fn(goal="Test", source="monitor-test")
        mock_log.assert_called_once()
        assert mock_log.call_args[1]["event_type"] == "session_event"

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_empty_planned_tasks(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.capture_intent.return_value = _make_mock_intent()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_intent")
        result = fn(goal="Test", source="none", planned_tasks="")
        data = json.loads(result)
        assert data["planned_tasks"] == []


# ── session_capture_outcome ─────────────────────────────────


class TestSessionCaptureOutcome:
    """Tests for session_capture_outcome MCP tool."""

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", False)
    def test_no_collector_returns_error(self, mock_fmt):
        fn = _register_and_get("session_capture_outcome")
        result = fn(status="COMPLETE")
        data = json.loads(result)
        assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.list_active_sessions", return_value=[])
    def test_no_active_session_error(self, mock_list, mock_fmt):
        fn = _register_and_get("session_capture_outcome")
        result = fn(status="COMPLETE")
        data = json.loads(result)
        assert "error" in data

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_basic_outcome_capture(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.intent = None
        collector.capture_outcome.return_value = _make_mock_outcome()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_outcome")
        result = fn(status="COMPLETE")
        data = json.loads(result)
        assert data["status"] == "COMPLETE"
        assert data["reconciliation"] is None

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_reconciliation_with_intent(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.intent = _make_mock_intent(planned_tasks=["T1", "T2", "T3"])
        collector.capture_outcome.return_value = _make_mock_outcome()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_outcome")
        result = fn(status="PARTIAL", achieved_tasks="T1,T2", deferred_tasks="T3")
        data = json.loads(result)

        recon = data["reconciliation"]
        assert recon["planned_count"] == 3
        assert recon["achieved_count"] == 2
        assert recon["deferred_count"] == 1
        assert recon["completion_rate"] == pytest.approx(66.666, rel=0.01)
        assert recon["planned_not_done"] == []

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_handoff_items_pipe_separated(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.intent = None
        collector.capture_outcome.return_value = _make_mock_outcome()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_outcome")
        result = fn(status="DEFERRED", handoff_items="Item A|Item B|Item C")
        data = json.loads(result)
        assert data["handoff_items"] == ["Item A", "Item B", "Item C"]

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_discoveries_pipe_separated(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.intent = None
        collector.capture_outcome.return_value = _make_mock_outcome()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_outcome")
        result = fn(status="COMPLETE", discoveries="GAP-NEW-001|R&D item X")
        data = json.loads(result)
        assert data["discoveries"] == ["GAP-NEW-001", "R&D item X"]

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_untracked_achieved_detected(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.intent = _make_mock_intent(planned_tasks=["T1"])
        collector.capture_outcome.return_value = _make_mock_outcome()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_outcome")
        result = fn(status="COMPLETE", achieved_tasks="T1,EXTRA-1")
        data = json.loads(result)
        assert "EXTRA-1" in data["reconciliation"]["untracked_achieved"]

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_planned_not_done_detected(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.intent = _make_mock_intent(planned_tasks=["T1", "T2", "T3"])
        collector.capture_outcome.return_value = _make_mock_outcome()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_outcome")
        result = fn(status="PARTIAL", achieved_tasks="T1")
        data = json.loads(result)
        planned_not_done = set(data["reconciliation"]["planned_not_done"])
        assert planned_not_done == {"T2", "T3"}

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", False)
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_100_percent_when_no_planned(self, mock_get, mock_list, mock_fmt):
        collector = _make_mock_collector()
        collector.intent = _make_mock_intent(planned_tasks=[])
        collector.capture_outcome.return_value = _make_mock_outcome()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_outcome")
        result = fn(status="COMPLETE", achieved_tasks="ADHOC-1")
        data = json.loads(result)
        assert data["reconciliation"]["completion_rate"] == 100

    @patch(_FMT, side_effect=_json_fmt)
    @patch(f"{_MOD}.SESSION_COLLECTOR_AVAILABLE", True)
    @patch(f"{_MOD}.MONITORING_AVAILABLE", True)
    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.list_active_sessions", return_value=["SESSION-2026-02-12-TEST"])
    @patch(f"{_MOD}.get_or_create_session")
    def test_monitoring_on_outcome(self, mock_get, mock_list, mock_log, mock_fmt):
        collector = _make_mock_collector()
        collector.intent = None
        collector.capture_outcome.return_value = _make_mock_outcome()
        mock_get.return_value = collector

        fn = _register_and_get("session_capture_outcome")
        fn(status="COMPLETE")
        mock_log.assert_called_once()
        details = mock_log.call_args[1]["details"]
        assert details["action"] == "capture_outcome"
        assert details["status"] == "COMPLETE"
