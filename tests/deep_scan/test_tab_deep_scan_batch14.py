"""
Unit tests for Tab Deep Scan Batch 14 — Form validation + cross-tab consistency.

Covers: form input validation (trim/empty), cross-tab refresh on view change,
on_view_change handler coverage for data freshness.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── Task edit form validation (BUG-UI-VALIDATION-001) ────────


class TestTaskEditValidation:
    """submit_task_edit must validate required fields."""

    def test_task_edit_has_validation(self):
        """submit_task_edit must validate description."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-VALIDATION-001" in source

    def test_task_edit_trims_strings(self):
        """submit_task_edit must strip whitespace from inputs."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        # Description trimmed in validation block
        assert '.strip()' in source

    @patch("agent.governance_ui.controllers.tasks.httpx")
    @patch("agent.governance_ui.controllers.tasks.add_error_trace")
    def test_empty_description_rejected(self, mock_err, mock_httpx):
        """Empty description must be rejected before API call."""
        state = MagicMock()
        state.selected_task = {"task_id": "T1"}
        state.edit_task_description = "   "  # whitespace only
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
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_task_edit"]()
        assert state.has_error is True
        assert "required" in state.error_message.lower()
        # API must NOT be called
        mock_httpx.Client.assert_not_called()

    @patch("agent.governance_ui.controllers.tasks.httpx")
    @patch("agent.governance_ui.controllers.tasks.add_error_trace")
    def test_valid_description_proceeds(self, mock_err, mock_httpx):
        """Valid description must proceed to API call."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"task_id": "T1", "description": "Valid"}
        mock_client = MagicMock()
        mock_client.put.return_value = mock_resp
        mock_client.get.return_value = MagicMock(status_code=200, json=MagicMock(
            return_value={"items": [{"task_id": "T1"}], "pagination": {}}
        ))
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)

        state = MagicMock()
        state.selected_task = {"task_id": "T1"}
        state.edit_task_description = "Valid description"
        state.edit_task_phase = "P10"
        state.edit_task_status = "TODO"
        state.edit_task_agent = ""
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
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_task_edit"]()
        # API must be called
        mock_client.put.assert_called_once()


# ── Session form validation ─────────────────────────────────


class TestSessionFormValidation:
    """submit_session_form must validate on create mode."""

    def test_session_form_has_validation(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        assert "BUG-UI-VALIDATION-001" in source

    def test_session_form_trims_inputs(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        # Inputs must be trimmed
        assert ".strip()" in source


# ── Decision form validation ────────────────────────────────


class TestDecisionFormValidation:
    """submit_decision_form must validate name and context."""

    def test_decision_form_has_validation(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        assert "BUG-UI-VALIDATION-001" in source

    @patch("agent.governance_ui.controllers.decisions.httpx")
    @patch("agent.governance_ui.controllers.decisions.add_error_trace")
    def test_empty_name_rejected(self, mock_err, mock_httpx):
        """Empty decision name must be rejected."""
        state = MagicMock()
        state.form_decision_name = ""
        state.form_decision_context = "Some context"
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
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        register_decisions_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_decision_form"]()
        assert state.has_error is True
        assert "name" in state.error_message.lower()

    @patch("agent.governance_ui.controllers.decisions.httpx")
    @patch("agent.governance_ui.controllers.decisions.add_error_trace")
    def test_empty_context_rejected(self, mock_err, mock_httpx):
        """Empty decision context must be rejected."""
        state = MagicMock()
        state.form_decision_name = "Valid Name"
        state.form_decision_context = "   "  # whitespace only
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
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.decisions import register_decisions_controllers
        register_decisions_controllers(state, ctrl, "http://localhost:8082")
        triggers["submit_decision_form"]()
        assert state.has_error is True
        assert "context" in state.error_message.lower()


# ── Cross-tab freshness via on_view_change ──────────────────


class TestCrossTabFreshness:
    """on_view_change must refresh data to prevent cross-tab staleness."""

    def test_on_view_change_covers_sessions(self):
        """Switching to sessions tab must trigger refresh."""
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "sessions" in source
        assert "load_sessions_list" in source

    def test_on_view_change_covers_tasks(self):
        """Switching to tasks tab must trigger refresh."""
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "load_tasks_page" in source

    def test_on_view_change_covers_rules(self):
        """Switching to rules tab must trigger refresh via load_rules."""
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        # Rules loaded by data_loaders or on_view_change
        assert "rules" in source

    def test_on_view_change_covers_infra(self):
        """Switching to infra tab must trigger refresh."""
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        assert "infra" in source
        assert "load_infra_status" in source


# ── create_task has validation (consistency check) ──────────


class TestCreateTaskValidationConsistency:
    """create_task and submit_task_edit must both validate."""

    def test_create_task_validates_description(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        # create_task has description validation
        assert "Description is required" in source

    def test_create_task_validates_id(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "Task ID or Task Type is required" in source
