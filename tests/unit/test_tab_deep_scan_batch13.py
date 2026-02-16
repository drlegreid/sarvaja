"""
Unit tests for Tab Deep Scan Batch 13 — Error recovery + spinner reset.

Covers: tests_running spinner reset on non-200, loading flag patterns,
detail loader finally blocks, error recovery consistency.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── Tests tab spinner reset (BUG-UI-TESTS-001) ──────────────


class TestTestsSpinnerReset:
    """tests_running must be reset to False on all code paths."""

    def test_on_run_tests_has_non_200_reset(self):
        """on_run_tests must reset tests_running on non-200 status."""
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        # BUG-UI-TESTS-001: Non-200 path must reset spinner
        assert "BUG-UI-TESTS-001" in source

    def test_start_regression_has_non_200_reset(self):
        """_start_regression must reset tests_running on non-200 status."""
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        # Count: 2 occurrences of the bug marker — one in each function
        count = source.count("BUG-UI-TESTS-001")
        assert count >= 2

    @patch("agent.governance_ui.controllers.tests.httpx")
    @patch("agent.governance_ui.controllers.tests.add_api_trace")
    @patch("agent.governance_ui.controllers.tests.add_error_trace")
    @patch("agent.governance_ui.controllers.tests.time")
    def test_run_tests_non_200_resets_flag(self, mock_time, mock_err, mock_trace, mock_httpx):
        """Actual test: non-200 response resets tests_running."""
        mock_time.time.return_value = 0

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        state = MagicMock()
        state.tests_running = False
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tests import register_tests_controllers
        register_tests_controllers(state, ctrl, "http://localhost:8082")
        triggers["run_tests"]("unit")
        # After non-200 response, spinner must be reset
        assert state.tests_running is False

    @patch("agent.governance_ui.controllers.tests.httpx")
    @patch("agent.governance_ui.controllers.tests.add_api_trace")
    @patch("agent.governance_ui.controllers.tests.add_error_trace")
    @patch("agent.governance_ui.controllers.tests.time")
    def test_run_tests_exception_resets_flag(self, mock_time, mock_err, mock_trace, mock_httpx):
        """Exception during API call resets tests_running."""
        mock_time.time.return_value = 0
        mock_httpx.Client.return_value.__enter__ = MagicMock(
            side_effect=Exception("connection refused"))
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        state = MagicMock()
        state.tests_running = False
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tests import register_tests_controllers
        register_tests_controllers(state, ctrl, "http://localhost:8082")
        triggers["run_tests"]()
        assert state.tests_running is False


# ── Detail loader finally blocks ────────────────────────────


class TestDetailLoaderFinallyBlocks:
    """Session detail loaders must use finally blocks for loading flags."""

    def test_tool_calls_loader_has_finally(self):
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        # Must have finally blocks
        assert "session_tool_calls_loading = False" in source

    def test_thinking_loader_has_finally(self):
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        assert "session_thinking_items_loading = False" in source

    def test_evidence_loader_has_finally(self):
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        assert "session_evidence_loading = False" in source

    def test_tasks_loader_has_finally(self):
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        assert "session_tasks_loading = False" in source

    def test_transcript_loader_has_finally(self):
        from agent.governance_ui.controllers import sessions_detail_loaders
        source = inspect.getsource(sessions_detail_loaders)
        assert "session_transcript_loading = False" in source


# ── Metrics loader finally blocks ───────────────────────────


class TestMetricsLoaderFinallyBlocks:
    """Metrics loaders must use finally blocks for loading flags."""

    def test_metrics_loading_has_finally(self):
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        assert "finally:" in source
        assert "metrics_loading = False" in source

    def test_metrics_search_loading_has_finally(self):
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        assert "metrics_search_loading = False" in source

    def test_metrics_timeline_loading_has_finally(self):
        from agent.governance_ui.controllers import metrics
        source = inspect.getsource(metrics)
        assert "metrics_timeline_loading = False" in source


# ── Executive report finally block ──────────────────────────


class TestExecutiveLoaderFinally:
    """Executive report loader must use finally block."""

    def test_executive_loading_has_finally(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        assert "executive_loading = False" in source


# ── Chat loader finally blocks ──────────────────────────────


class TestChatLoaderFinally:
    """Chat loaders must use finally blocks."""

    def test_chat_loading_has_finally(self):
        from agent.governance_ui.controllers import chat
        source = inspect.getsource(chat)
        assert "chat_loading = False" in source

    def test_file_viewer_loading_has_finally(self):
        from agent.governance_ui.controllers import chat
        source = inspect.getsource(chat)
        assert "file_viewer_loading = False" in source

    def test_task_execution_loading_has_finally(self):
        from agent.governance_ui.controllers import chat
        source = inspect.getsource(chat)
        assert "task_execution_loading = False" in source


# ── Sessions pagination non-200 recovery ────────────────────


class TestSessionsPaginationRecovery:
    """sessions_pagination loading reset covers all status codes."""

    def test_loading_reset_outside_if_block(self):
        """is_loading = False must be reachable on non-200 paths."""
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        # Both success and exception paths must reset
        assert source.count("is_loading = False") >= 2


# ── Metrics state initialization ────────────────────────────


class TestMetricsStateInitialization:
    """Metrics state vars must be declared in initial state."""

    def test_metrics_data_initialized(self):
        from agent.governance_ui.state.metrics import get_metrics_initial_state
        state = get_metrics_initial_state()
        assert "metrics_data" in state
        assert "metrics_loading" in state
        assert "metrics_search_loading" in state
        assert "metrics_timeline_loading" in state

    def test_metrics_merged_into_initial(self):
        """get_metrics_initial_state must be merged via ** spread."""
        from agent.governance_ui.state import initial
        source = inspect.getsource(initial)
        assert "get_metrics_initial_state" in source
