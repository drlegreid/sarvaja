"""
Tests for workspace controller CRUD triggers.

Tests for agent/governance_ui/controllers/workspaces.py.
"""

import inspect
from unittest.mock import MagicMock, patch

import pytest


_SAMPLE_WS = {
    "workspace_id": "WS-TEST1",
    "name": "Test Workspace",
    "workspace_type": "generic",
    "project_id": None,
    "description": "A test workspace",
    "status": "active",
    "created_at": "2026-03-19T10:00:00",
    "agent_ids": [],
    "default_rules": [],
    "capabilities": [],
    "icon": "mdi-folder",
    "color": "#64748b",
}

_SAMPLE_WS_LIST = [_SAMPLE_WS]

_SAMPLE_TYPES = [
    {"type_id": "generic", "name": "Generic"},
    {"type_id": "governance", "name": "Governance"},
]


def _make_state():
    """Create a mock state object with workspace state variables."""
    state = MagicMock()
    state.workspaces = []
    state.selected_workspace = None
    state.show_workspace_detail = False
    state.workspaces_loading = False
    state.workspace_types = []
    state.workspace_type_options = []
    state.show_workspace_form = False
    state.form_workspace_name = ""
    state.form_workspace_type = "generic"
    state.form_workspace_description = ""
    state.form_workspace_project_id = ""
    state.edit_workspace_mode = False
    state.edit_workspace_name = ""
    state.edit_workspace_description = ""
    state.edit_workspace_status = "active"
    state.show_workspace_delete_confirm = False
    state.is_loading = False
    state.has_error = False
    state.error_message = ""
    state.status_message = ""
    state.agent_capabilities = []
    state.agent_capabilities_loading = False
    return state


def _make_ctrl():
    """Create a mock ctrl that captures triggers."""
    ctrl = MagicMock()
    _triggers = {}

    def trigger_decorator(name):
        def decorator(fn):
            _triggers[name] = fn
            return fn
        return decorator

    ctrl.trigger = trigger_decorator
    ctrl._triggers = _triggers
    return ctrl


