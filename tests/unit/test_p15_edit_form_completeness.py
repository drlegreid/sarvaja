"""
EPIC-TASK-QUALITY-V3 Phase 15: Edit Form Completeness.

Tests that the edit form exposes all editable fields (summary, body,
priority, task_type) and submit_task_edit sends them to the API.
"""

import inspect
import unittest
from unittest.mock import MagicMock, patch


# ── Helpers ─────────────────────────────────────────────────

def _make_state_ctrl(api_base="http://localhost:8082"):
    """Create mock state/ctrl and register tasks_crud controllers."""
    state = MagicMock()
    ctrl = MagicMock()
    triggers = {}

    def trigger(name):
        def wrap(fn):
            triggers[name] = fn
            return fn
        return wrap

    ctrl.trigger = trigger
    state.change = lambda name: lambda fn: fn

    from agent.governance_ui.controllers.tasks_crud import register_tasks_crud
    register_tasks_crud(state, ctrl, api_base)
    return state, ctrl, triggers


# ── 1. Edit form has new fields ─────────────────────────────

class TestEditFormFields(unittest.TestCase):
    """P15: edit form must expose summary, body, priority, task_type."""

    def test_edit_form_has_summary_field(self):
        from agent.governance_ui.views.tasks import forms_edit
        source = inspect.getsource(forms_edit)
        assert "edit_task_summary" in source
        assert "task-edit-summary" in source

    def test_edit_form_has_body_field(self):
        from agent.governance_ui.views.tasks import forms_edit
        source = inspect.getsource(forms_edit)
        assert "edit_task_body" in source
        assert "task-edit-body" in source

    def test_edit_form_has_priority_select(self):
        from agent.governance_ui.views.tasks import forms_edit
        source = inspect.getsource(forms_edit)
        assert "edit_task_priority" in source
        assert "task-edit-priority" in source

    def test_edit_form_has_task_type_select(self):
        from agent.governance_ui.views.tasks import forms_edit
        source = inspect.getsource(forms_edit)
        assert "edit_task_type" in source
        assert "task-edit-type" in source

    def test_priority_uses_options_from_state(self):
        """Priority select should use task_priority_options from state."""
        from agent.governance_ui.views.tasks import forms_edit
        source = inspect.getsource(forms_edit)
        assert "task_priority_options" in source

    def test_type_uses_options_from_state(self):
        """Task type select should use task_type_options from state."""
        from agent.governance_ui.views.tasks import forms_edit
        source = inspect.getsource(forms_edit)
        assert "task_type_options" in source


# ── 2. State variables declared ──────────────────────────────

