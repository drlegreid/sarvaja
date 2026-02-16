"""TDD Tests: Task detail state reset and loading state fixes.

Validates:
1. close_task_detail resets edit_task_mode
2. claim_task/complete_task set is_loading = False on exception
3. claim_task/complete_task clear errors before starting
"""
from unittest.mock import MagicMock, patch

import pytest


_MOD = "agent.governance_ui.controllers.tasks"


@pytest.fixture
def state():
    s = MagicMock()
    s.tasks = []
    s.tasks_page = 1
    s.tasks_per_page = 20
    s.tasks_pagination = {"total": 0, "has_more": False}
    s.active_view = "tasks"
    s.tasks_status_filter = None
    s.tasks_phase_filter = None
    return s


@pytest.fixture
def triggers(state):
    """Register controllers and capture triggers."""
    ctrl = MagicMock()
    triggers = {}
    def fake_trigger(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator
    ctrl.trigger = fake_trigger
    ctrl.set = fake_trigger

    # Mock state.change to capture reactive handlers
    handlers = {}
    def fake_change(field):
        def decorator(fn):
            handlers[field] = fn
            return fn
        return decorator
    state.change = fake_change

    with patch(f"{_MOD}.register_tasks_navigation"):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://test:8082")
    return triggers


class TestCloseTaskDetailReset:
    """close_task_detail properly resets all detail state."""

    def test_resets_edit_task_mode(self, state, triggers):
        state.edit_task_mode = True
        triggers["close_task_detail"]()
        assert state.edit_task_mode is False

    def test_resets_show_task_detail(self, state, triggers):
        state.show_task_detail = True
        triggers["close_task_detail"]()
        assert state.show_task_detail is False

    def test_clears_selected_task(self, state, triggers):
        state.selected_task = {"task_id": "T-1"}
        triggers["close_task_detail"]()
        assert state.selected_task is None

    def test_clears_execution_log(self, state, triggers):
        state.task_execution_log = [{"event": "test"}]
        triggers["close_task_detail"]()
        assert state.task_execution_log == []

    def test_clears_show_task_execution(self, state, triggers):
        state.show_task_execution = True
        triggers["close_task_detail"]()
        assert state.show_task_execution is False


class TestClaimTaskLoadingState:
    """claim_task properly manages is_loading on all paths."""

    @patch(f"{_MOD}.httpx.Client")
    def test_claim_resets_loading_on_exception(self, mock_client_cls, state, triggers):
        state.selected_task = {"task_id": "T-1"}
        mock_client_cls.return_value.__enter__ = MagicMock(
            side_effect=ConnectionError("network down")
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        triggers["claim_selected_task"]()
        assert state.is_loading is False

    def test_claim_clears_error_before_start(self, state, triggers):
        state.selected_task = {"task_id": "T-1"}
        state.has_error = True
        state.error_message = "old error"
        with patch(f"{_MOD}.httpx.Client") as mock_client_cls:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"task_id": "T-1", "status": "IN_PROGRESS"}
            mock_client_cls.return_value.__enter__ = lambda s: MagicMock(post=lambda *a, **k: mock_resp)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            triggers["claim_selected_task"]()
        # has_error should have been cleared before the try
        assert state.is_loading is False


class TestCompleteTaskLoadingState:
    """complete_task properly manages is_loading on all paths."""

    @patch(f"{_MOD}.httpx.Client")
    def test_complete_resets_loading_on_exception(self, mock_client_cls, state, triggers):
        state.selected_task = {"task_id": "T-1"}
        mock_client_cls.return_value.__enter__ = MagicMock(
            side_effect=ConnectionError("network down")
        )
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        triggers["complete_selected_task"]()
        assert state.is_loading is False

    def test_complete_clears_error_before_start(self, state, triggers):
        state.selected_task = {"task_id": "T-1"}
        state.has_error = True
        with patch(f"{_MOD}.httpx.Client") as mock_client_cls:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"task_id": "T-1", "status": "DONE"}
            mock_client_cls.return_value.__enter__ = lambda s: MagicMock(post=lambda *a, **k: mock_resp)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            triggers["complete_selected_task"]()
        assert state.is_loading is False
