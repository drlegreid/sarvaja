"""
Workspaces List View Component.

Per RULE-012: Single Responsibility - only workspace list UI.
Per RULE-032: File size limit (<300 lines).
Displays workspace entities with type, project, and agent count.
"""

from trame.widgets import vuetify3 as v3, html


def build_workspaces_list_view() -> None:
    """Build the Workspaces list view."""
    with v3.VCard(
        v_if="active_view === 'workspaces' && !show_workspace_detail",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "workspaces-list"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Workspaces")
            v3.VSpacer()
            v3.VBtn(
                "Create Workspace",
                prepend_icon="mdi-plus",
                color="primary",
                size="small",
                click="trigger('create_workspace_dialog')",
                classes="mr-2",
                __properties=["data-testid"],
                **{"data-testid": "workspace-create-btn"}
            )
            v3.VBtn(
                "Refresh",
                prepend_icon="mdi-refresh",
                variant="outlined",
                size="small",
                click="trigger('load_workspaces')",
                __properties=["data-testid"],
                **{"data-testid": "workspace-refresh-btn"}
            )

        # Summary stats
        with v3.VCardText(classes="pb-0"):
            with v3.VRow(dense=True, classes="mb-2"):
                with v3.VCol(cols=6, sm=3):
                    with v3.VCard(variant="tonal", classes="text-center pa-2"):
                        html.Div(
                            "{{ (workspaces || []).length }}",
                            classes="text-h6"
                        )
                        html.Div("Total", classes="text-caption")
                with v3.VCol(cols=6, sm=3):
                    with v3.VCard(variant="tonal", classes="text-center pa-2"):
                        html.Div(
                            "{{ (workspaces || []).filter("
                            "w => w.status === 'active').length }}",
                            classes="text-h6"
                        )
                        html.Div("Active", classes="text-caption")
                with v3.VCol(cols=6, sm=3):
                    with v3.VCard(variant="tonal", classes="text-center pa-2"):
                        html.Div(
                            "{{ (workspace_types || []).length }}",
                            classes="text-h6"
                        )
                        html.Div("Types", classes="text-caption")

        # Filters
        with v3.VCardText(classes="pb-0"):
            with v3.VRow(dense=True):
                with v3.VCol(cols=12, sm=4):
                    v3.VTextField(
                        v_model="workspaces_search",
                        label="Search workspaces",
                        prepend_inner_icon="mdi-magnify",
                        density="compact",
                        hide_details=True,
                        clearable=True,
                    )
                with v3.VCol(cols=6, sm=4):
                    v3.VSelect(
                        v_model="workspaces_type_filter",
                        label="Type",
                        items=("workspace_type_options", []),
                        density="compact",
                        hide_details=True,
                        clearable=True,
                    )
                with v3.VCol(cols=6, sm=4):
                    v3.VSelect(
                        v_model="workspaces_status_filter",
                        label="Status",
                        items=["active", "archived"],
                        density="compact",
                        hide_details=True,
                        clearable=True,
                    )

        # Loading
        v3.VProgressLinear(
            v_if="workspaces_loading",
            indeterminate=True,
            color="primary",
        )

        # List
        with v3.VCardText(
            v_if="!workspaces_loading",
            style="max-height: calc(100vh - 350px); overflow-y: auto;"
        ):
            html.Div(
                "{{ (workspaces || []).length }} workspaces",
                classes="mb-2 text-grey"
            )
            with v3.VList(
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "workspaces-table"}
            ):
                with v3.VListItem(
                    v_for="ws in workspaces",
                    **{":key": "ws.workspace_id"},
                    click="trigger('select_workspace', [ws.workspace_id])",
                    __properties=["data-testid"],
                    **{"data-testid": "workspace-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        with v3.VAvatar(
                            color=(
                                "ws.status === 'active' ? 'primary' : 'grey'",
                            ),
                            size="40"
                        ):
                            v3.VIcon(
                                "mdi-briefcase-outline",
                                color="white"
                            )
                    with v3.VListItemTitle():
                        html.Span("{{ ws.name }}")
                    with v3.VListItemSubtitle():
                        html.Span(
                            "{{ ws.workspace_type }} | "
                            "Agents: {{ (ws.agent_ids || []).length }} | "
                            "{{ ws.project_id || 'No project' }}"
                        )
                    with html.Template(v_slot_append=True):
                        v3.VChip(
                            v_text="ws.status || 'active'",
                            color=(
                                "ws.status === 'active' ? 'success' : 'grey'",
                            ),
                            size="small",
                        )
