"""
Unit tests for Tab Deep Scan Batch 19 — Rules/Tasks/Agents tab integrity.

Covers: rules form validation, rules_headers in state, tasks_headers in state,
tasks pagination page reset on delete, rules validation consistency.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import math
from unittest.mock import MagicMock, patch


# ── Rules form validation (BUG-UI-VALIDATION-001) ──────────────────────


class TestRulesFormValidation:
    """submit_rule_form must validate required fields."""

    def test_source_has_validation_marker(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "BUG-UI-VALIDATION-001" in source

    def test_validates_rule_id(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "Rule ID is required" in source

    def test_validates_rule_name(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "Rule name is required" in source

    def test_validates_directive(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "Rule directive is required" in source

    @patch("agent.governance_ui.controllers.rules.httpx")
    @patch("agent.governance_ui.controllers.rules.add_error_trace")
    def test_empty_id_rejected(self, mock_err, mock_httpx):
        """Empty rule ID must be rejected before API call."""
        state = MagicMock()
        state.form_rule_id = ""
        state.form_rule_title = "Test"
        state.form_rule_directive = "Do stuff"
        state.has_error = False
        state.is_loading = False
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        ctrl.set = lambda name: lambda fn: fn
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.rules import register_rules_controllers
        register_rules_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_rule_form"]()
        assert state.has_error is True
        assert "id" in state.error_message.lower()
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.rules.httpx")
    @patch("agent.governance_ui.controllers.rules.add_error_trace")
    def test_empty_name_rejected(self, mock_err, mock_httpx):
        """Empty rule name must be rejected."""
        state = MagicMock()
        state.form_rule_id = "TEST-001"
        state.form_rule_title = "   "
        state.form_rule_directive = "Do stuff"
        state.has_error = False
        state.is_loading = False
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        ctrl.set = lambda name: lambda fn: fn
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.rules import register_rules_controllers
        register_rules_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_rule_form"]()
        assert state.has_error is True
        assert "name" in state.error_message.lower()

    @patch("agent.governance_ui.controllers.rules.httpx")
    @patch("agent.governance_ui.controllers.rules.add_error_trace")
    def test_empty_directive_rejected(self, mock_err, mock_httpx):
        """Empty directive must be rejected."""
        state = MagicMock()
        state.form_rule_id = "TEST-001"
        state.form_rule_title = "Test Rule"
        state.form_rule_directive = ""
        state.has_error = False
        state.is_loading = False
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        ctrl.set = lambda name: lambda fn: fn
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.rules import register_rules_controllers
        register_rules_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_rule_form"]()
        assert state.has_error is True
        assert "directive" in state.error_message.lower()


# ── Headers in state (pattern consistency) ──────────────────────────────


class TestHeadersInState:
    """All tab headers must be declared in initial state."""

    def test_rules_headers_in_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "rules_headers" in state

    def test_tasks_headers_in_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "tasks_headers" in state

    def test_sessions_headers_in_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "sessions_headers" in state

    def test_projects_headers_in_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "projects_headers" in state

    def test_rules_headers_has_id_key(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        keys = [h["key"] for h in state["rules_headers"]]
        assert "id" in keys

    def test_tasks_headers_has_task_id_key(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        keys = [h["key"] for h in state["tasks_headers"]]
        assert "task_id" in keys

    def test_rules_headers_match_view(self):
        """State rules headers keys must appear in rules_view.py."""
        from agent.governance_ui.state.initial import get_initial_state
        from agent.governance_ui.views import rules_view
        state = get_initial_state()
        source = inspect.getsource(rules_view)
        for h in state["rules_headers"]:
            assert h["key"] in source, f"Header key '{h['key']}' not in rules_view.py"

    def test_tasks_headers_match_view(self):
        """State tasks headers keys must appear in tasks/list.py."""
        from agent.governance_ui.state.initial import get_initial_state
        from agent.governance_ui.views.tasks import list as tlist
        state = get_initial_state()
        source = inspect.getsource(tlist)
        for h in state["tasks_headers"]:
            assert h["key"] in source, f"Header key '{h['key']}' not in tasks/list.py"


# ── Tasks pagination page reset on delete (BUG-UI-PAGINATION-003) ──────


class TestTasksPaginationPageResetOnDelete:
    """Deleting last task on page must reset to previous page."""

    def test_source_has_pagination_fix(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-PAGINATION-003" in source

    def test_page_reset_logic_exists(self):
        """Delete handler must check for empty page and go back."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        # Must have logic to decrease page when empty
        assert "tasks_page - 1" in source or "tasks_page -= 1" in source


# ── Validation consistency across all CRUD controllers ──────────────────


class TestValidationConsistencyAcrossTabs:
    """All form submit handlers must have BUG-UI-VALIDATION-001."""

    def test_sessions_has_validation(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "BUG-UI-VALIDATION-001" in source

    def test_decisions_has_validation(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "BUG-UI-VALIDATION-001" in source

    def test_rules_has_validation(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "BUG-UI-VALIDATION-001" in source

    def test_tasks_has_validation(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-VALIDATION-001" in source


# ── Double-click guard consistency ──────────────────────────────────────


class TestDoubleClickGuardConsistency:
    """All destructive handlers must have BUG-UI-DOUBLECLICK-001."""

    def test_sessions_has_guard(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert source.count("BUG-UI-DOUBLECLICK-001") >= 2  # submit + delete

    def test_decisions_has_guard(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert source.count("BUG-UI-DOUBLECLICK-001") >= 2

    def test_rules_has_guard(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert source.count("BUG-UI-DOUBLECLICK-001") >= 2

    def test_tasks_has_guard(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert source.count("BUG-UI-DOUBLECLICK-001") >= 3  # submit + delete + create
