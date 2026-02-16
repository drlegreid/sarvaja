"""TDD Tests: Error clearing + state reset on close across all controllers.

Validates:
1. All mutating operations clear has_error before starting
2. Close handlers reset all associated detail state
3. Agent close clears agent_sessions
4. Rule close clears rule_implementing_tasks
"""
import inspect

from unittest.mock import MagicMock, patch


# --- Decisions Error Clearing ---

class TestDecisionsErrorClearing:
    """decisions.py mutations clear has_error before network calls."""

    def test_submit_decision_form_clears_error(self):
        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        source = inspect.getsource(register_decisions_controllers)
        # has_error = False should appear before is_loading = True in submit
        idx_clear = source.index("submit_decision_form")
        sub = source[idx_clear:]
        idx_has_error = sub.index("has_error = False")
        idx_loading = sub.index("is_loading = True")
        assert idx_has_error < idx_loading

    def test_delete_decision_clears_error(self):
        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        source = inspect.getsource(register_decisions_controllers)
        idx_delete = source.index("delete_decision")
        sub = source[idx_delete:]
        assert "has_error = False" in sub


# --- Rules Error Clearing ---

class TestRulesErrorClearing:
    """rules.py mutations clear has_error before network calls."""

    def test_submit_rule_form_clears_error(self):
        from agent.governance_ui.controllers.rules import register_rules_controllers
        source = inspect.getsource(register_rules_controllers)
        idx_submit = source.index("submit_rule_form")
        sub = source[idx_submit:]
        idx_has_error = sub.index("has_error = False")
        idx_loading = sub.index("is_loading = True")
        assert idx_has_error < idx_loading

    def test_delete_rule_clears_error(self):
        from agent.governance_ui.controllers.rules import register_rules_controllers
        source = inspect.getsource(register_rules_controllers)
        idx_delete = source.index("delete_rule")
        sub = source[idx_delete:]
        assert "has_error = False" in sub


# --- Backlog Error Clearing ---

class TestBacklogErrorClearing:
    """backlog.py mutations clear has_error before network calls."""

    def test_claim_task_clears_error(self):
        from agent.governance_ui.controllers.backlog import register_backlog_controllers
        source = inspect.getsource(register_backlog_controllers)
        # Find claim_task, check has_error = False appears after validation
        idx_claim = source.index("def claim_task")
        sub = source[idx_claim:]
        assert "has_error = False" in sub

    def test_complete_task_clears_error(self):
        from agent.governance_ui.controllers.backlog import register_backlog_controllers
        source = inspect.getsource(register_backlog_controllers)
        idx_complete = source.index("def complete_task")
        sub = source[idx_complete:]
        assert "has_error = False" in sub


# --- Trust Error Clearing ---

class TestTrustErrorClearing:
    """trust.py mutations clear has_error before network calls."""

    def test_register_agent_clears_error(self):
        from agent.governance_ui.controllers.trust import register_trust_controllers
        source = inspect.getsource(register_trust_controllers)
        idx_reg = source.index("def register_agent")
        sub = source[idx_reg:]
        assert "has_error = False" in sub


# --- Close Handler State Reset ---

class TestCloseRuleDetailReset:
    """close_rule_detail resets all associated state."""

    def test_clears_rule_implementing_tasks(self):
        from agent.governance_ui.controllers.rules import register_rules_controllers
        source = inspect.getsource(register_rules_controllers)
        idx = source.index("close_rule_detail")
        sub = source[idx:idx + 300]
        assert "rule_implementing_tasks = []" in sub

    def test_clears_rule_implementing_tasks_loading(self):
        from agent.governance_ui.controllers.rules import register_rules_controllers
        source = inspect.getsource(register_rules_controllers)
        idx = source.index("close_rule_detail")
        sub = source[idx:idx + 300]
        assert "rule_implementing_tasks_loading = False" in sub


class TestCloseAgentDetailReset:
    """close_agent_detail resets all associated state."""

    def test_clears_agent_sessions(self):
        from agent.governance_ui.controllers.trust import register_trust_controllers
        source = inspect.getsource(register_trust_controllers)
        idx = source.index("close_agent_detail")
        sub = source[idx:idx + 300]
        assert "agent_sessions = []" in sub

    def test_behavioral_close_resets_sessions(self):
        """Behavioral: calling close_agent_detail actually clears agent_sessions."""
        state = MagicMock()
        ctrl = MagicMock()
        setters = {}

        def fake_set(name):
            def decorator(fn):
                setters[name] = fn
                return fn
            return decorator
        ctrl.set = fake_set
        ctrl.trigger = fake_set

        from agent.governance_ui.controllers.trust import register_trust_controllers
        register_trust_controllers(state, ctrl, "http://test:8082")

        state.agent_sessions = [{"session_id": "S-1"}]
        setters["close_agent_detail"]()
        assert state.agent_sessions == []
        assert state.show_agent_detail is False
