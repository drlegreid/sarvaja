"""
Unit tests for Rule Detail & Audit Filter Handlers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/handlers/common_handlers_audit.py.
Tests: register_rule_detail_handlers — rule detail, implementing tasks, audit filters.
"""

from unittest.mock import MagicMock, patch

from agent.governance_ui.handlers.common_handlers_audit import (
    register_rule_detail_handlers,
)


def _setup():
    """Create mock ctrl and state, register handlers, return internals."""
    ctrl = MagicMock()
    state = MagicMock()

    # Capture registered triggers and state.change callbacks
    triggers = {}
    changes = {}

    def trigger_decorator(name):
        def wrapper(fn):
            triggers[name] = fn
            return fn
        return wrapper

    def change_decorator(name):
        def wrapper(fn):
            changes[name] = fn
            return fn
        return wrapper

    ctrl.trigger = MagicMock(side_effect=trigger_decorator)
    state.change = MagicMock(side_effect=change_decorator)

    register_rule_detail_handlers(ctrl, state)

    return ctrl, state, triggers, changes


# ── Registration ─────────────────────────────────────────


class TestRegistration:
    def test_registers_trigger(self):
        ctrl, state, triggers, changes = _setup()
        assert "load_rule_implementing_tasks" in triggers

    def test_registers_show_rule_detail_change(self):
        _, _, _, changes = _setup()
        assert "show_rule_detail" in changes

    def test_registers_selected_rule_change(self):
        _, _, _, changes = _setup()
        assert "selected_rule" in changes

    def test_registers_audit_filter_changes(self):
        _, _, _, changes = _setup()
        assert "audit_filter_entity_type" in changes
        assert "audit_filter_action_type" in changes
        assert "audit_filter_entity_id" in changes
        assert "audit_filter_correlation_id" in changes


# ── load_rule_implementing_tasks ─────────────────────────


class TestLoadRuleImplementingTasks:
    def test_no_selected_rule(self):
        _, state, triggers, _ = _setup()
        state.selected_rule = None
        triggers["load_rule_implementing_tasks"]()
        assert state.rule_implementing_tasks == []

    def test_selected_rule_no_id(self):
        _, state, triggers, _ = _setup()
        state.selected_rule = {"name": "My Rule"}
        triggers["load_rule_implementing_tasks"]()
        assert state.rule_implementing_tasks == []

    @patch("agent.governance_ui.handlers.common_handlers_audit.httpx.Client")
    def test_success_with_rule_id(self, MockClient):
        _, state, triggers, _ = _setup()
        state.selected_rule = {"id": "RULE-001"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "implementing_tasks": [{"task_id": "T-1"}, {"task_id": "T-2"}]
        }
        MockClient.return_value.__enter__ = MagicMock(return_value=MagicMock(
            get=MagicMock(return_value=mock_response)
        ))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["load_rule_implementing_tasks"]()
        assert state.rule_implementing_tasks == [{"task_id": "T-1"}, {"task_id": "T-2"}]
        assert state.rule_implementing_tasks_loading is False

    @patch("agent.governance_ui.handlers.common_handlers_audit.httpx.Client")
    def test_success_with_rule_id_key(self, MockClient):
        _, state, triggers, _ = _setup()
        state.selected_rule = {"rule_id": "RULE-002"}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"implementing_tasks": []}
        MockClient.return_value.__enter__ = MagicMock(return_value=MagicMock(
            get=MagicMock(return_value=mock_response)
        ))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["load_rule_implementing_tasks"]()
        assert state.rule_implementing_tasks == []

    @patch("agent.governance_ui.handlers.common_handlers_audit.httpx.Client")
    def test_api_failure(self, MockClient):
        _, state, triggers, _ = _setup()
        state.selected_rule = {"id": "RULE-001"}

        mock_response = MagicMock()
        mock_response.status_code = 500
        MockClient.return_value.__enter__ = MagicMock(return_value=MagicMock(
            get=MagicMock(return_value=mock_response)
        ))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["load_rule_implementing_tasks"]()
        assert state.rule_implementing_tasks == []

    @patch("agent.governance_ui.handlers.common_handlers_audit.httpx.Client")
    def test_exception(self, MockClient):
        _, state, triggers, _ = _setup()
        state.selected_rule = {"id": "RULE-001"}
        MockClient.side_effect = Exception("connection refused")

        triggers["load_rule_implementing_tasks"]()
        assert state.rule_implementing_tasks == []
        assert state.rule_implementing_tasks_loading is False


# ── Audit filter reactive handlers ───────────────────────


class TestAuditFilterHandlers:
    def test_entity_type_triggers_reload(self):
        ctrl, state, _, changes = _setup()
        state.active_view = "audit"
        changes["audit_filter_entity_type"](audit_filter_entity_type="rule")
        ctrl.trigger.assert_called_with("load_audit_trail")

    def test_action_type_triggers_reload(self):
        ctrl, state, _, changes = _setup()
        state.active_view = "audit"
        changes["audit_filter_action_type"](audit_filter_action_type="create")
        ctrl.trigger.assert_called_with("load_audit_trail")

    def test_entity_id_triggers_reload(self):
        ctrl, state, _, changes = _setup()
        state.active_view = "audit"
        changes["audit_filter_entity_id"](audit_filter_entity_id="RULE-001")
        ctrl.trigger.assert_called_with("load_audit_trail")

    def test_correlation_id_triggers_reload(self):
        ctrl, state, _, changes = _setup()
        state.active_view = "audit"
        changes["audit_filter_correlation_id"](audit_filter_correlation_id="abc-123")
        ctrl.trigger.assert_called_with("load_audit_trail")

    def test_filter_no_reload_when_not_audit_view(self):
        ctrl, state, _, changes = _setup()
        state.active_view = "sessions"
        calls_before = ctrl.trigger.call_count
        changes["audit_filter_entity_type"](audit_filter_entity_type="task")
        # Should NOT have called ctrl.trigger("load_audit_trail")
        assert ctrl.trigger.call_count == calls_before
