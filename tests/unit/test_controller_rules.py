"""
Tests for rules controllers.

Per GAP-FILE-005: Rule CRUD operations.
Batch 166: New coverage for controllers/rules.py (0->14 tests).
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_state_ctrl(api_base="http://localhost:8082"):
    """Build mock state/ctrl and register rule controllers."""
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

    from agent.governance_ui.controllers.rules import register_rules_controllers
    register_rules_controllers(state, ctrl, api_base)
    return state, ctrl, triggers, setters


class TestRegisterRulesControllers:
    def test_registers_select_rule(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "select_rule" in triggers

    def test_registers_close_rule_detail(self):
        _, _, _, setters = _make_state_ctrl()
        assert "close_rule_detail" in setters

    def test_registers_show_rule_form(self):
        _, _, _, setters = _make_state_ctrl()
        assert "show_rule_form" in setters

    def test_registers_edit_rule(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "edit_rule" in triggers

    def test_registers_close_rule_form(self):
        _, _, _, setters = _make_state_ctrl()
        assert "close_rule_form" in setters

    def test_registers_submit_rule_form(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "submit_rule_form" in triggers

    def test_registers_delete_rule(self):
        _, _, triggers, _ = _make_state_ctrl()
        assert "delete_rule" in triggers

    def test_registers_filter_by_status(self):
        _, _, _, setters = _make_state_ctrl()
        assert "filter_rules_by_status" in setters

    def test_registers_search_rules(self):
        _, _, _, setters = _make_state_ctrl()
        assert "search_rules" in setters


class TestSelectRule:
    def test_selects_matching_rule(self):
        state, _, triggers, _ = _make_state_ctrl()
        state.rules = [{"rule_id": "TEST-001", "name": "Test Rule"}]
        triggers["select_rule"]("TEST-001")
        assert state.show_rule_detail is True

    def test_no_match_does_nothing(self):
        state, _, triggers, _ = _make_state_ctrl()
        state.rules = []
        triggers["select_rule"]("NONEXISTENT")


class TestCloseRuleDetail:
    def test_clears_state(self):
        state, _, _, setters = _make_state_ctrl()
        setters["close_rule_detail"]()
        assert state.show_rule_detail is False
        assert state.selected_rule is None


class TestDeleteRule:
    @patch("agent.governance_ui.controllers.rules.httpx")
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
        state.selected_rule = {"rule_id": "TEST-001"}
        triggers["delete_rule"]()
        assert state.show_rule_detail is False
