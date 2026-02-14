"""
Tests for tasks controllers.

Per GAP-FILE-005: Task CRUD operations.
Batch 166: New coverage for controllers/tasks.py (0->18 tests).
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_state_ctrl(api_base="http://localhost:8082"):
    """Build mock state/ctrl and register task controllers."""
    state = MagicMock()
    ctrl = MagicMock()
    triggers = {}
    setters = {}

    def _trigger(name):
        def decorator(fn):
            triggers[name] = fn
            return fn
        return decorator

    def _set(name):
        def decorator(fn):
            setters[name] = fn
            return fn
        return decorator

    ctrl.trigger = _trigger
    ctrl.set = _set

    with patch("agent.governance_ui.controllers.tasks.register_tasks_navigation"):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, api_base)
    return state, ctrl, triggers, setters


class TestRegisterTasksControllers:
    def test_registers_select_task(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "select_task" in triggers

    def test_registers_close_task_detail(self):
        _, _, _, setters = _make_state_ctrl()
        assert "close_task_detail" in setters

    def test_registers_delete_task(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "delete_task" in triggers

    def test_registers_submit_task_edit(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "submit_task_edit" in triggers

    def test_registers_create_task(self):
        _, _, _, setters = _make_state_ctrl()
        assert "create_task" in setters

    def test_registers_edit_task(self):
        _, _, _, setters = _make_state_ctrl()
        assert "edit_task" in setters

    def test_registers_cancel_task_edit(self):
        _, _, _, setters = _make_state_ctrl()
        assert "cancel_task_edit" in setters


class TestSelectTask:
    @patch("agent.governance_ui.controllers.tasks.httpx")
    def test_api_success_sets_task(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"task_id": "T-001", "title": "Test"}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        state.tasks = []
        triggers["select_task"]("T-001")
        assert state.show_task_detail is True

    @patch("agent.governance_ui.controllers.tasks.httpx")
    def test_fallback_to_local_tasks(self, mock_httpx):
        mock_httpx.Client.side_effect = ConnectionError("offline")
        state, _, triggers, _ = _make_state_ctrl()
        state.tasks = [{"task_id": "T-001", "title": "Local"}]
        triggers["select_task"]("T-001")
        assert state.show_task_detail is True


class TestCloseTaskDetail:
    def test_clears_state(self):
        state, _, _, setters = _make_state_ctrl()
        setters["close_task_detail"]()
        assert state.show_task_detail is False
        assert state.selected_task is None


class TestDeleteTask:
    @patch("agent.governance_ui.controllers.tasks.httpx")
    def test_success_closes_detail(self, mock_httpx):
        mock_del_resp = MagicMock()
        mock_del_resp.status_code = 204
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {"items": [], "pagination": {}}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.delete.return_value = mock_del_resp
        mock_client.get.return_value = mock_get_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        state.selected_task = {"task_id": "T-001"}
        state.tasks_per_page = 20
        state.tasks_page = 1
        triggers["delete_task"]()
        assert state.show_task_detail is False
