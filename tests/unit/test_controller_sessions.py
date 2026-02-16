"""
Tests for sessions controllers.

Per GAP-UI-034: Session CRUD operations.
Batch 166: New coverage for controllers/sessions.py (0->14 tests).
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_state_ctrl(api_base="http://localhost:8082"):
    """Build mock state/ctrl and register session controllers."""
    state = MagicMock()
    state.is_loading = False
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

    with patch("agent.governance_ui.controllers.sessions.register_sessions_pagination") as mock_pag, \
         patch("agent.governance_ui.controllers.sessions.log_action"):
        mock_pag.return_value = MagicMock()  # load_sessions_page
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        register_sessions_controllers(state, ctrl, api_base)
    return state, ctrl, triggers, setters


class TestRegisterSessionsControllers:
    def test_registers_select_session(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "select_session" in triggers

    def test_registers_close_session_detail(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "close_session_detail" in triggers

    def test_registers_open_session_form(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "open_session_form" in triggers

    def test_registers_close_session_form(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "close_session_form" in triggers

    def test_registers_submit_session_form(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "submit_session_form" in triggers

    def test_registers_delete_session(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "delete_session" in triggers

    def test_registers_attach_evidence(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "attach_evidence" in triggers


class TestSelectSession:
    @patch("agent.governance_ui.controllers.sessions.httpx")
    def test_selects_from_local_list(self, mock_httpx):
        mock_httpx.get.side_effect = ConnectionError("offline")
        state, _, triggers, _ = _make_state_ctrl()
        state.sessions = [{"session_id": "S-001", "topic": "Test"}]
        triggers["select_session"]("S-001")
        assert state.show_session_detail is True


class TestCloseSessionDetail:
    def test_clears_state(self):
        state, _, triggers, _ = _make_state_ctrl()
        triggers["close_session_detail"]()
        assert state.show_session_detail is False
        assert state.selected_session is None


class TestOpenSessionForm:
    def test_sets_form_mode(self):
        state, _, triggers, _ = _make_state_ctrl()
        triggers["open_session_form"]("create")
        assert state.show_session_form is True


class TestCloseSessionForm:
    def test_hides_form(self):
        state, _, triggers, _ = _make_state_ctrl()
        triggers["close_session_form"]()
        assert state.show_session_form is False


class TestDeleteSession:
    @patch("agent.governance_ui.controllers.sessions.httpx")
    def test_success_closes_detail(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.delete.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        state.selected_session = {"session_id": "S-001"}
        triggers["delete_session"]()
        assert state.show_session_detail is False
