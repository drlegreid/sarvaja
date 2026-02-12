"""
Unit tests for Data Loader Controllers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/data_loaders.py.
Tests: register_data_loader_controllers — load_trust_data, load_monitor_data,
       load_backlog_data, load_executive_report_data, trigger registration.
"""

from unittest.mock import patch, MagicMock, PropertyMock
import json

from agent.governance_ui.controllers.data_loaders import register_data_loader_controllers


def _make_state(**attrs):
    """Create a mock Trame state."""
    s = MagicMock()
    for k, v in attrs.items():
        setattr(s, k, v)
    return s


def _make_ctrl():
    """Create a mock Trame controller that captures triggers."""
    ctrl = MagicMock()
    triggers = {}

    def trigger_decorator(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator

    ctrl.trigger = trigger_decorator
    ctrl._triggers = triggers
    return ctrl


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def _setup(state=None, **state_attrs):
    """Register controllers and return (state, ctrl, loaders)."""
    s = state or _make_state(**state_attrs)
    ctrl = _make_ctrl()
    with patch("agent.governance_ui.controllers.data_loaders.register_infra_loader_controllers",
               return_value={"load_infra_status": MagicMock()}), \
         patch("agent.governance_ui.controllers.data_loaders.register_workflow_loader_controllers",
               return_value={"load_workflow_status": MagicMock()}), \
         patch("agent.governance_ui.controllers.data_loaders.register_audit_loader_controllers",
               return_value={"load_audit_trail": MagicMock()}), \
         patch("agent.governance_ui.controllers.data_loaders.register_refresh_controllers",
               return_value={"load_sessions_list": MagicMock()}):
        loaders = register_data_loader_controllers(s, ctrl, "http://localhost:8082")
    return s, ctrl, loaders


# ── Registration ───────────────────────────────────────


class TestRegistration:
    def test_returns_all_loaders(self):
        _, _, loaders = _setup()
        expected = {"load_trust_data", "load_monitor_data", "load_backlog_data",
                    "load_executive_report_data", "load_infra_status",
                    "load_workflow_status", "load_audit_trail", "load_sessions_list"}
        assert set(loaders.keys()) == expected

    def test_registers_triggers(self):
        _, ctrl, _ = _setup()
        expected_triggers = {"load_trust_data", "load_monitor_data",
                             "refresh_backlog", "load_executive_report"}
        assert expected_triggers.issubset(set(ctrl._triggers.keys()))


# ── load_trust_data ────────────────────────────────────


class TestLoadTrustData:
    @patch("agent.governance_ui.controllers.data_loaders.get_governance_stats", return_value={})
    @patch("agent.governance_ui.controllers.data_loaders.get_escalated_proposals", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.get_proposals", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.build_trust_leaderboard", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.add_api_trace")
    @patch("httpx.Client")
    def test_success_list(self, MockClient, mock_trace, mock_leaderboard,
                          mock_proposals, mock_escalated, mock_stats):
        agents = [{"agent_id": "A-1"}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, agents)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup()
        loaders["load_trust_data"]()

        assert state.agents == agents
        mock_leaderboard.assert_called_once()
        mock_proposals.assert_called_once()
        mock_escalated.assert_called_once()
        mock_stats.assert_called_once()

    @patch("agent.governance_ui.controllers.data_loaders.get_governance_stats", return_value={})
    @patch("agent.governance_ui.controllers.data_loaders.get_escalated_proposals", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.get_proposals", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.build_trust_leaderboard", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.add_api_trace")
    @patch("httpx.Client")
    def test_success_dict_with_items(self, MockClient, mock_trace, mock_lb,
                                      mock_p, mock_ep, mock_gs):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": [{"agent_id": "A-1"}]})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup()
        loaders["load_trust_data"]()

        assert state.agents == [{"agent_id": "A-1"}]

    @patch("agent.governance_ui.controllers.data_loaders.get_governance_stats", return_value={})
    @patch("agent.governance_ui.controllers.data_loaders.get_escalated_proposals", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.get_proposals", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.build_trust_leaderboard", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.add_api_trace")
    @patch("httpx.Client")
    def test_non_200_sets_empty(self, MockClient, mock_trace, mock_lb,
                                 mock_p, mock_ep, mock_gs):
        mc = MagicMock()
        mc.get.return_value = _mock_response(500, None)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup()
        loaders["load_trust_data"]()

        assert state.agents == []

    @patch("agent.governance_ui.controllers.data_loaders.get_governance_stats", return_value={})
    @patch("agent.governance_ui.controllers.data_loaders.get_escalated_proposals", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.get_proposals", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.build_trust_leaderboard", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.add_error_trace")
    @patch("httpx.Client")
    def test_exception_sets_empty(self, MockClient, mock_err, mock_lb,
                                   mock_p, mock_ep, mock_gs):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("connection refused"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup()
        loaders["load_trust_data"]()

        assert state.agents == []
        mock_err.assert_called_once()


# ── load_monitor_data ──────────────────────────────────


class TestLoadMonitorData:
    @patch("agent.governance_ui.controllers.data_loaders.get_hourly_monitor_stats", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.get_top_monitored_rules", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_stats", return_value={})
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_alerts", return_value=[])
    @patch("agent.governance_ui.controllers.data_loaders.get_monitor_feed", return_value=[])
    def test_calls_all_apis(self, mock_feed, mock_alerts, mock_stats,
                             mock_top, mock_hourly):
        state, _, loaders = _setup()
        loaders["load_monitor_data"]()

        mock_feed.assert_called_once_with(limit=50)
        mock_alerts.assert_called_once_with(acknowledged=False)
        mock_stats.assert_called_once()
        mock_top.assert_called_once_with(limit=10)
        mock_hourly.assert_called_once()


# ── load_backlog_data ──────────────────────────────────


class TestLoadBacklogData:
    @patch("httpx.Client")
    def test_loads_available_tasks(self, MockClient):
        tasks = [{"task_id": "T-1"}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, tasks)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup(backlog_agent_id=None)
        loaders["load_backlog_data"]()

        assert state.available_tasks == tasks
        assert state.claimed_tasks == []

    @patch("httpx.Client")
    def test_loads_claimed_tasks_when_agent_set(self, MockClient):
        mc = MagicMock()
        mc.get.side_effect = [
            _mock_response(200, []),  # available
            _mock_response(200, [
                {"task_id": "T-1", "agent_id": "bot-1", "status": "IN_PROGRESS"},
                {"task_id": "T-2", "agent_id": "bot-1", "status": "DONE"},
                {"task_id": "T-3", "agent_id": "other", "status": "IN_PROGRESS"},
            ]),
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup(backlog_agent_id="bot-1")
        loaders["load_backlog_data"]()

        assert len(state.claimed_tasks) == 1
        assert state.claimed_tasks[0]["task_id"] == "T-1"

    @patch("httpx.Client")
    def test_handles_dict_with_items(self, MockClient):
        mc = MagicMock()
        mc.get.side_effect = [
            _mock_response(200, []),  # available
            _mock_response(200, {"items": [
                {"task_id": "T-1", "agent_id": "bot-1", "status": "IN_PROGRESS"},
            ]}),
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup(backlog_agent_id="bot-1")
        loaders["load_backlog_data"]()

        assert len(state.claimed_tasks) == 1

    @patch("httpx.Client")
    def test_exception_sets_empty(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("timeout"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup(backlog_agent_id=None)
        loaders["load_backlog_data"]()

        assert state.available_tasks == []
        assert state.claimed_tasks == []


# ── load_executive_report_data ─────────────────────────


class TestLoadExecutiveReport:
    @patch("httpx.Client")
    def test_success_with_period(self, MockClient):
        report = {"report_id": "RPT-1", "sections": []}
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, report)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup(executive_period="week")
        # Ensure no session_id
        state.executive_session_id = None
        type(state).executive_session_id = PropertyMock(return_value=None)
        loaders["load_executive_report_data"]()

        assert state.executive_report == report
        assert state.executive_loading is False

    @patch("httpx.Client")
    def test_non_200_sets_error(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(500, None)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup(executive_period="week")
        state.executive_session_id = None
        type(state).executive_session_id = PropertyMock(return_value=None)
        loaders["load_executive_report_data"]()

        assert "error" in state.executive_report
        assert state.executive_loading is False

    @patch("httpx.Client")
    def test_exception_sets_error(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("connection refused"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, loaders = _setup(executive_period="week")
        state.executive_session_id = None
        type(state).executive_session_id = PropertyMock(return_value=None)
        loaders["load_executive_report_data"]()

        assert "error" in state.executive_report
        assert state.executive_loading is False