class TestWorkspaceControllerRegistration:
    """Verify controller registration returns expected loaders."""

    def test_register_returns_dict(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        result = register_workspace_controllers(state, ctrl, "http://localhost:8082")
        assert isinstance(result, dict)
        assert "load_workspaces" in result
        assert callable(result["load_workspaces"])

    def test_registers_all_triggers(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        expected_triggers = [
            "load_workspaces",
            "select_workspace",
            "show_create_workspace_form",
            "cancel_workspace_form",
            "create_workspace",
            "edit_workspace",
            "cancel_workspace_edit",
            "submit_workspace_edit",
            "confirm_delete_workspace",
            "cancel_delete_workspace",
            "delete_workspace",
            "load_agent_capabilities",
        ]
        for trigger_name in expected_triggers:
            assert trigger_name in ctrl._triggers, f"Missing trigger: {trigger_name}"

    def test_register_function_has_docstring(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        assert register_workspace_controllers.__doc__ is not None


class TestLoadWorkspaces:
    """Tests for the load_workspaces trigger."""

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    @patch("agent.governance_ui.controllers.workspaces.add_api_trace")
    def test_load_workspaces_success(self, mock_trace, mock_client_cls):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        ws_resp = MagicMock(status_code=200)
        ws_resp.json.return_value = _SAMPLE_WS_LIST
        types_resp = MagicMock(status_code=200)
        types_resp.json.return_value = _SAMPLE_TYPES
        mock_client.get.side_effect = [ws_resp, types_resp]

        result = register_workspace_controllers(state, ctrl, "http://localhost:8082")
        result["load_workspaces"]()

        assert state.workspaces == _SAMPLE_WS_LIST
        assert state.workspace_types == _SAMPLE_TYPES
        assert state.workspace_type_options == ["generic", "governance"]
        assert state.workspaces_loading is False

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    @patch("agent.governance_ui.controllers.workspaces.add_api_trace")
    def test_load_workspaces_api_error(self, mock_trace, mock_client_cls):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MagicMock(status_code=500)

        result = register_workspace_controllers(state, ctrl, "http://localhost:8082")
        result["load_workspaces"]()

        assert state.workspaces == []
        assert state.workspaces_loading is False


class TestSelectWorkspace:
    """Tests for the select_workspace trigger."""

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    @patch("agent.governance_ui.controllers.workspaces.add_api_trace")
    def test_select_workspace_success(self, mock_trace, mock_client_cls):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = MagicMock(
            status_code=200, json=MagicMock(return_value=_SAMPLE_WS)
        )

        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        ctrl._triggers["select_workspace"]("WS-TEST1")

        assert state.selected_workspace == _SAMPLE_WS
        assert state.show_workspace_detail is True
        assert state.edit_workspace_mode is False

    def test_select_workspace_empty_id_noop(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        ctrl._triggers["select_workspace"](None)
        assert state.selected_workspace is None


class TestCreateWorkspace:
    """Tests for workspace creation flow."""

    def test_show_create_form_sets_state(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        ctrl._triggers["show_create_workspace_form"]()

        assert state.show_workspace_form is True
        assert state.form_workspace_name == ""
        assert state.form_workspace_type == "generic"

    def test_cancel_workspace_form_closes(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.show_workspace_form = True
        ctrl._triggers["cancel_workspace_form"]()

        assert state.show_workspace_form is False

    def test_create_workspace_requires_name(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.form_workspace_name = ""
        ctrl._triggers["create_workspace"]()

        assert state.has_error is True
        assert "name" in state.error_message.lower()

    def test_create_workspace_skips_when_loading(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.is_loading = True
        state.form_workspace_name = "Test"
        ctrl._triggers["create_workspace"]()
        # Should not have set has_error (skipped entirely)
        assert state.has_error is False

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    @patch("agent.governance_ui.controllers.workspaces.add_api_trace")
    def test_create_workspace_success(self, mock_trace, mock_client_cls):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        # POST create returns 201, then GET workspaces + types for refresh
        create_resp = MagicMock(status_code=201)
        create_resp.json.return_value = _SAMPLE_WS
        ws_list_resp = MagicMock(status_code=200)
        ws_list_resp.json.return_value = _SAMPLE_WS_LIST
        types_resp = MagicMock(status_code=200)
        types_resp.json.return_value = _SAMPLE_TYPES
        mock_client.post.return_value = create_resp
        mock_client.get.side_effect = [ws_list_resp, types_resp]

        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.form_workspace_name = "Test Workspace"
        state.form_workspace_type = "generic"
        ctrl._triggers["create_workspace"]()

        assert state.show_workspace_form is False
        assert state.status_message == "Workspace created"
        assert state.is_loading is False


class TestEditWorkspace:
    """Tests for workspace edit flow."""

    def test_edit_workspace_populates_fields(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.selected_workspace = _SAMPLE_WS
        ctrl._triggers["edit_workspace"]()

        assert state.edit_workspace_mode is True
        assert state.edit_workspace_name == "Test Workspace"
        assert state.edit_workspace_description == "A test workspace"
        assert state.edit_workspace_status == "active"

    def test_cancel_workspace_edit(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.edit_workspace_mode = True
        ctrl._triggers["cancel_workspace_edit"]()

        assert state.edit_workspace_mode is False

    def test_submit_edit_requires_name(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.selected_workspace = _SAMPLE_WS
        state.edit_workspace_name = "  "
        ctrl._triggers["submit_workspace_edit"]()

        assert state.has_error is True
        assert "name" in state.error_message.lower()

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    @patch("agent.governance_ui.controllers.workspaces.add_api_trace")
    def test_submit_edit_success(self, mock_trace, mock_client_cls):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        updated_ws = {**_SAMPLE_WS, "name": "Renamed"}
        put_resp = MagicMock(status_code=200)
        put_resp.json.return_value = updated_ws
        ws_list_resp = MagicMock(status_code=200)
        ws_list_resp.json.return_value = [updated_ws]
        types_resp = MagicMock(status_code=200)
        types_resp.json.return_value = _SAMPLE_TYPES
        mock_client.put.return_value = put_resp
        mock_client.get.side_effect = [ws_list_resp, types_resp]

        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.selected_workspace = _SAMPLE_WS
        state.edit_workspace_name = "Renamed"
        state.edit_workspace_description = "Updated desc"
        state.edit_workspace_status = "active"
        ctrl._triggers["submit_workspace_edit"]()

        assert state.selected_workspace == updated_ws
        assert state.edit_workspace_mode is False
        assert state.status_message == "Workspace updated"
        assert state.is_loading is False


class TestDeleteWorkspace:
    """Tests for workspace delete flow."""

    def test_confirm_delete_shows_dialog(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        ctrl._triggers["confirm_delete_workspace"]()

        assert state.show_workspace_delete_confirm is True

    def test_cancel_delete_hides_dialog(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.show_workspace_delete_confirm = True
        ctrl._triggers["cancel_delete_workspace"]()

        assert state.show_workspace_delete_confirm is False

    @patch("agent.governance_ui.controllers.workspaces.httpx.Client")
    @patch("agent.governance_ui.controllers.workspaces.add_api_trace")
    def test_delete_workspace_success(self, mock_trace, mock_client_cls):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        delete_resp = MagicMock(status_code=200)
        ws_list_resp = MagicMock(status_code=200)
        ws_list_resp.json.return_value = []
        types_resp = MagicMock(status_code=200)
        types_resp.json.return_value = _SAMPLE_TYPES
        mock_client.delete.return_value = delete_resp
        mock_client.get.side_effect = [ws_list_resp, types_resp]

        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.selected_workspace = _SAMPLE_WS
        ctrl._triggers["delete_workspace"]()

        assert state.show_workspace_detail is False
        assert state.selected_workspace is None
        assert state.show_workspace_delete_confirm is False
        assert "deleted" in state.status_message.lower()
        assert state.is_loading is False

    def test_delete_workspace_skips_when_loading(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.selected_workspace = _SAMPLE_WS
        state.is_loading = True
        ctrl._triggers["delete_workspace"]()
        # Should not have changed state (skipped)
        assert state.selected_workspace == _SAMPLE_WS

    def test_delete_workspace_skips_without_selection(self):
        from agent.governance_ui.controllers.workspaces import (
            register_workspace_controllers,
        )
        state = _make_state()
        ctrl = _make_ctrl()
        register_workspace_controllers(state, ctrl, "http://localhost:8082")
        state.selected_workspace = None
        ctrl._triggers["delete_workspace"]()
        assert state.has_error is False
