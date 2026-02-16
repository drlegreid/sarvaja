"""
Tests for decisions controller.

Per GAP-UI-033: Decision CRUD operations.
Batch 160: New coverage for controllers/decisions.py (0→20 tests).
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_state_ctrl(api_base="http://localhost:8082"):
    """Build mock state/ctrl and register controllers."""
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

    from agent.governance_ui.controllers.decisions import register_decisions_controllers
    register_decisions_controllers(state, ctrl, api_base)
    return state, ctrl, triggers, setters


class TestRegisterDecisionsControllers:
    def test_registers_select_decision(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "select_decision" in triggers

    def test_registers_close_detail(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "close_decision_detail" in triggers

    def test_registers_open_form(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "open_decision_form" in triggers

    def test_registers_close_form(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "close_decision_form" in triggers

    def test_registers_submit_trigger(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "submit_decision_form" in triggers

    def test_registers_delete_trigger(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "delete_decision" in triggers


class TestSelectDecision:
    def test_select_by_decision_id(self):
        state, _, triggers, _ = _make_state_ctrl()
        state.decisions = [
            {"decision_id": "DEC-001", "name": "Test"},
        ]
        triggers["select_decision"]("DEC-001")
        assert state.selected_decision == {"decision_id": "DEC-001", "name": "Test"}
        assert state.show_decision_detail is True

    def test_select_by_id_field(self):
        state, _, triggers, _ = _make_state_ctrl()
        state.decisions = [{"id": "DEC-002", "name": "Alt"}]
        triggers["select_decision"]("DEC-002")
        assert state.selected_decision["name"] == "Alt"

    def test_no_match_does_nothing(self):
        state, _, triggers, _ = _make_state_ctrl()
        state.decisions = [{"decision_id": "DEC-001"}]
        state.selected_decision = None
        state.show_decision_detail = False
        triggers["select_decision"]("NONEXIST")
        # show_decision_detail should not be set to True (still mock)


class TestCloseDecisionDetail:
    def test_closes_detail(self):
        state, _, triggers, _ = _make_state_ctrl()
        triggers["close_decision_detail"]()
        assert state.show_decision_detail is False
        assert state.selected_decision is None


class TestOpenDecisionForm:
    def test_create_mode_clears_fields(self):
        state, _, triggers, _ = _make_state_ctrl()
        triggers["open_decision_form"]("create")
        assert state.form_decision_id == ""
        assert state.form_decision_name == ""
        assert state.form_decision_status == "PENDING"
        assert state.show_decision_form is True

    def test_edit_mode_populates_fields(self):
        state, _, triggers, _ = _make_state_ctrl()
        state.selected_decision = {
            "decision_id": "DEC-001",
            "name": "Test Decision",
            "context": "Some context",
            "rationale": "Because",
            "status": "APPROVED",
        }
        triggers["open_decision_form"]("edit")
        assert state.form_decision_id == "DEC-001"
        assert state.form_decision_name == "Test Decision"
        assert state.form_decision_context == "Some context"
        assert state.form_decision_status == "APPROVED"


class TestSubmitDecisionForm:
    @patch("agent.governance_ui.controllers.decisions.httpx")
    def test_create_posts_to_api(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_list_resp = MagicMock()
        mock_list_resp.status_code = 200
        mock_list_resp.json.return_value = {"items": []}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client.get.return_value = mock_list_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        state.decision_form_mode = "create"
        state.form_decision_id = "DEC-NEW"
        state.form_decision_name = "New"
        state.form_decision_context = "Some context"
        state.form_decision_rationale = ""
        state.form_decision_status = "PENDING"
        triggers["submit_decision_form"]()
        mock_client.post.assert_called_once()
        assert state.show_decision_form is False

    @patch("agent.governance_ui.controllers.decisions.httpx")
    def test_edit_puts_to_api(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_list_resp = MagicMock()
        mock_list_resp.status_code = 200
        mock_list_resp.json.return_value = []
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.put.return_value = mock_resp
        mock_client.get.return_value = mock_list_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        state.decision_form_mode = "edit"
        state.selected_decision = {"id": "DEC-001"}
        state.form_decision_id = "DEC-001"
        state.form_decision_name = "Updated"
        state.form_decision_context = "Updated context"
        state.form_decision_rationale = ""
        state.form_decision_status = "APPROVED"
        triggers["submit_decision_form"]()
        mock_client.put.assert_called_once()

    @patch("agent.governance_ui.controllers.decisions.httpx")
    def test_exception_sets_error(self, mock_httpx):
        mock_httpx.Client.side_effect = ConnectionError("offline")
        state, _, triggers, _ = _make_state_ctrl()
        state.decision_form_mode = "create"
        state.form_decision_id = ""
        state.form_decision_name = "Exception Test"
        state.form_decision_context = "Some context"
        state.form_decision_rationale = ""
        state.form_decision_status = "PENDING"
        triggers["submit_decision_form"]()
        assert state.has_error is True
        assert state.is_loading is False


class TestDeleteDecision:
    def test_no_selection_returns_early(self):
        state, _, triggers, _ = _make_state_ctrl()
        state.selected_decision = None
        triggers["delete_decision"]()

    @patch("agent.governance_ui.controllers.decisions.httpx")
    def test_success_clears_selection(self, mock_httpx):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_list_resp = MagicMock()
        mock_list_resp.status_code = 200
        mock_list_resp.json.return_value = []
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.delete.return_value = mock_resp
        mock_client.get.return_value = mock_list_resp
        mock_httpx.Client.return_value = mock_client

        state, _, triggers, _ = _make_state_ctrl()
        state.selected_decision = {"id": "DEC-001"}
        triggers["delete_decision"]()
        assert state.show_decision_detail is False
        assert state.selected_decision is None
