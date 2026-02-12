"""
Unit tests for Task Navigation Controllers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/tasks_navigation.py.
Tests: register_tasks_navigation — navigate_to_task, navigate_back_to_source.
"""

from unittest.mock import MagicMock, patch

from agent.governance_ui.controllers.tasks_navigation import (
    register_tasks_navigation,
)


def _setup(tasks=None, sessions=None, rules=None):
    """Create mock ctrl + state, register handlers, return internals."""
    ctrl = MagicMock()
    state = MagicMock()

    # Set default lists
    state.tasks = tasks or []
    state.sessions = sessions or []
    state.rules = rules or []

    triggers = {}

    def trigger_decorator(name):
        def wrapper(fn):
            triggers[name] = fn
            return fn
        return wrapper

    ctrl.trigger = MagicMock(side_effect=trigger_decorator)

    register_tasks_navigation(state, ctrl, "http://localhost:8082")

    return ctrl, state, triggers


# ── Registration ─────────────────────────────────────────


class TestRegistration:
    def test_registers_triggers(self):
        _, _, triggers = _setup()
        assert "navigate_to_task" in triggers
        assert "navigate_back_to_source" in triggers


# ── navigate_to_task ─────────────────────────────────────


class TestNavigateToTask:
    def test_empty_task_id_returns(self):
        _, state, triggers = _setup()
        state.active_view = "sessions"  # pre-set
        triggers["navigate_to_task"](None)
        # Should return early without changing active_view
        assert state.active_view == "sessions"

    def test_switches_to_tasks_view(self):
        _, state, triggers = _setup()
        triggers["navigate_to_task"]("T-001")
        assert state.active_view == "tasks"
        assert state.show_session_detail is False

    def test_captures_source_navigation(self):
        _, state, triggers = _setup()
        triggers["navigate_to_task"]("T-001", source_view="sessions",
                                     source_id="S-001", source_label="Back")
        assert state.nav_source_view == "sessions"
        assert state.nav_source_id == "S-001"
        assert state.nav_source_label == "Back"

    def test_clears_source_when_no_source(self):
        _, state, triggers = _setup()
        triggers["navigate_to_task"]("T-001")
        assert state.nav_source_view is None
        assert state.nav_source_id is None

    def test_default_source_label(self):
        _, state, triggers = _setup()
        triggers["navigate_to_task"]("T-001", source_view="rules", source_id="R-1")
        assert state.nav_source_label == "Back to rules"

    def test_finds_task_in_list_by_task_id(self):
        tasks = [{"task_id": "T-001", "name": "Task 1"}]
        _, state, triggers = _setup(tasks=tasks)
        triggers["navigate_to_task"]("T-001")
        assert state.selected_task == {"task_id": "T-001", "name": "Task 1"}
        assert state.show_task_detail is True

    def test_finds_task_in_list_by_id(self):
        tasks = [{"id": "T-002", "name": "Task 2"}]
        _, state, triggers = _setup(tasks=tasks)
        triggers["navigate_to_task"]("T-002")
        assert state.selected_task == {"id": "T-002", "name": "Task 2"}

    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_loads_from_api_when_not_in_list(self, MockClient):
        _, state, triggers = _setup(tasks=[])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"task_id": "T-API", "name": "From API"}
        MockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(return_value=mock_response))
        )
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["navigate_to_task"]("T-API")
        assert state.selected_task == {"task_id": "T-API", "name": "From API"}
        assert state.show_task_detail is True

    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_api_not_found(self, MockClient):
        _, state, triggers = _setup(tasks=[])

        mock_response = MagicMock()
        mock_response.status_code = 404
        MockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(return_value=mock_response))
        )
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["navigate_to_task"]("T-MISSING")
        assert state.error_message == "Task T-MISSING not found"

    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_api_exception(self, MockClient):
        _, state, triggers = _setup(tasks=[])
        MockClient.side_effect = Exception("timeout")

        triggers["navigate_to_task"]("T-ERR")
        assert state.error_message == "Failed to load task T-ERR"


# ── navigate_back_to_source ──────────────────────────────


class TestNavigateBackToSource:
    def test_clears_task_detail(self):
        _, state, triggers = _setup()
        state.nav_source_view = None
        state.nav_source_id = None
        triggers["navigate_back_to_source"]()
        assert state.show_task_detail is False
        assert state.selected_task is None

    def test_clears_nav_context(self):
        _, state, triggers = _setup()
        state.nav_source_view = "sessions"
        state.nav_source_id = "S-001"
        state.sessions = []
        triggers["navigate_back_to_source"]()
        assert state.nav_source_view is None
        assert state.nav_source_id is None
        assert state.nav_source_label is None

    def test_navigates_to_session(self):
        sessions = [{"session_id": "S-001", "name": "Session 1"}]
        _, state, triggers = _setup(sessions=sessions)
        state.nav_source_view = "sessions"
        state.nav_source_id = "S-001"
        triggers["navigate_back_to_source"]()
        assert state.active_view == "sessions"
        assert state.selected_session == {"session_id": "S-001", "name": "Session 1"}
        assert state.show_session_detail is True

    def test_navigates_to_rules(self):
        rules = [{"rule_id": "R-001", "name": "Rule 1"}]
        _, state, triggers = _setup(rules=rules)
        state.nav_source_view = "rules"
        state.nav_source_id = "R-001"
        triggers["navigate_back_to_source"]()
        assert state.active_view == "rules"
        assert state.selected_rule == {"rule_id": "R-001", "name": "Rule 1"}
        assert state.show_rule_detail is True

    def test_navigates_to_generic_view(self):
        _, state, triggers = _setup()
        state.nav_source_view = "agents"
        state.nav_source_id = None
        triggers["navigate_back_to_source"]()
        assert state.active_view == "agents"

    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_loads_session_from_api(self, MockClient):
        _, state, triggers = _setup(sessions=[])
        state.nav_source_view = "sessions"
        state.nav_source_id = "S-API"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"session_id": "S-API"}
        MockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(return_value=mock_response))
        )
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["navigate_back_to_source"]()
        assert state.selected_session == {"session_id": "S-API"}
        assert state.show_session_detail is True
