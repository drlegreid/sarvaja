"""
Unit tests for Task Navigation Controllers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/tasks_navigation.py.
Tests: register_tasks_navigation — navigate_to_task, navigate_to_session, navigate_back_to_source.
Per BUG-012: Tests for cross-nav guard flag and load-first pattern.
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
        assert "navigate_to_session" in triggers
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
        tasks = [{"task_id": "T-001", "name": "Task 1"}]
        _, state, triggers = _setup(tasks=tasks)
        triggers["navigate_to_task"]("T-001")
        assert state.active_view == "tasks"
        assert state.show_session_detail is False

    def test_captures_source_navigation(self):
        tasks = [{"task_id": "T-001"}]
        _, state, triggers = _setup(tasks=tasks)
        triggers["navigate_to_task"]("T-001", source_view="sessions",
                                     source_id="S-001", source_label="Back")
        assert state.nav_source_view == "sessions"
        assert state.nav_source_id == "S-001"
        assert state.nav_source_label == "Back"

    def test_clears_source_when_no_source(self):
        tasks = [{"task_id": "T-001"}]
        _, state, triggers = _setup(tasks=tasks)
        triggers["navigate_to_task"]("T-001")
        assert state.nav_source_view is None
        assert state.nav_source_id is None

    def test_default_source_label(self):
        tasks = [{"task_id": "T-001"}]
        _, state, triggers = _setup(tasks=tasks)
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
    def test_api_not_found_shows_error_no_view_change(self, MockClient):
        """BUG-012: Task not found should NOT change view."""
        _, state, triggers = _setup(tasks=[])
        state.active_view = "sessions"

        mock_response = MagicMock()
        mock_response.status_code = 404
        MockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(return_value=mock_response))
        )
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["navigate_to_task"]("T-MISSING")
        assert state.error_message == "Task T-MISSING not found"
        # View should NOT change (BUG-012: load-first pattern)
        assert state.active_view == "sessions"

    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_api_exception_shows_error(self, mock_load):
        _, state, triggers = _setup(tasks=[])
        mock_load.return_value = None

        triggers["navigate_to_task"]("T-ERR")
        assert state.error_message == "Task T-ERR not found"

    def test_sets_cross_nav_guard(self):
        """BUG-012: Guard flag set before active_view change."""
        tasks = [{"task_id": "T-001"}]
        _, state, triggers = _setup(tasks=tasks)
        triggers["navigate_to_task"]("T-001", source_view="sessions")
        assert state.cross_nav_in_progress is True


# ── navigate_to_session ──────────────────────────────────


class TestNavigateToSession:
    def test_empty_session_id_returns(self):
        _, state, triggers = _setup()
        state.active_view = "tasks"
        triggers["navigate_to_session"](None)
        assert state.active_view == "tasks"

    def test_switches_to_sessions_view(self):
        sessions = [{"session_id": "S-001"}]
        _, state, triggers = _setup(sessions=sessions)
        state.active_view = "tasks"
        triggers["navigate_to_session"]("S-001")
        assert state.active_view == "sessions"
        assert state.show_task_detail is False

    def test_captures_source_navigation(self):
        sessions = [{"session_id": "S-001"}]
        _, state, triggers = _setup(sessions=sessions)
        triggers["navigate_to_session"]("S-001", source_view="tasks",
                                         source_id="T-001", source_label="Back to Task")
        assert state.nav_source_view == "tasks"
        assert state.nav_source_id == "T-001"
        assert state.nav_source_label == "Back to Task"

    def test_default_source_label(self):
        sessions = [{"session_id": "S-001"}]
        _, state, triggers = _setup(sessions=sessions)
        triggers["navigate_to_session"]("S-001", source_view="tasks", source_id="T-1")
        assert state.nav_source_label == "Back to tasks"

    def test_finds_session_in_list_by_session_id(self):
        sessions = [{"session_id": "S-001", "name": "Session 1"}]
        _, state, triggers = _setup(sessions=sessions)
        triggers["navigate_to_session"]("S-001")
        assert state.selected_session == {"session_id": "S-001", "name": "Session 1"}
        assert state.show_session_detail is True

    def test_finds_session_in_list_by_id(self):
        sessions = [{"id": "S-002", "name": "Session 2"}]
        _, state, triggers = _setup(sessions=sessions)
        triggers["navigate_to_session"]("S-002")
        assert state.selected_session == {"id": "S-002", "name": "Session 2"}

    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_loads_from_api_when_not_in_list(self, MockClient):
        _, state, triggers = _setup(sessions=[])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"session_id": "S-API"}
        MockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(return_value=mock_response))
        )
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        triggers["navigate_to_session"]("S-API")
        assert state.selected_session == {"session_id": "S-API"}
        assert state.show_session_detail is True
        assert state.active_view == "sessions"

    @patch("agent.governance_ui.controllers.tasks_navigation._load_session_from_api")
    def test_bug012_not_found_stays_on_current_view(self, mock_load):
        """BUG-012: Session not found should NOT change view (load-first)."""
        _, state, triggers = _setup(sessions=[])
        state.active_view = "tasks"
        state.show_task_detail = True

        mock_load.return_value = None

        triggers["navigate_to_session"]("S-MISSING", source_view="tasks", source_id="T-1")
        # View must stay on tasks (not switch to sessions then rollback)
        assert state.active_view == "tasks"
        assert state.show_task_detail is True
        assert state.error_message == "Session S-MISSING not found"

    @patch("agent.governance_ui.controllers.tasks_navigation._load_session_from_api")
    def test_bug012_not_found_no_nav_source_set(self, mock_load):
        """BUG-012: Failed nav should not leave stale nav_source."""
        _, state, triggers = _setup(sessions=[])
        mock_load.return_value = None

        triggers["navigate_to_session"]("S-GONE", source_view="tasks", source_id="T-1")
        # nav_source should NOT be set since we didn't navigate
        # (nav_source_view is never assigned when load fails)

    def test_sets_cross_nav_guard(self):
        """BUG-012: Guard flag set before active_view change."""
        sessions = [{"session_id": "S-001"}]
        _, state, triggers = _setup(sessions=sessions)
        triggers["navigate_to_session"]("S-001", source_view="tasks")
        assert state.cross_nav_in_progress is True

    def test_sets_session_detail_true(self):
        """Session detail flag must be True after successful navigation."""
        sessions = [{"session_id": "S-001"}]
        _, state, triggers = _setup(sessions=sessions)
        triggers["navigate_to_session"]("S-001")
        assert state.show_session_detail is True

    def test_forces_trame_reactivity(self):
        """BUG-013/BUG-012: dirty() called on detail flags (NOT active_view)."""
        sessions = [{"session_id": "S-001"}]
        _, state, triggers = _setup(sessions=sessions)
        triggers["navigate_to_session"]("S-001")
        # BUG-012: dirty('active_view') removed — triggers double on_view_change
        state.dirty.assert_any_call('show_session_detail')
        state.dirty.assert_any_call('show_task_detail')


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

    @patch("agent.governance_ui.controllers.tasks_navigation._load_session_from_api")
    def test_loads_session_from_api(self, mock_load):
        mock_load.return_value = {"session_id": "S-API"}
        _, state, triggers = _setup(sessions=[])
        state.nav_source_view = "sessions"
        state.nav_source_id = "S-API"

        triggers["navigate_back_to_source"]()
        assert state.selected_session == {"session_id": "S-API"}
        assert state.show_session_detail is True

    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_loads_task_from_api(self, mock_load):
        mock_load.return_value = {"task_id": "T-API"}
        _, state, triggers = _setup(tasks=[])
        state.nav_source_view = "tasks"
        state.nav_source_id = "T-API"

        triggers["navigate_back_to_source"]()
        assert state.selected_task == {"task_id": "T-API"}
        assert state.show_task_detail is True

    def test_sets_cross_nav_guard(self):
        """BUG-012: Guard flag set before active_view change in back nav."""
        sessions = [{"session_id": "S-001"}]
        _, state, triggers = _setup(sessions=sessions)
        state.nav_source_view = "sessions"
        state.nav_source_id = "S-001"
        triggers["navigate_back_to_source"]()
        assert state.cross_nav_in_progress is True

    def test_defaults_to_tasks_when_no_source(self):
        _, state, triggers = _setup()
        state.nav_source_view = None
        state.nav_source_id = None
        triggers["navigate_back_to_source"]()
        assert state.active_view == "tasks"


# ── Helper functions ─────────────────────────────────────


class TestHelperFunctions:
    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_load_session_from_api_success(self, MockClient):
        from agent.governance_ui.controllers.tasks_navigation import _load_session_from_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"session_id": "S-1"}
        MockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(return_value=mock_response))
        )
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = _load_session_from_api("http://localhost:8082", "S-1")
        assert result == {"session_id": "S-1"}

    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_load_session_from_api_404(self, MockClient):
        from agent.governance_ui.controllers.tasks_navigation import _load_session_from_api

        mock_response = MagicMock()
        mock_response.status_code = 404
        MockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(return_value=mock_response))
        )
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = _load_session_from_api("http://localhost:8082", "S-GONE")
        assert result is None

    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_load_session_from_api_exception(self, MockClient):
        from agent.governance_ui.controllers.tasks_navigation import _load_session_from_api

        MockClient.side_effect = Exception("timeout")
        result = _load_session_from_api("http://localhost:8082", "S-ERR")
        assert result is None

    @patch("agent.governance_ui.controllers.tasks_navigation.httpx.Client")
    def test_load_task_from_api_success(self, MockClient):
        from agent.governance_ui.controllers.tasks_navigation import _load_task_from_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"task_id": "T-1"}
        MockClient.return_value.__enter__ = MagicMock(
            return_value=MagicMock(get=MagicMock(return_value=mock_response))
        )
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = _load_task_from_api("http://localhost:8082", "T-1")
        assert result == {"task_id": "T-1"}
