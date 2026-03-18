"""
Tests for workspace list and detail view components.

Tests for agent/governance_ui/views/workspaces/list.py
and agent/governance_ui/views/workspaces/detail.py.
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

    def test_has_trigger_create_workspace_dialog(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert "trigger('create_workspace_dialog')" in source

    def test_has_status_filter_items(self):
        from agent.governance_ui.views.workspaces import list as ws_list
        source = inspect.getsource(ws_list)
        assert '"active"' in source
        assert '"archived"' in source

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

    def test_has_rule_ids_binding(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "selected_workspace.rule_ids" in source

    def test_has_v_for_agents(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "v_for" in source
        assert "aid in selected_workspace.agent_ids" in source

    def test_has_v_for_rules(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "rid in selected_workspace.rule_ids" in source

    def test_has_trigger_select_agent(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('select_agent'" in source

    def test_has_trigger_select_rule(self):
        from agent.governance_ui.views.workspaces import detail
        source = inspect.getsource(detail)
        assert "trigger('select_rule'" in source

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

    def test_module_docstring_present(self):
        from agent.governance_ui.views.workspaces import detail
        assert detail.__doc__ is not None
        assert "Workspace" in detail.__doc__
