"""
Unit tests for Data Loader Refresh Controller.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/data_loaders_refresh.py.
Tests: _traced_get, refresh_data, load_sessions_list.
"""

from unittest.mock import patch, MagicMock

from agent.governance_ui.controllers.data_loaders_refresh import register_refresh_controllers


def _make_state(**attrs):
    s = MagicMock()
    for k, v in attrs.items():
        setattr(s, k, v)
    return s


def _make_ctrl():
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


def _mock_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = text
    return resp


def _setup(**state_attrs):
    state = _make_state(**state_attrs)
    ctrl = _make_ctrl()
    infra_loaders = {"load_infra_status": MagicMock()}
    result = register_refresh_controllers(
        state, ctrl, "http://localhost:8082", infra_loaders)
    return state, ctrl, result, infra_loaders


# ── Registration ───────────────────────────────────────


class TestRegistration:
    def test_returns_sessions_loader(self):
        _, _, result, _ = _setup()
        assert "load_sessions_list" in result

    def test_registers_triggers(self):
        _, ctrl, _, _ = _setup()
        assert "refresh_data" in ctrl._triggers
        assert "load_sessions_list" in ctrl._triggers


# ── refresh_data ───────────────────────────────────────


class TestRefreshData:
    @patch("agent.governance_ui.controllers.data_loaders_refresh.compute_timeline_data",
           return_value=([], []))
    @patch("agent.governance_ui.controllers.data_loaders_refresh.compute_session_metrics",
           return_value={"duration": "0s", "avg_tasks": 0})
    @patch("agent.governance_ui.controllers.data_loaders_refresh.compute_session_duration",
           return_value="10m")
    @patch("agent.governance_ui.controllers.data_loaders_refresh.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("agent.governance_ui.controllers.data_loaders_refresh.add_api_trace")
    @patch("httpx.Client")
    def test_success_sets_all_state(self, MockClient, mock_trace,
                                     mock_fmt, mock_dur, mock_metrics,
                                     mock_tl):
        mc = MagicMock()
        mc.get.side_effect = [
            _mock_response(200, [{"rule_id": "R-1"}]),      # rules
            _mock_response(200, [{"decision_id": "D-1"}]),   # decisions
            _mock_response(200, [{"task_id": "T-1"}]),       # tasks
            _mock_response(200, [{"session_id": "S-1", "agent_id": "a1"}]),  # sessions
            _mock_response(200, [{"agent_id": "A-1"}]),      # agents
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, ctrl, _, infra = _setup(tasks_per_page=20)
        ctrl._triggers["refresh_data"]()

        assert state.is_loading is False
        assert state.status_message == "Data refreshed from API"
        infra["load_infra_status"].assert_called_once()

    @patch("agent.governance_ui.controllers.data_loaders_refresh.add_api_trace")
    @patch("httpx.Client")
    def test_rules_dict_with_items(self, MockClient, mock_trace):
        mc = MagicMock()
        mc.get.side_effect = [
            _mock_response(200, {"items": [{"rule_id": "R-1"}]}),
            _mock_response(500),  # decisions fail
            _mock_response(500),  # tasks fail
            _mock_response(500),  # sessions fail
            _mock_response(500),  # agents fail
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, ctrl, _, _ = _setup(tasks_per_page=20)
        ctrl._triggers["refresh_data"]()

        assert state.rules == [{"rule_id": "R-1", "linked_tasks_count": 0,
                                 "linked_sessions_count": 0}]

    @patch("agent.governance_ui.controllers.data_loaders_refresh.add_api_trace")
    @patch("agent.governance_ui.controllers.data_loaders_refresh.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_tasks_dict_with_items_and_pagination(self, MockClient, mock_fmt, mock_trace):
        mc = MagicMock()
        pagination = {"total": 50, "offset": 0, "limit": 20}
        mc.get.side_effect = [
            _mock_response(500),  # rules fail
            _mock_response(500),  # decisions fail
            _mock_response(200, {"items": [{"task_id": "T-1"}], "pagination": pagination}),
            _mock_response(500),  # sessions fail
            _mock_response(500),  # agents fail
        ]
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, ctrl, _, _ = _setup(tasks_per_page=20)
        ctrl._triggers["refresh_data"]()

        assert state.tasks_pagination == pagination
        assert state.tasks_page == 1

    @patch("httpx.Client")
    def test_connection_error_sets_cached_message(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("connection refused"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, ctrl, _, _ = _setup(tasks_per_page=20)
        ctrl._triggers["refresh_data"]()

        assert state.is_loading is False
        assert "cached data" in state.status_message


# ── load_sessions_list ─────────────────────────────────


class TestLoadSessionsList:
    @patch("agent.governance_ui.controllers.data_loaders_refresh.compute_session_duration",
           return_value="5m")
    @patch("agent.governance_ui.controllers.data_loaders_refresh.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_loads_sessions(self, MockClient, mock_fmt, mock_dur):
        sessions = [{"session_id": "S-1", "start_time": "", "end_time": ""}]
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, sessions)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, result, _ = _setup()
        result["load_sessions_list"]()

        mock_dur.assert_called_once()

    @patch("agent.governance_ui.controllers.data_loaders_refresh.compute_session_duration",
           return_value="5m")
    @patch("agent.governance_ui.controllers.data_loaders_refresh.format_timestamps_in_list",
           side_effect=lambda items, _: items)
    @patch("httpx.Client")
    def test_handles_dict_response(self, MockClient, mock_fmt, mock_dur):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"items": [{"session_id": "S-1"}]})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, result, _ = _setup()
        result["load_sessions_list"]()

        mock_dur.assert_called_once()

    @patch("httpx.Client")
    def test_exception_fallback(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("timeout"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        state, _, result, _ = _setup()
        state.sessions = None  # Falsy value
        result["load_sessions_list"]()

        assert state.sessions == []
