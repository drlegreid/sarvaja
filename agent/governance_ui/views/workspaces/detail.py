"""
Workspace Detail View Component.

Per RULE-012: Single Responsibility - only workspace detail UI.
Per RULE-032: File size limit (<300 lines).
Shows workspace info with edit/delete actions, assigned agents, and linked rules.
"""

from trame.widgets import vuetify3 as v3, html

from agent.governance_ui.views.workspaces.linked_tasks import (
    build_workspace_linked_tasks,
)


def build_workspace_detail_view() -> None:
    """Build workspace detail view with edit/delete and agents."""
    with v3.VCard(
        v_if="active_view === 'workspaces' && show_workspace_detail "
             "&& selected_workspace",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "workspace-detail"}
    ):
        # Header
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click=(
                    "show_workspace_detail = false; "
                    "selected_workspace = null; "
                    "edit_workspace_mode = false"
                ),
                __properties=["data-testid"],
                **{"data-testid": "workspace-detail-back-btn"}
            )
            with v3.VAvatar(
                color="primary", size="32", classes="mr-2"
            ):
                v3.VIcon("mdi-briefcase-outline", color="white", size="small")
            html.Span(
                "{{ selected_workspace.name }}",
                v_if="!edit_workspace_mode",
                __properties=["data-testid"],
                **{"data-testid": "workspace-detail-name"}
            )
            html.Span(
                "Editing Workspace",
                v_if="edit_workspace_mode",
                classes="text-grey",
            )
            v3.VSpacer()
            # Action buttons (view mode)
            with html.Div(v_if="!edit_workspace_mode"):
                v3.VBtn(
                    icon="mdi-pencil",
                    variant="text",
                    color="primary",
                    click="trigger('edit_workspace')",
                    __properties=["data-testid"],
                    **{"data-testid": "workspace-edit-btn"},
                )
                v3.VBtn(
                    icon="mdi-delete",
                    variant="text",
                    color="error",
                    click="trigger('confirm_delete_workspace')",
                    __properties=["data-testid"],
                    **{"data-testid": "workspace-delete-btn"},
                )
            v3.VChip(
                v_text="selected_workspace.status || 'active'",
                v_if="!edit_workspace_mode",
                color=(
                    "selected_workspace.status === 'active' ? 'success' : 'grey'",
                ),
                __properties=["data-testid"],
                **{"data-testid": "workspace-detail-status"}
            )

        with v3.VCardText():
            # Error alert
            v3.VAlert(
                v_if="has_error",
                type_="error",
                variant="tonal",
                classes="mb-4",
                v_text="error_message",
                closable=True,
                **{"@click:close": "has_error = false"},
            )

            # ── Edit mode ───────────────────────────────────────
            with v3.VCard(
                v_if="edit_workspace_mode",
                variant="outlined",
                classes="mb-4",
            ):
                v3.VCardTitle("Edit Workspace", density="compact")
                with v3.VCardText():
                    v3.VTextField(
                        v_model="edit_workspace_name",
                        label="Name *",
                        density="compact",
                        classes="mb-3",
                        __properties=["data-testid"],
                        **{"data-testid": "workspace-edit-name"},
                    )
                    v3.VTextarea(
                        v_model="edit_workspace_description",
                        label="Description",
                        density="compact",
                        rows=3,
                        auto_grow=True,
                        classes="mb-3",
                        __properties=["data-testid"],
                        **{"data-testid": "workspace-edit-description"},
                    )
                    v3.VSelect(
                        v_model="edit_workspace_status",
                        label="Status",
                        items=["active", "archived"],
                        density="compact",
                        __properties=["data-testid"],
                        **{"data-testid": "workspace-edit-status"},
                    )
                with v3.VCardActions():
                    v3.VSpacer()
                    v3.VBtn(
                        "Cancel",
                        variant="text",
                        click="trigger('cancel_workspace_edit')",
                    )
                    v3.VBtn(
                        "Save",
                        color="primary",
                        click="trigger('submit_workspace_edit')",
                        loading=("is_loading",),
                        disabled=("!edit_workspace_name",),
                        __properties=["data-testid"],
                        **{"data-testid": "workspace-edit-save-btn"},
                    )

            # ── View mode ───────────────────────────────────────
            # Info card
            with v3.VCard(
                v_if="!edit_workspace_mode",
                variant="outlined",
                classes="mb-4",
            ):
                v3.VCardTitle("Workspace Info", density="compact")
                with v3.VCardText():
                    with v3.VRow(dense=True):
                        with v3.VCol(cols=6):
                            html.Div("ID", classes="text-caption text-grey")
                            html.Div("{{ selected_workspace.workspace_id }}")
                        with v3.VCol(cols=6):
                            html.Div("Type", classes="text-caption text-grey")
                            html.Div("{{ selected_workspace.workspace_type }}")
                        with v3.VCol(cols=6):
                            html.Div("Project", classes="text-caption text-grey")
                            html.Div(
                                "{{ selected_workspace.project_id || 'None' }}"
                            )
                        with v3.VCol(cols=6):
                            html.Div("Created", classes="text-caption text-grey")
                            html.Div(
                                "{{ selected_workspace.created_at || 'Unknown' }}"
                            )
                    html.Div(
                        v_if="selected_workspace.description",
                        classes="mt-2"
                    ).add_child(
                        html.Span(
                            "{{ selected_workspace.description }}",
                            classes="text-body-2"
                        )
                    )

            # Assigned agents (shown in both modes)
            with v3.VCard(
                v_if="!edit_workspace_mode",
                variant="outlined",
                classes="mb-4",
            ):
                with v3.VCardTitle(
                    classes="d-flex align-center", density="compact"
                ):
                    v3.VIcon("mdi-robot", size="small", classes="mr-2")
                    html.Span("Assigned Agents")
                    v3.VSpacer()
                    v3.VChip(
                        v_text=(
                            "(selected_workspace.agent_ids || []).length "
                            "+ ' agents'"
                        ),
                        size="x-small",
                        color="info",
                        variant="tonal",
                    )
                with v3.VCardText():
                    html.Div(
                        v_if="!selected_workspace.agent_ids || "
                             "selected_workspace.agent_ids.length === 0",
                        classes="text-grey text-center py-2"
                    ).add_child(html.Span("No agents assigned"))
                    with html.Div(
                        v_if="selected_workspace.agent_ids && "
                             "selected_workspace.agent_ids.length > 0"
                    ):
                        v3.VChip(
                            v_for="aid in selected_workspace.agent_ids",
                            v_text="aid",
                            **{":key": "aid"},
                            size="small",
                            color="primary",
                            classes="mr-1 mb-1",
                            prepend_icon="mdi-robot",
                            click=(
                                "trigger('select_agent', [aid]); "
                                "active_view = 'agents'"
                            ),
                        )

            # Linked rules
            with v3.VCard(
                v_if="!edit_workspace_mode",
                variant="outlined",
                classes="mb-4",
            ):
                with v3.VCardTitle(
                    classes="d-flex align-center", density="compact"
                ):
                    v3.VIcon("mdi-gavel", size="small", classes="mr-2")
                    html.Span("Default Rules")
                    v3.VSpacer()
                    v3.VChip(
                        v_text=(
                            "(selected_workspace.default_rules || []).length "
                            "+ ' rules'"
                        ),
                        size="x-small",
                        color="warning",
                        variant="tonal",
                    )
                with v3.VCardText():
                    html.Div(
                        v_if="!selected_workspace.default_rules || "
                             "selected_workspace.default_rules.length === 0",
                        classes="text-grey text-center py-2"
                    ).add_child(html.Span("No default rules"))
                    with html.Div(
                        v_if="selected_workspace.default_rules && "
                             "selected_workspace.default_rules.length > 0"
                    ):
                        v3.VChip(
                            v_for="rid in selected_workspace.default_rules",
                            v_text="rid",
                            **{":key": "rid"},
                            size="small",
                            color="warning",
                            classes="mr-1 mb-1",
                            prepend_icon="mdi-gavel",
                            click=(
                                "trigger('select_rule', [rid]); "
                                "active_view = 'rules'"
                            ),
                        )

        # GAP-WS-DETAIL-UI: Linked tasks section
        build_workspace_linked_tasks()

        # Delete confirmation dialog
        with v3.VDialog(
            v_model="show_workspace_delete_confirm",
            max_width="400px",
            __properties=["data-testid"],
            **{"data-testid": "workspace-delete-dialog"}
        ):
            with v3.VCard():
                v3.VCardTitle("Delete Workspace?")
                v3.VCardText(
                    "Are you sure you want to delete workspace "
                    "'{{ selected_workspace.name }}'? "
                    "This cannot be undone."
                )
                with v3.VCardActions():
                    v3.VSpacer()
                    v3.VBtn(
                        "Cancel",
                        variant="text",
                        click="trigger('cancel_delete_workspace')",
                        __properties=["data-testid"],
                        **{"data-testid": "workspace-delete-cancel-btn"},
                    )
                    v3.VBtn(
                        "Delete",
                        color="error",
                        click="trigger('delete_workspace')",
                        loading=("is_loading",),
                        __properties=["data-testid"],
                        **{"data-testid": "workspace-delete-confirm-btn"},
                    )