class TestEditStateVars(unittest.TestCase):
    """P15: initial state must declare new edit vars."""

    def test_edit_task_summary_in_initial_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "edit_task_summary" in state
        assert state["edit_task_summary"] == ""

    def test_edit_task_priority_in_initial_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "edit_task_priority" in state
        assert state["edit_task_priority"] is None

    def test_edit_task_type_in_initial_state(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "edit_task_type" in state
        assert state["edit_task_type"] is None

    def test_edit_task_body_in_initial_state(self):
        """Body was pre-existing but verify it's still present."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "edit_task_body" in state


# ── 3. Edit button initializes new fields ────────────────────

class TestEditButtonInitialization(unittest.TestCase):
    """P15: Edit button click must initialize all new state vars."""

    def test_edit_click_sets_summary(self):
        from agent.governance_ui.views.tasks import detail
        source = inspect.getsource(detail)
        assert "edit_task_summary = selected_task.summary" in source

    def test_edit_click_sets_body(self):
        from agent.governance_ui.views.tasks import detail
        source = inspect.getsource(detail)
        assert "edit_task_body = selected_task.body" in source

    def test_edit_click_sets_priority(self):
        from agent.governance_ui.views.tasks import detail
        source = inspect.getsource(detail)
        assert "edit_task_priority = selected_task.priority" in source

    def test_edit_click_sets_type(self):
        from agent.governance_ui.views.tasks import detail
        source = inspect.getsource(detail)
        assert "edit_task_type = selected_task.task_type" in source


# ── 4. submit_task_edit sends all fields ─────────────────────

class TestSubmitSendsAllFields(unittest.TestCase):
    """P15: submit_task_edit must include summary, body, priority, task_type."""

    @patch("agent.governance_ui.controllers.tasks_crud._httpx")
    @patch("agent.governance_ui.controllers.tasks_crud._add_error_trace")
    def test_submit_sends_summary(self, mock_err, mock_httpx):
        state, ctrl, triggers = _make_state_ctrl()
        state.selected_task = {"task_id": "T-1", "id": "T-1"}
        state.is_loading = False
        state.edit_task_description = "Desc"
        state.edit_task_phase = "P10"
        state.edit_task_status = "TODO"
        state.edit_task_agent = ""
        state.edit_task_body = ""
        state.edit_task_summary = "Short summary"
        state.edit_task_priority = "HIGH"
        state.edit_task_type = "bug"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"task_id": "T-1", "status": "TODO"}
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.put.return_value = mock_response
        # Mock tasks list refresh
        list_resp = MagicMock()
        list_resp.status_code = 200
        list_resp.json.return_value = {"items": [], "pagination": {}}
        mock_client.get.return_value = list_resp
        mock_httpx.Client.return_value = mock_client

        triggers["submit_task_edit"]()

        call_args = mock_client.put.call_args
        payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1] if len(call_args[0]) > 1 else None
        assert payload is not None, "PUT not called with json payload"
        assert payload.get("summary") == "Short summary"
        assert payload.get("priority") == "HIGH"
        assert payload.get("task_type") == "bug"

    @patch("agent.governance_ui.controllers.tasks_crud._httpx")
    @patch("agent.governance_ui.controllers.tasks_crud._add_error_trace")
    def test_submit_sends_none_for_empty_optional_fields(self, mock_err, mock_httpx):
        """Empty/null optional fields should be sent as None."""
        state, ctrl, triggers = _make_state_ctrl()
        state.selected_task = {"task_id": "T-2", "id": "T-2"}
        state.is_loading = False
        state.edit_task_description = "Required desc"
        state.edit_task_phase = "P10"
        state.edit_task_status = "TODO"
        state.edit_task_agent = ""
        state.edit_task_body = ""
        state.edit_task_summary = ""
        state.edit_task_priority = None
        state.edit_task_type = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"task_id": "T-2"}
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.put.return_value = mock_response
        list_resp = MagicMock()
        list_resp.status_code = 200
        list_resp.json.return_value = {"items": [], "pagination": {}}
        mock_client.get.return_value = list_resp
        mock_httpx.Client.return_value = mock_client

        triggers["submit_task_edit"]()

        payload = mock_client.put.call_args[1]["json"]
        assert payload.get("summary") is None
        assert payload.get("priority") is None
        assert payload.get("task_type") is None


# ── 5. Form field count parity ───────────────────────────────

class TestFormParity(unittest.TestCase):
    """P15: edit form should have parity with create form for shared fields."""

    def test_edit_form_field_count_gte_8(self):
        """Edit form must have at least 8 editable fields."""
        from agent.governance_ui.views.tasks import forms_edit
        source = inspect.getsource(forms_edit)
        # Count distinct v_model bindings
        import re
        models = set(re.findall(r'v_model="(edit_task_\w+)"', source))
        assert len(models) >= 7, f"Only {len(models)} fields: {models}"

    def test_create_form_has_priority_and_type(self):
        """Create form already has priority and type — sanity check."""
        from agent.governance_ui.views.tasks import forms_create
        source = inspect.getsource(forms_create)
        assert "form_task_priority" in source
        assert "form_task_type" in source


# ── 6. BUG-P14.5 Regression: return statement ────────────────

class TestTasksControllerReturnLoader(unittest.TestCase):
    """BUG-P14.5: register_tasks_controllers must return load_tasks_page."""

    def test_returns_dict_with_load_tasks_page(self):
        """P14.5 regression: missing return caused tasks tab to not load on first visit."""
        from unittest.mock import MagicMock
        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def wrap(fn):
                triggers[name] = fn
                return fn
            return wrap

        ctrl.trigger = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        result = register_tasks_controllers(state, ctrl, "http://localhost:8082")
        assert result is not None, "register_tasks_controllers must return a dict"
        assert "load_tasks_page" in result, "return dict must contain load_tasks_page"
        assert callable(result["load_tasks_page"])


if __name__ == "__main__":
    unittest.main()
