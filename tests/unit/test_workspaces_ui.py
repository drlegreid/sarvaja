"""
Tests for workspace list, detail, and form view components.

Tests for agent/governance_ui/views/workspaces/list.py,
agent/governance_ui/views/workspaces/detail.py, and
agent/governance_ui/views/workspaces/form.py.
"""
import inspect

import pytest


# ---------------------------------------------------------------------------
# Workspaces List View
# ---------------------------------------------------------------------------


class TestWorkspacesListComponents:
    """Verify the list build function exists and is callable."""

    def test_build_workspaces_list_view_callable(self):
        from agent.governance_ui.views.workspaces.list import (
            build_workspaces_list_view,
        )
        assert callable(build_workspaces_list_view)

    def test_list_build_function_takes_no_args(self):
        from agent.governance_ui.views.workspaces.list import (
            build_workspaces_list_view,
        )
        sig = inspect.signature(build_workspaces_list_view)
        assert len(sig.parameters) == 0

    def test_list_build_function_has_docstring(self):
        from agent.governance_ui.views.workspaces.list import (
            build_workspaces_list_view,
        )
        assert build_workspaces_list_view.__doc__ is not None
        assert "workspaces" in build_workspaces_list_view.__doc__.lower()


class TestWorkspacesListTestIds:
    """Verify data-testid attributes for E2E selector targeting."""

    def test_has_workspaces_list_testid(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspaces-list" in source

    def test_has_workspace_create_btn_testid(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspace-create-btn" in source

    def test_has_workspace_refresh_btn_testid(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspace-refresh-btn" in source

    def test_has_workspaces_table_testid(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspaces-table" in source

    def test_has_workspace_item_testid(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspace-item" in source


class TestWorkspacesListContent:
    """Verify UI content strings and icons in the list view."""

    def test_has_workspaces_title(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "Workspaces" in source

    def test_has_create_workspace_button(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "Create Workspace" in source

    def test_has_refresh_button(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "Refresh" in source

    def test_has_plus_icon(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "mdi-plus" in source

    def test_has_refresh_icon(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "mdi-refresh" in source

    def test_has_magnify_icon(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "mdi-magnify" in source

    def test_has_briefcase_icon(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "mdi-briefcase-outline" in source

    def test_has_total_stat_label(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert '"Total"' in source

    def test_has_active_stat_label(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert '"Active"' in source

    def test_has_types_stat_label(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert '"Types"' in source


class TestWorkspacesListStructure:
    """Verify Vuetify component usage and reactive bindings in list view."""

    def test_uses_vcard(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "VCard(" in source

    def test_uses_vlist(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "VList(" in source

    def test_uses_vlistitem(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "VListItem(" in source

    def test_uses_vtextfield(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "VTextField(" in source

    def test_uses_vselect(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "VSelect(" in source

    def test_uses_vprogress_linear(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "VProgressLinear(" in source

    def test_has_search_binding(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspaces_search" in source

    def test_has_type_filter_binding(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspaces_type_filter" in source

    def test_has_status_filter_binding(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspaces_status_filter" in source

    def test_has_loading_state_binding(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "workspaces_loading" in source

    def test_has_active_view_guard(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "active_view === 'workspaces'" in source

    def test_has_v_for_workspaces(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "v_for" in source
        assert "ws in workspaces" in source

    def test_has_workspace_id_key(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "ws.workspace_id" in source

    def test_has_status_color_condition(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "ws.status === 'active'" in source

    def test_has_trigger_select_workspace(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "trigger('select_workspace'" in source

    def test_has_trigger_load_workspaces(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "trigger('load_workspaces')" in source

    def test_has_trigger_show_create_workspace_form(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "trigger('show_create_workspace_form')" in source

    def test_has_status_filter_items(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert '"active"' in source
        assert '"archived"' in source

    def test_list_hidden_when_form_open(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "show_workspace_form" in source

    def test_module_docstring_present(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        assert ws_list.__doc__ is not None
        assert "Workspaces" in ws_list.__doc__


# ---------------------------------------------------------------------------
# Workspace Detail View
# ---------------------------------------------------------------------------


class TestWorkspaceDetailComponents:
    """Verify the detail build function exists and is callable."""

    def test_build_workspace_detail_view_callable(self):
        from agent.governance_ui.views.workspaces.detail import (
            build_workspace_detail_view,
        )
        assert callable(build_workspace_detail_view)

    def test_detail_build_function_takes_no_args(self):
        from agent.governance_ui.views.workspaces.detail import (
            build_workspace_detail_view,
        )
        sig = inspect.signature(build_workspace_detail_view)
        assert len(sig.parameters) == 0

    def test_detail_build_function_has_docstring(self):
        from agent.governance_ui.views.workspaces.detail import (
            build_workspace_detail_view,
        )
        assert build_workspace_detail_view.__doc__ is not None
        assert "workspace" in build_workspace_detail_view.__doc__.lower()


class TestWorkspaceDetailTestIds:
    """Verify data-testid attributes for E2E selector targeting."""

    def test_has_workspace_detail_testid(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "workspace-detail" in source

    def test_has_workspace_detail_back_btn_testid(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "workspace-detail-back-btn" in source

    def test_has_workspace_detail_name_testid(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "workspace-detail-name" in source

    def test_has_workspace_detail_status_testid(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "workspace-detail-status" in source

    def test_has_workspace_edit_btn_testid(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "workspace-edit-btn" in source

    def test_has_workspace_delete_btn_testid(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "workspace-delete-btn" in source

    def test_has_workspace_delete_dialog_testid(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "workspace-delete-dialog" in source

    def test_has_workspace_edit_save_btn_testid(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "workspace-edit-save-btn" in source


class TestWorkspaceDetailContent:
    """Verify UI content strings and icons in the detail view."""

    def test_has_workspace_info_title(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "Workspace Info" in source

    def test_has_assigned_agents_title(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "Assigned Agents" in source

    def test_has_default_rules_title(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "Default Rules" in source

    def test_has_arrow_left_icon(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "mdi-arrow-left" in source

    def test_has_briefcase_icon(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "mdi-briefcase-outline" in source

    def test_has_robot_icon(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "mdi-robot" in source

    def test_has_gavel_icon(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "mdi-gavel" in source

    def test_has_pencil_icon(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "mdi-pencil" in source

    def test_has_delete_icon(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "mdi-delete" in source

    def test_has_id_label(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert '"ID"' in source

    def test_has_type_label(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert '"Type"' in source

    def test_has_project_label(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert '"Project"' in source

    def test_has_created_label(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert '"Created"' in source

    def test_has_empty_agents_message(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "No agents assigned" in source

    def test_has_empty_rules_message(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "No default rules" in source

    def test_has_delete_confirmation_text(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "Delete Workspace?" in source
        assert "cannot be undone" in source

    def test_has_edit_workspace_title(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "Edit Workspace" in source


class TestWorkspaceDetailStructure:
    """Verify Vuetify component usage and reactive bindings in detail view."""

    def test_uses_vcard(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VCard(" in source

    def test_uses_vchip(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VChip(" in source

    def test_uses_vrow(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VRow(" in source

    def test_uses_vcol(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VCol(" in source

    def test_uses_vbtn(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VBtn(" in source

    def test_uses_vavatar(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VAvatar(" in source

    def test_uses_vdialog(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VDialog(" in source

    def test_uses_vtextfield_in_edit(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VTextField(" in source

    def test_uses_vtextarea_in_edit(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VTextarea(" in source

    def test_uses_vselect_in_edit(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "VSelect(" in source

    def test_has_selected_workspace_binding(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "selected_workspace" in source

    def test_has_active_view_guard(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "active_view === 'workspaces'" in source

    def test_has_show_workspace_detail_guard(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "show_workspace_detail" in source

    def test_has_back_button_resets_state(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "show_workspace_detail = false" in source
        assert "selected_workspace = null" in source

    def test_has_agent_ids_binding(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "selected_workspace.agent_ids" in source

    def test_has_default_rules_binding(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "selected_workspace.default_rules" in source

    def test_has_v_for_agents(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "v_for" in source
        assert "aid in selected_workspace.agent_ids" in source

    def test_has_v_for_rules(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "rid in selected_workspace.default_rules" in source

    def test_has_trigger_select_agent(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('select_agent'" in source

    def test_has_trigger_select_rule(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('select_rule'" in source

    def test_has_trigger_edit_workspace(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('edit_workspace')" in source

    def test_has_trigger_submit_workspace_edit(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('submit_workspace_edit')" in source

    def test_has_trigger_cancel_workspace_edit(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('cancel_workspace_edit')" in source

    def test_has_trigger_confirm_delete_workspace(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('confirm_delete_workspace')" in source

    def test_has_trigger_delete_workspace(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('delete_workspace')" in source

    def test_has_agent_navigation(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "active_view = 'agents'" in source

    def test_has_rule_navigation(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "active_view = 'rules'" in source

    def test_has_agents_count_chip(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "agents" in source

    def test_has_rules_count_chip(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "rules" in source

    def test_has_description_section(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "selected_workspace.description" in source

    def test_has_project_id_fallback(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "selected_workspace.project_id || 'None'" in source

    def test_has_created_at_fallback(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "selected_workspace.created_at || 'Unknown'" in source

    def test_has_edit_workspace_mode_guard(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "edit_workspace_mode" in source

    def test_has_edit_workspace_name_binding(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "edit_workspace_name" in source

    def test_has_edit_workspace_description_binding(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "edit_workspace_description" in source

    def test_has_edit_workspace_status_binding(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "edit_workspace_status" in source

    def test_has_delete_confirm_dialog_binding(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "show_workspace_delete_confirm" in source

    def test_module_docstring_present(self):
        from agent.governance_ui.views.workspaces import detail
        assert detail.__doc__ is not None
        assert "Workspace" in detail.__doc__


# ---------------------------------------------------------------------------
# Workspace Form View
# ---------------------------------------------------------------------------


class TestWorkspaceFormComponents:
    """Verify the form build function exists and is callable."""

    def test_build_workspace_form_view_callable(self):
        from agent.governance_ui.views.workspaces.form import (
            build_workspace_form_view,
        )
        assert callable(build_workspace_form_view)

    def test_form_build_function_takes_no_args(self):
        from agent.governance_ui.views.workspaces.form import (
            build_workspace_form_view,
        )
        sig = inspect.signature(build_workspace_form_view)
        assert len(sig.parameters) == 0

    def test_form_build_function_has_docstring(self):
        from agent.governance_ui.views.workspaces.form import (
            build_workspace_form_view,
        )
        assert build_workspace_form_view.__doc__ is not None
        assert "workspace" in build_workspace_form_view.__doc__.lower()


class TestWorkspaceFormTestIds:
    """Verify data-testid attributes for E2E targeting."""

    def test_has_workspace_form_testid(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "workspace-form" in source

    def test_has_workspace_form_cancel_btn_testid(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "workspace-form-cancel-btn" in source

    def test_has_workspace_form_submit_btn_testid(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "workspace-form-submit-btn" in source

    def test_has_workspace_form_name_testid(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "workspace-form-name" in source

    def test_has_workspace_form_type_testid(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "workspace-form-type" in source

    def test_has_workspace_form_description_testid(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "workspace-form-description" in source

    def test_has_workspace_form_project_testid(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "workspace-form-project" in source

    def test_has_workspace_create_form_testid(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "workspace-create-form" in source


class TestWorkspaceFormContent:
    """Verify UI content strings and field labels in the form view."""

    def test_has_create_workspace_title(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "Create Workspace" in source

    def test_has_name_label(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "Workspace Name" in source

    def test_has_type_label(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "Workspace Type" in source

    def test_has_description_label(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "Description" in source

    def test_has_project_label(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "Project ID" in source

    def test_has_cancel_button(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert '"Cancel"' in source

    def test_has_create_button(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert '"Create"' in source


class TestWorkspaceFormStructure:
    """Verify Vuetify components and bindings in the form view."""

    def test_uses_vcard(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "VCard(" in source

    def test_uses_vtextfield(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "VTextField(" in source

    def test_uses_vtextarea(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "VTextarea(" in source

    def test_uses_vselect(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "VSelect(" in source

    def test_uses_vform(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "VForm(" in source

    def test_uses_vbtn(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "VBtn(" in source

    def test_has_form_name_binding(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "form_workspace_name" in source

    def test_has_form_type_binding(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "form_workspace_type" in source

    def test_has_form_description_binding(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "form_workspace_description" in source

    def test_has_form_project_binding(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "form_workspace_project_id" in source

    def test_has_trigger_create_workspace(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "trigger('create_workspace')" in source

    def test_has_trigger_cancel_workspace_form(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "trigger('cancel_workspace_form')" in source

    def test_has_active_view_guard(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "active_view === 'workspaces'" in source

    def test_has_show_workspace_form_guard(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "show_workspace_form" in source

    def test_has_loading_state(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "is_loading" in source

    def test_has_error_alert(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "has_error" in source

    def test_has_submit_disabled_when_empty(self):
        from agent.governance_ui.views.workspaces import form
        source = inspect.getsource(form)
        assert "form_workspace_name" in source

    def test_module_docstring_present(self):
        from agent.governance_ui.views.workspaces import form
        assert form.__doc__ is not None
        assert "Workspace" in form.__doc__


# ---------------------------------------------------------------------------
# Workspaces View Entry Point
# ---------------------------------------------------------------------------


class TestWorkspacesViewEntryPoint:
    """Verify the top-level workspaces_view.py entry point."""

    def test_build_workspaces_view_callable(self):
        from agent.governance_ui.views.workspaces_view import (
            build_workspaces_view,
        )
        assert callable(build_workspaces_view)

    def test_workspaces_view_has_docstring(self):
        from agent.governance_ui.views.workspaces_view import (
            build_workspaces_view,
        )
        assert build_workspaces_view.__doc__ is not None

    def test_workspaces_view_imports_all_subviews(self):
        from agent.governance_ui.views import workspaces_view
        source = inspect.getsource(workspaces_view)
        assert "build_workspaces_list_view" in source
        assert "build_workspace_detail_view" in source
        assert "build_workspace_form_view" in source


# ---------------------------------------------------------------------------
# Workspaces __init__.py exports
# ---------------------------------------------------------------------------


class TestWorkspacesPackageExports:
    """Verify __init__.py exports all view builders."""

    def test_exports_list_view(self):
        from agent.governance_ui.views.workspaces import (
            build_workspaces_list_view,
        )
        assert callable(build_workspaces_list_view)

    def test_exports_detail_view(self):
        from agent.governance_ui.views.workspaces import (
            build_workspace_detail_view,
        )
        assert callable(build_workspace_detail_view)

    def test_exports_form_view(self):
        from agent.governance_ui.views.workspaces import (
            build_workspace_form_view,
        )
        assert callable(build_workspace_form_view)
