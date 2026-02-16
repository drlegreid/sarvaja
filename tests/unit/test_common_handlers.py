"""
Unit tests for Common Handlers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/handlers/common_handlers.py.
Tests: register_common_handlers (refresh_data, toggle_graph_view),
       register_view_handlers (on_view_change),
       register_backlog_handlers (load_backlog_data, claim_backlog_task,
       complete_backlog_task), register_executive_handlers,
       register_trace_bar_handlers.
"""

from unittest.mock import MagicMock, patch

import pytest


_P = "agent.governance_ui.handlers.common_handlers"


class _MockCtrl:
    """Mock Trame controller that captures triggers."""

    def __init__(self):
        self._triggers = {}
        self._setters = {}

    def trigger(self, name):
        def decorator(fn):
            self._triggers[name] = fn
            return fn
        return decorator

    def set(self, name):
        def decorator(fn):
            self._setters[name] = fn
            return fn
        return decorator


class _MockState:
    """Mock Trame state that stores attributes."""

    def __init__(self):
        self._change_handlers = {}

    def change(self, attr):
        def decorator(fn):
            self._change_handlers[attr] = fn
            return fn
        return decorator

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)


# ── register_common_handlers ─────────────────────────────────


class TestRefreshData:
    def test_successful_refresh(self):
        from agent.governance_ui.handlers.common_handlers import register_common_handlers
        ctrl = _MockCtrl()
        state = _MockState()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [{"id": "R-1"}]}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch(f"{_P}.httpx.Client", return_value=mock_client), \
             patch(f"{_P}.extract_items_from_response", return_value=[]), \
             patch(f"{_P}.format_timestamps_in_list", side_effect=lambda x, _: x), \
             patch(f"{_P}.compute_session_duration", return_value="1h 0m"):
            register_common_handlers(ctrl, state)
            ctrl._triggers["refresh_data"]()

        assert state.is_loading is False
        assert hasattr(state, "status_message")

    def test_api_unavailable(self):
        from agent.governance_ui.handlers.common_handlers import register_common_handlers
        ctrl = _MockCtrl()
        state = _MockState()

        with patch(f"{_P}.httpx.Client", side_effect=Exception("connection refused")):
            register_common_handlers(ctrl, state)
            ctrl._triggers["refresh_data"]()

        assert state.is_loading is False
        # BUG-UI-SILENT-FAIL-001: Now uses error_message + has_error
        assert state.has_error is True
        assert "unavailable" in state.error_message.lower()


class TestToggleGraphView:
    def test_toggles_state(self):
        from agent.governance_ui.handlers.common_handlers import register_common_handlers
        ctrl = _MockCtrl()
        state = _MockState()
        state.show_graph_view = False

        register_common_handlers(ctrl, state)
        ctrl._setters["toggle_graph_view"]()

        assert state.show_graph_view is True


# ── register_view_handlers ────────────────────────────────────


class TestViewHandlers:
    def test_calls_load_fn(self):
        from agent.governance_ui.handlers.common_handlers import register_view_handlers
        ctrl = _MockCtrl()
        state = _MockState()
        load_fn = MagicMock()

        register_view_handlers(ctrl, state, load_fn)
        state._change_handlers["active_view"]("rules")

        load_fn.assert_called_once_with("rules")


# ── register_backlog_handlers ─────────────────────────────────


class TestBacklogHandlers:
    def test_load_backlog_success(self):
        from agent.governance_ui.handlers.common_handlers import register_backlog_handlers
        ctrl = _MockCtrl()
        state = _MockState()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"task_id": "T-1"}]
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch(f"{_P}.httpx.Client", return_value=mock_client):
            register_backlog_handlers(ctrl, state)
            ctrl._triggers["load_backlog_data"]()

        assert state.backlog_tasks == [{"task_id": "T-1"}]
        assert state.backlog_loading is False

    def test_load_backlog_failure(self):
        from agent.governance_ui.handlers.common_handlers import register_backlog_handlers
        ctrl = _MockCtrl()
        state = _MockState()

        with patch(f"{_P}.httpx.Client", side_effect=Exception("fail")):
            register_backlog_handlers(ctrl, state)
            ctrl._triggers["load_backlog_data"]()

        assert state.backlog_loading is False
        assert hasattr(state, "backlog_error")

    def test_claim_task_success(self):
        from agent.governance_ui.handlers.common_handlers import register_backlog_handlers
        ctrl = _MockCtrl()
        state = _MockState()
        state.current_agent_id = "test-agent"

        mock_response_post = MagicMock()
        mock_response_post.status_code = 200
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = []
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response_post
        mock_client.get.return_value = mock_response_get
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch(f"{_P}.httpx.Client", return_value=mock_client):
            register_backlog_handlers(ctrl, state)
            ctrl._triggers["claim_backlog_task"]("T-1")

        assert "T-1" in state.status_message

    def test_complete_task_success(self):
        from agent.governance_ui.handlers.common_handlers import register_backlog_handlers
        ctrl = _MockCtrl()
        state = _MockState()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_client = MagicMock()
        mock_client.put.return_value = mock_response
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch(f"{_P}.httpx.Client", return_value=mock_client):
            register_backlog_handlers(ctrl, state)
            ctrl._triggers["complete_backlog_task"]("T-2")

        assert "T-2" in state.status_message

    def test_refresh_delegates(self):
        from agent.governance_ui.handlers.common_handlers import register_backlog_handlers
        ctrl = _MockCtrl()
        state = _MockState()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch(f"{_P}.httpx.Client", return_value=mock_client):
            register_backlog_handlers(ctrl, state)
            ctrl._triggers["refresh_backlog"]()

        assert state.backlog_loading is False


# ── register_executive_handlers ───────────────────────────────


class TestExecutiveHandlers:
    def test_load_report_success(self):
        from agent.governance_ui.handlers.common_handlers import register_executive_handlers
        ctrl = _MockCtrl()
        state = _MockState()
        state.executive_period = "week"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"summary": "good"}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch(f"{_P}.httpx.Client", return_value=mock_client):
            register_executive_handlers(ctrl, state)
            ctrl._triggers["load_executive_report_data"]()

        assert state.executive_report == {"summary": "good"}
        assert state.executive_loading is False

    def test_load_report_failure(self):
        from agent.governance_ui.handlers.common_handlers import register_executive_handlers
        ctrl = _MockCtrl()
        state = _MockState()
        state.executive_period = "week"

        with patch(f"{_P}.httpx.Client", side_effect=Exception("fail")):
            register_executive_handlers(ctrl, state)
            ctrl._triggers["load_executive_report_data"]()

        assert state.executive_loading is False
        assert hasattr(state, "executive_error")

    def test_trigger_delegates(self):
        from agent.governance_ui.handlers.common_handlers import register_executive_handlers
        ctrl = _MockCtrl()
        state = _MockState()
        state.executive_period = "month"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        with patch(f"{_P}.httpx.Client", return_value=mock_client):
            register_executive_handlers(ctrl, state)
            ctrl._triggers["trigger_load_executive_report"]()

        assert state.executive_loading is False


# ── register_trace_bar_handlers ───────────────────────────────


class TestTraceBarHandlers:
    def test_clear_traces(self):
        from agent.governance_ui.handlers.common_handlers import register_trace_bar_handlers
        ctrl = _MockCtrl()
        state = _MockState()

        with patch(f"{_P}.clear_traces") as mock_clear:
            register_trace_bar_handlers(ctrl, state)
            ctrl._triggers["clear_traces"]()

        mock_clear.assert_called_once_with(state)
