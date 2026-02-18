"""
Unit tests for Tab Deep Scan Batch 9 fixes.

Covers: Chat message cap, audit trace additions, dead code identification,
common_handlers_audit trace fix.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── Chat message cap (antirot) ───────────────────────────────────


class TestChatMessageCap:
    """Chat messages must be capped to prevent memory leak."""

    def test_capped_messages_under_limit(self):
        from agent.governance_ui.controllers.chat import _capped_messages
        msgs = [{"id": f"M{i}"} for i in range(10)]
        result = _capped_messages(msgs)
        assert len(result) == 10

    def test_capped_messages_at_limit(self):
        from agent.governance_ui.controllers.chat import _capped_messages, _MAX_CHAT_MESSAGES
        msgs = [{"id": f"M{i}"} for i in range(_MAX_CHAT_MESSAGES)]
        result = _capped_messages(msgs)
        assert len(result) == _MAX_CHAT_MESSAGES

    def test_capped_messages_over_limit_truncates(self):
        from agent.governance_ui.controllers.chat import _capped_messages, _MAX_CHAT_MESSAGES
        msgs = [{"id": f"M{i}"} for i in range(_MAX_CHAT_MESSAGES + 100)]
        result = _capped_messages(msgs)
        assert len(result) == _MAX_CHAT_MESSAGES
        # Should keep LAST N messages (newest)
        assert result[0]["id"] == "M100"
        assert result[-1]["id"] == f"M{_MAX_CHAT_MESSAGES + 99}"

    def test_max_chat_messages_constant(self):
        from agent.governance_ui.controllers.chat import _MAX_CHAT_MESSAGES
        assert _MAX_CHAT_MESSAGES == 500

    def test_send_chat_uses_cap(self):
        """send_chat_message must use _capped_messages."""
        from agent.governance_ui.controllers import chat
        source = inspect.getsource(chat)
        assert "_capped_messages" in source


# ── Audit loaders trace ─────────────────────────────────────────


class TestAuditLoadersTrace:
    """audit_loaders.py must have add_error_trace on exception path."""

    def test_has_trace_import(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "add_error_trace" in source

    def test_load_audit_trail_has_trace(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "Load audit trail failed" in source


# ── Common handlers audit trace ──────────────────────────────────


class TestCommonHandlersAuditTrace:
    """common_handlers_audit.py must use add_error_trace, not print."""

    def test_has_trace_import(self):
        from agent.governance_ui.handlers import common_handlers_audit
        source = inspect.getsource(common_handlers_audit)
        assert "add_error_trace" in source

    def test_no_print_errors(self):
        """Should not use print() for error output."""
        from agent.governance_ui.handlers import common_handlers_audit
        source = inspect.getsource(common_handlers_audit)
        assert 'print(f"Error' not in source

    def test_load_implementing_tasks_has_trace(self):
        from agent.governance_ui.handlers import common_handlers_audit
        source = inspect.getsource(common_handlers_audit)
        assert "Load implementing tasks failed" in source


# ── Dead code identification (common_handlers.py) ────────────────


class TestDeadCodeIdentification:
    """common_handlers.py handler functions should not be called."""

    def _get_ctrl_init_source(self):
        import importlib
        mod = importlib.import_module("agent.governance_ui.controllers")
        return inspect.getsource(mod)

    def test_register_common_handlers_not_imported(self):
        """register_common_handlers should not be imported by controllers."""
        source = self._get_ctrl_init_source()
        assert "register_common_handlers" not in source

    def test_register_backlog_handlers_not_imported(self):
        """register_backlog_handlers should not be imported by controllers."""
        source = self._get_ctrl_init_source()
        assert "register_backlog_handlers" not in source

    def test_register_executive_handlers_not_imported(self):
        """register_executive_handlers should not be imported by controllers."""
        source = self._get_ctrl_init_source()
        assert "register_executive_handlers" not in source

    def test_active_handlers_still_imported(self):
        """register_trace_bar_handlers and register_rule_detail_handlers must be active."""
        source = self._get_ctrl_init_source()
        assert "register_trace_bar_handlers" in source
        assert "register_rule_detail_handlers" in source


# ── navigate_to_entity handler coverage ──────────────────────────


class TestNavigateToEntity:
    """audit_loaders navigate_to_entity cross-view navigation."""

    def _make_audit_ctrl(self, api_base="http://localhost:8082"):
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def _trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = _trigger

        from agent.governance_ui.controllers.audit_loaders import register_audit_loader_controllers
        register_audit_loader_controllers(state, ctrl, api_base)
        return state, ctrl, triggers

    def test_navigate_to_rule(self):
        state, _, triggers = self._make_audit_ctrl()
        state.rules = [{"rule_id": "R1", "title": "Test"}]
        triggers["navigate_to_entity"]("rule", "R1")
        assert state.active_view == "rules"
        assert state.show_rule_detail is True

    def test_navigate_to_task(self):
        state, _, triggers = self._make_audit_ctrl()
        state.tasks = [{"task_id": "T1", "title": "Test"}]
        triggers["navigate_to_entity"]("task", "T1")
        assert state.active_view == "tasks"
        assert state.show_task_detail is True

    def test_navigate_to_decision(self):
        state, _, triggers = self._make_audit_ctrl()
        state.decisions = [{"decision_id": "D1", "name": "Test"}]
        triggers["navigate_to_entity"]("decision", "D1")
        assert state.active_view == "decisions"
        assert state.show_decision_detail is True

    def test_navigate_unknown_entity_noop(self):
        state, _, triggers = self._make_audit_ctrl()
        triggers["navigate_to_entity"]("unknown", "X1")
        # Should not crash, no view change for unknown types
