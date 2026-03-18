"""
Workspace Detail View Component.

Per RULE-012: Single Responsibility - only workspace detail UI.
Per RULE-032: File size limit (<300 lines).
Shows workspace info, assigned agents, and linked rules.
"""

from trame.widgets import vuetify3 as v3, html


def build_workspace_detail_view() -> None:
    """Build workspace detail view with agents and config."""
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
                click="show_workspace_detail = false; selected_workspace = null",
                __properties=["data-testid"],
                **{"data-testid": "workspace-detail-back-btn"}
            )
            with v3.VAvatar(
                color="primary", size="32", classes="mr-2"
            ):
                v3.VIcon("mdi-briefcase-outline", color="white", size="small")
            html.Span(
                "{{ selected_workspace.name }}",
                __properties=["data-testid"],
                **{"data-testid": "workspace-detail-name"}
            )
            v3.VSpacer()
            v3.VChip(
                v_text="selected_workspace.status || 'active'",
                color=(
                    "selected_workspace.status === 'active' ? 'success' : 'grey'",
                ),
                __properties=["data-testid"],
                **{"data-testid": "workspace-detail-status"}
            )

        with v3.VCardText():
            # Info card
            with v3.VCard(variant="outlined", classes="mb-4"):
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

            # Assigned agents
            with v3.VCard(variant="outlined", classes="mb-4"):
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
                    # Empty state
                    html.Div(
                        v_if="!selected_workspace.agent_ids || "
                             "selected_workspace.agent_ids.length === 0",
                        classes="text-grey text-center py-2"
                    ).add_child(html.Span("No agents assigned"))
                    # Agent chips
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
            with v3.VCard(variant="outlined", classes="mb-4"):
                with v3.VCardTitle(
                    classes="d-flex align-center", density="compact"
                ):
                    v3.VIcon("mdi-gavel", size="small", classes="mr-2")
                    html.Span("Default Rules")
                    v3.VSpacer()
                    v3.VChip(
                        v_text=(
                            "(selected_workspace.rule_ids || []).length "
                            "+ ' rules'"
                        ),
                        size="x-small",
                        color="warning",
                        variant="tonal",
                    )
                with v3.VCardText():
                    html.Div(
                        v_if="!selected_workspace.rule_ids || "
                             "selected_workspace.rule_ids.length === 0",
                        classes="text-grey text-center py-2"
                    ).add_child(html.Span("No default rules"))
                    with html.Div(
                        v_if="selected_workspace.rule_ids && "
                             "selected_workspace.rule_ids.length > 0"
                    ):
                        v3.VChip(
                            v_for="rid in selected_workspace.rule_ids",
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
