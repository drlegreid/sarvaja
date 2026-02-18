"""
Unit tests for Test Runner Controllers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/tests.py.
Tests: register_tests_controllers — load_tests_data, on_run_tests,
       on_view_test_run, on_run_regression, on_load_robot_summary.
"""

from unittest.mock import MagicMock, patch

from agent.governance_ui.controllers.tests import register_tests_controllers


def _setup():
    """Create mock ctrl + state, register handlers, return internals."""
    ctrl = MagicMock()
    state = MagicMock()

    triggers = {}

    def trigger_decorator(name):
        def wrapper(fn):
            triggers[name] = fn
            return fn
        return wrapper

    ctrl.trigger = MagicMock(side_effect=trigger_decorator)

    result = register_tests_controllers(state, ctrl, "http://localhost:8082")

    return ctrl, state, triggers, result


# ── Registration ─────────────────────────────────────────


class TestRegistration:
    def test_registers_triggers(self):
        _, _, triggers, _ = _setup()
        assert "load_test_results" in triggers
        assert "run_tests" in triggers
        assert "view_test_run" in triggers
        assert "run_regression" in triggers
        assert "run_regression_static" in triggers
        assert "load_robot_summary" in triggers

    def test_returns_loader(self):
        _, _, _, result = _setup()
        assert "load_tests_data" in result
        assert callable(result["load_tests_data"])


# ── load_tests_data ──────────────────────────────────────


class TestLoadTestsData:
    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_success(self, MockClient):
        _, state, triggers, _ = _setup()

        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"runs": [{"run_id": "R-1"}]}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["load_test_results"]()
        assert state.tests_recent_runs == [{"run_id": "R-1"}]
        assert state.tests_loading is False

    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_api_error(self, MockClient):
        _, state, triggers, _ = _setup()

        mock_resp = MagicMock(status_code=500)
        mock_resp.json.return_value = None
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["load_test_results"]()
        assert state.tests_recent_runs == []
        assert state.tests_loading is False

    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_exception(self, MockClient):
        _, state, triggers, _ = _setup()
        MockClient.side_effect = Exception("timeout")

        triggers["load_test_results"]()
        assert state.tests_recent_runs == []
        assert state.tests_loading is False


# ── run_tests ────────────────────────────────────────────


class TestRunTests:
    @patch("agent.governance_ui.controllers.tests.threading")
    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_success_starts_polling(self, MockClient, mock_threading):
        _, state, triggers, _ = _setup()

        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"run_id": "RUN-001"}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["run_tests"]("heuristic")
        assert state.tests_current_run["run_id"] == "RUN-001"
        assert state.tests_current_run["status"] == "running"
        mock_threading.Thread.assert_called_once()

    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_exception(self, MockClient):
        _, state, triggers, _ = _setup()
        MockClient.side_effect = Exception("network error")

        triggers["run_tests"]()
        assert state.tests_running is False


# ── view_test_run ────────────────────────────────────────


class TestViewTestRun:
    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_success(self, MockClient):
        _, state, triggers, _ = _setup()

        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"run_id": "RUN-001", "status": "completed"}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["view_test_run"]("RUN-001")
        assert state.tests_current_run == {"run_id": "RUN-001", "status": "completed"}

    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_exception(self, MockClient):
        _, state, triggers, _ = _setup()
        MockClient.side_effect = Exception("err")
        # Should not raise
        triggers["view_test_run"]("RUN-X")


# ── run_regression ───────────────────────────────────────


class TestRunRegression:
    @patch("agent.governance_ui.controllers.tests.threading")
    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_full_regression(self, MockClient, mock_threading):
        _, state, triggers, _ = _setup()

        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"run_id": "REG-001"}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["run_regression"]()
        assert state.tests_current_run["category"] == "regression"
        # Should NOT include skip_dynamic in URL
        url = mock_client.post.call_args[0][0]
        assert "skip_dynamic" not in url

    @patch("agent.governance_ui.controllers.tests.threading")
    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_static_regression(self, MockClient, mock_threading):
        _, state, triggers, _ = _setup()

        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"run_id": "REG-002"}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["run_regression_static"]()
        url = mock_client.post.call_args[0][0]
        assert "skip_dynamic=true" in url

    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_regression_exception(self, MockClient):
        _, state, triggers, _ = _setup()
        MockClient.side_effect = Exception("fail")

        triggers["run_regression"]()
        assert state.tests_running is False


# ── load_robot_summary ───────────────────────────────────


class TestLoadRobotSummary:
    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_success(self, MockClient):
        _, state, triggers, _ = _setup()

        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"available": True, "tests": 5}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["load_robot_summary"]()
        assert state.robot_summary == {"available": True, "tests": 5}

    @patch("agent.governance_ui.controllers.tests.httpx.Client")
    def test_exception(self, MockClient):
        _, state, triggers, _ = _setup()
        MockClient.side_effect = Exception("timeout")

        triggers["load_robot_summary"]()
        assert state.robot_summary["available"] is False
        # BUG-453-TST-008: message now contains type(e).__name__ (not str(e)) to prevent info disclosure
        assert state.robot_summary["message"] == "Exception"
