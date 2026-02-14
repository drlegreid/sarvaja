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

    def test_audit_filter_handlers_in_audit_loaders(self):
        """Per BUG-UI-AUDIT-001: filter handlers moved to audit_loaders.py."""
        import inspect
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "audit_filter_entity_type" in source
        assert "audit_filter_action_type" in source


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
    """Per BUG-UI-AUDIT-001: filter handlers moved to audit_loaders.py.

    The handlers now call load_audit_trail() directly (not ctrl.trigger).
    These tests verify the handlers exist in the correct module.
    """

    def test_entity_type_handler_exists(self):
        import inspect
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "audit_filter_entity_type" in source
        assert "load_audit_trail()" in source

    def test_action_type_handler_exists(self):
        import inspect
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "audit_filter_action_type" in source

    def test_entity_id_handler_exists(self):
        import inspect
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "audit_filter_entity_id" in source

    def test_correlation_id_handler_exists(self):
        import inspect
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "audit_filter_correlation_id" in source

    def test_filter_checks_active_view(self):
        import inspect
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert 'active_view == "audit"' in source
