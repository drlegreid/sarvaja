"""
Tests for session metrics controller.

Per SESSION-METRICS-01-v1: Metrics dashboard controller.
Batch 160: New coverage for controllers/metrics.py (0→18 tests).
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


def _make_state_ctrl(api_base="http://localhost:8082"):
    """Build mock state/ctrl and register controllers."""
    state = MagicMock()
    ctrl = MagicMock()
    triggers = {}

    def _trigger(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator

    ctrl.trigger = _trigger

    from agent.governance_ui.controllers.metrics import register_metrics_controllers
    result = register_metrics_controllers(state, ctrl, api_base)
    return state, ctrl, triggers, result


class TestRegisterMetricsControllers:
    def test_returns_dict_with_loader(self):
        _, _, _, result = _make_state_ctrl()
        assert isinstance(result, dict)
        assert "load_metrics_data" in result

    def test_loader_callable(self):
        _, _, _, result = _make_state_ctrl()
        assert callable(result["load_metrics_data"])

    def test_registers_three_triggers(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "load_metrics_data" in triggers
        assert "search_metrics" in triggers
        assert "load_metrics_timeline" in triggers


class TestLoadMetricsData:
    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_success_sets_metrics_data(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"sessions": 10}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, _, result = _make_state_ctrl()
        result["load_metrics_data"]()
        assert state.metrics_data == {"sessions": 10}
        assert state.metrics_loading is False

    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_api_error_sets_error_message(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.side_effect = Exception("bad json")
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, _, result = _make_state_ctrl()
        result["load_metrics_data"]()
        assert state.metrics_data is None
        assert "500" in state.metrics_error

    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_exception_sets_error(self, mock_httpx):
        mock_httpx.Client.side_effect = ConnectionError("offline")
        state, _, _, result = _make_state_ctrl()
        result["load_metrics_data"]()
        assert state.metrics_data is None
        assert "offline" in str(state.metrics_error)
        assert state.metrics_loading is False

    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_uses_days_filter(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, _, result = _make_state_ctrl()
        state.metrics_days_filter = 30
        result["load_metrics_data"]()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["days"] == 30


class TestSearchMetrics:
    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_success_sets_results(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"id": 1}], "total_matches": 1}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        state.metrics_search_query = "test"
        triggers["search_metrics"]()
        assert state.metrics_search_results == [{"id": 1}]
        assert state.metrics_search_total == 1

    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_error_clears_results(self, mock_httpx):
        mock_httpx.Client.side_effect = ConnectionError("offline")
        state, _, triggers, _ = _make_state_ctrl()
        state.metrics_search_query = "test"
        triggers["search_metrics"]()
        assert state.metrics_search_results == []
        assert state.metrics_search_total == 0

    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_api_error_code_clears_results(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = None
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        triggers["search_metrics"]()
        assert state.metrics_search_results == []


class TestLoadMetricsTimeline:
    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_success_sets_timeline(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"timeline": [{"date": "2026-01-01"}]}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        triggers["load_metrics_timeline"]()
        assert state.metrics_timeline == [{"date": "2026-01-01"}]

    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_exception_clears_timeline(self, mock_httpx):
        mock_httpx.Client.side_effect = ConnectionError("offline")
        state, _, triggers, _ = _make_state_ctrl()
        triggers["load_metrics_timeline"]()
        assert state.metrics_timeline == []
        assert state.metrics_timeline_loading is False

    @patch("agent.governance_ui.controllers.metrics.httpx")
    def test_api_error_clears_timeline(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        mock_resp.json.return_value = None
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        triggers["load_metrics_timeline"]()
        assert state.metrics_timeline == []
