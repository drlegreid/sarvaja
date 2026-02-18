"""
Unit tests for Tab Deep Scan Batch 2 fixes.

Covers: workflow_loaders, trust, impact, executive, chat, tasks controllers.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import ast
import inspect
from unittest.mock import MagicMock, patch

from agent.governance_ui.state.initial import get_initial_state


# ── Workflow Loaders: os.getenv removed, api_base_url used ──────────


class TestWorkflowLoadersUrl:
    def test_no_os_getenv_usage(self):
        """BUG-WORKFLOW-URL-001: workflow_loaders must not use os.getenv."""
        source = inspect.getsource(
            __import__(
                "agent.governance_ui.controllers.workflow_loaders",
                fromlist=["register_workflow_loader_controllers"],
            )
        )
        assert "os.getenv" not in source

    def test_no_os_import(self):
        """workflow_loaders should not import os at all."""
        from agent.governance_ui.controllers import workflow_loaders

        source = inspect.getsource(workflow_loaders)
        tree = ast.parse(source)
        imports = [
            n.names[0].name
            for n in ast.walk(tree)
            if isinstance(n, ast.Import)
        ]
        assert "os" not in imports

    @patch("agent.governance_ui.controllers.workflow_loaders.httpx")
    def test_trigger_uses_api_base_url(self, mock_httpx):
        """Workflow trigger must use api_base_url parameter."""
        from agent.governance_ui.controllers.workflow_loaders import (
            register_workflow_loader_controllers,
        )

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_decorator(name):
            def wrapper(fn):
                triggers[name] = fn
                return fn
            return wrapper

        ctrl.trigger = MagicMock(side_effect=trigger_decorator)

        with patch(
            "agent.governance_ui.controllers.workflow_loaders.run_compliance_checks",
            side_effect=ImportError("not available"),
            create=True,
        ):
            register_workflow_loader_controllers(state, ctrl, "http://test:9999")

        # Mock responses for the two API calls
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"items": []}
        mock_httpx.get.return_value = resp

        triggers["load_workflow_status"]()

        # Should call http://test:9999, not localhost:8082
        calls = [str(c) for c in mock_httpx.get.call_args_list]
        for call in calls:
            assert "test:9999" in call


class TestWorkflowLoadersTrace:
    def test_has_add_error_trace_import(self):
        """workflow_loaders should import add_error_trace."""
        from agent.governance_ui.controllers import workflow_loaders

        source = inspect.getsource(workflow_loaders)
        assert "add_error_trace" in source

    def test_has_add_api_trace_import(self):
        """workflow_loaders should import add_api_trace."""
        from agent.governance_ui.controllers import workflow_loaders

        source = inspect.getsource(workflow_loaders)
        assert "add_api_trace" in source


# ── Trust: select_agent trace + close handler ────────────────────────


class TestTrustSelectAgentTrace:
    def test_select_agent_has_trace(self):
        """select_agent should trace API calls for agent sessions."""
        from agent.governance_ui.controllers import trust

        source = inspect.getsource(trust)
        assert "add_api_trace" in source
        assert "Load agent sessions failed" in source


class TestTrustBackButton:
    def test_agent_detail_uses_close_handler(self):
        """Agent detail back button should use trigger('close_agent_detail')."""
        from agent.governance_ui.views.trust import agent_detail

        source = inspect.getsource(agent_detail)
        assert "trigger('close_agent_detail')" in source
        # Should NOT have raw state manipulation
        assert 'show_agent_detail = false; selected_agent = null' not in source


# ── State: missing variables added ───────────────────────────────────


class TestStateNewVars:
    def test_trust_history_in_state(self):
        """trust_history must be in initial state."""
        state = get_initial_state()
        assert "trust_history" in state
        assert state["trust_history"] == []

    def test_show_agent_registration_in_state(self):
        """show_agent_registration must be in initial state."""
        state = get_initial_state()
        assert "show_agent_registration" in state
        assert state["show_agent_registration"] is False

    def test_dependency_overview_in_state(self):
        """dependency_overview must be in initial state for Impact tab."""
        state = get_initial_state()
        assert "dependency_overview" in state
        assert state["dependency_overview"] is None

    def test_edit_task_mode_in_state(self):
        """edit_task_mode must be in initial state."""
        state = get_initial_state()
        assert "edit_task_mode" in state
        assert state["edit_task_mode"] is False

    def test_edit_task_description_in_state(self):
        """edit_task_description must be in initial state."""
        state = get_initial_state()
        assert "edit_task_description" in state
        assert state["edit_task_description"] == ""

    def test_edit_task_phase_in_state(self):
        """edit_task_phase must be in initial state."""
        state = get_initial_state()
        assert "edit_task_phase" in state
        assert state["edit_task_phase"] == "P10"

    def test_edit_task_status_in_state(self):
        """edit_task_status must be in initial state."""
        state = get_initial_state()
        assert "edit_task_status" in state
        assert state["edit_task_status"] == "TODO"

    def test_edit_task_agent_in_state(self):
        """edit_task_agent must be in initial state."""
        state = get_initial_state()
        assert "edit_task_agent" in state
        assert state["edit_task_agent"] == ""


# ── Executive: api_base_url parameter ────────────────────────────────


class TestExecutiveApiUrl:
    def test_accepts_api_base_url_parameter(self):
        """get_executive_report should accept api_base_url parameter."""
        from agent.governance_ui.data_access.executive import get_executive_report

        sig = inspect.signature(get_executive_report)
        assert "api_base_url" in sig.parameters

    @patch("httpx.Client")
    def test_uses_api_base_url_when_provided(self, mock_client_cls):
        """get_executive_report should use provided api_base_url."""
        from agent.governance_ui.data_access.executive import get_executive_report

        mock_client = MagicMock()
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"sections": [], "overall_status": "ok"}
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        get_executive_report(api_base_url="http://test:1234")

        mock_client_cls.assert_called_once_with(
            base_url="http://test:1234", timeout=15.0
        )

    def test_no_module_level_api_constant(self):
        """No module-level _API_BASE_URL constant should exist."""
        from agent.governance_ui.data_access import executive

        assert not hasattr(executive, "_API_BASE_URL")


# ── Chat: trace calls added ──────────────────────────────────────────


class TestChatTraces:
    def test_has_trace_imports(self):
        """chat.py should import trace functions."""
        from agent.governance_ui.controllers import chat

        source = inspect.getsource(chat)
        assert "add_api_trace" in source
        assert "add_error_trace" in source

    def test_send_chat_has_trace(self):
        """send_chat_message handler should trace API calls."""
        from agent.governance_ui.controllers import chat

        source = inspect.getsource(chat)
        assert "Chat send failed" in source

    def test_file_content_has_trace(self):
        """load_file_content handler should trace errors."""
        from agent.governance_ui.controllers import chat

        source = inspect.getsource(chat)
        assert "Load file failed" in source

    def test_task_execution_has_trace(self):
        """load_task_execution handler should trace errors."""
        from agent.governance_ui.controllers import chat

        source = inspect.getsource(chat)
        assert "Load execution failed" in source


# ── Tasks: close_task_detail resets edit state ───────────────────────


class TestTasksCloseHandler:
    def test_close_resets_edit_state(self):
        """close_task_detail should reset edit_task_* state vars."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def trigger_decorator(name):
            def wrapper(fn):
                triggers[name] = fn
                return fn
            return wrapper

        ctrl.trigger = MagicMock(side_effect=trigger_decorator)

        state.tasks = []
        state.active_view = "tasks"
        state.tasks_page = 1
        state.tasks_per_page = 20
        state.tasks_pagination = {}

        register_tasks_controllers(state, ctrl, "http://localhost:8082")

        triggers["close_task_detail"]()

        assert state.edit_task_mode is False
        assert state.edit_task_description == ""
        assert state.edit_task_body == ""
        assert state.show_task_detail is False
        assert state.task_execution_log == []
        assert state.nav_source_view is None

    def test_back_button_uses_trigger(self):
        """Task detail back button should use trigger('close_task_detail')."""
        from agent.governance_ui.views.tasks import detail

        source = inspect.getsource(detail)
        assert "trigger('close_task_detail')" in source
        # Should NOT have the old inline state manipulation
        assert "nav_source_label = null" not in source
