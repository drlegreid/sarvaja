"""
Agents View for Governance Dashboard.

Per RULE-012: Single Responsibility - only agents list/detail UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per GAP-FILE-001: Modularization of governance_dashboard.py.
Per GAP-UI-040: Effective config display.
Per GAP-UI-041: Agent-to-session/task relation links.

Extracted from governance_dashboard.py lines 2506-2549.
"""

from trame.widgets import vuetify3 as v3, html


def build_agents_list_view() -> None:
    """Build the Agents list view."""
    with v3.VCard(
        v_if="active_view === 'agents' && !show_agent_detail",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "agents-list"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            html.Span("Registered Agents")
            v3.VSpacer()
            v3.VBtn(
                "Refresh",
                prepend_icon="mdi-refresh",
                variant="outlined",
                size="small",
                click="trigger('refresh_data')",
                __properties=["data-testid"],
                **{"data-testid": "agents-refresh-btn"}
            )
        with v3.VCardText():
            html.Div(
                "{{ agents.length }} agents registered",
                classes="mb-2 text-grey"
            )
            with v3.VList(
                density="compact",
                __properties=["data-testid"],
                **{"data-testid": "agents-table"}
            ):
                with v3.VListItem(
                    v_for="agent in agents",
                    **{":key": "agent.agent_id"},
                    click="selected_agent = agent; show_agent_detail = true",
                    __properties=["data-testid"],
                    **{"data-testid": "agent-item"}
                ):
                    with html.Template(v_slot_prepend=True):
                        with v3.VAvatar(
                            color=(
                                "agent.status === 'ACTIVE' ? 'success' : 'grey'",
                            ),
                            size="40"
                        ):
                            v3.VIcon("mdi-robot", color="white")
                    with v3.VListItemTitle():
                        html.Span("{{ agent.name || agent.agent_id }}")
                    with v3.VListItemSubtitle():
                        html.Span(
                            "{{ agent.agent_type }} | "
                            "Tasks: {{ agent.tasks_executed || 0 }} | "
                            "Trust: {{ ((agent.trust_score || 0) * 100).toFixed(0) }}%"
                        )
                    with html.Template(v_slot_append=True):
                        v3.VChip(
                            v_text="agent.status",
                            color=(
                                "agent.status === 'ACTIVE' ? 'success' : 'grey'",
                            ),
                            size="small",
                        )


def build_agent_config_card() -> None:
    """Build agent configuration display card (GAP-UI-040)."""
    with v3.VCard(
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-config-card"}
    ):
        v3.VCardTitle("Configuration", density="compact")
        with v3.VCardText():
            with v3.VList(density="compact"):
                # Agent ID
                v3.VListItem(
                    title="Agent ID",
                    subtitle=("selected_agent.agent_id",),
                    prepend_icon="mdi-identifier"
                )
                # Agent Type
                v3.VListItem(
                    title="Type",
                    subtitle=("selected_agent.agent_type || 'N/A'",),
                    prepend_icon="mdi-cog"
                )
                # Model
                v3.VListItem(
                    v_if="selected_agent.model",
                    title="Model",
                    subtitle=("selected_agent.model",),
                    prepend_icon="mdi-brain"
                )
                # Instructions (truncated preview)
                v3.VListItem(
                    v_if="selected_agent.instructions",
                    title="Instructions",
                    subtitle=(
                        "(selected_agent.instructions || '').substring(0, 100) + "
                        "(selected_agent.instructions?.length > 100 ? '...' : '')",
                    ),
                    prepend_icon="mdi-text-box"
                )

            # Full instructions expandable
            with v3.VExpansionPanels(
                v_if="selected_agent.instructions?.length > 100",
                variant="accordion",
                classes="mt-2"
            ):
                with v3.VExpansionPanel():
                    v3.VExpansionPanelTitle("Full Instructions")
                    with v3.VExpansionPanelText():
                        html.Pre(
                            "{{ selected_agent.instructions }}",
                            style="white-space: pre-wrap; font-family: inherit; "
                                  "font-size: 0.875rem; margin: 0;",
                            __properties=["data-testid"],
                            **{"data-testid": "agent-instructions-full"}
                        )

            # Tools list
            with html.Div(
                v_if="selected_agent.tools?.length > 0",
                classes="mt-4"
            ):
                html.Div("Tools", classes="text-caption text-grey mb-2")
                v3.VChip(
                    v_for="tool in selected_agent.tools",
                    v_text="tool",
                    size="small",
                    color="secondary",
                    classes="mr-1 mb-1",
                    prepend_icon="mdi-wrench"
                )


def build_agent_metrics_card() -> None:
    """Build agent metrics display card."""
    with v3.VCard(
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-metrics-card"}
    ):
        v3.VCardTitle("Metrics", density="compact")
        with v3.VCardText():
            with v3.VRow():
                with v3.VCol(cols=4):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ ((selected_agent.trust_score || 0) * 100).toFixed(0) }}%",
                            classes="text-h4"
                        )
                        html.Div("Trust Score", classes="text-caption text-grey")
                with v3.VCol(cols=4):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ selected_agent.tasks_executed || 0 }}",
                            classes="text-h4"
                        )
                        html.Div("Tasks Executed", classes="text-caption text-grey")
                with v3.VCol(cols=4):
                    with html.Div(classes="text-center"):
                        html.Div(
                            "{{ selected_agent.sessions_count || 0 }}",
                            classes="text-h4"
                        )
                        html.Div("Sessions", classes="text-caption text-grey")

            # Last active
            html.Div(
                v_if="selected_agent.last_active",
                classes="text-center mt-4 text-caption text-grey"
            ).add_child(
                html.Span("Last active: {{ selected_agent.last_active }}")
            )


def build_agent_relations_card() -> None:
    """Build agent relations card (GAP-UI-041)."""
    with v3.VCard(
        variant="outlined",
        classes="mb-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-relations-card"}
    ):
        v3.VCardTitle("Related Items", density="compact")
        with v3.VCardText():
            # Recent sessions
            with html.Div(classes="mb-4"):
                html.Div("Recent Sessions", classes="font-weight-bold mb-2")
                with html.Div(
                    v_if="selected_agent.recent_sessions?.length > 0"
                ):
                    v3.VChip(
                        v_for="session in selected_agent.recent_sessions",
                        v_text="session",
                        size="small",
                        color="info",
                        classes="mr-1 mb-1",
                        prepend_icon="mdi-calendar-clock",
                        click="active_view = 'sessions'"
                    )
                html.Div(
                    v_if="!selected_agent.recent_sessions?.length",
                    classes="text-grey text-caption"
                ).add_child(html.Span("No sessions found"))

            # Active tasks
            with html.Div():
                html.Div("Active Tasks", classes="font-weight-bold mb-2")
                with html.Div(
                    v_if="selected_agent.active_tasks?.length > 0"
                ):
                    v3.VChip(
                        v_for="task in selected_agent.active_tasks",
                        v_text="task",
                        size="small",
                        color="warning",
                        classes="mr-1 mb-1",
                        prepend_icon="mdi-checkbox-marked-circle-outline",
                        click="active_view = 'tasks'"
                    )
                html.Div(
                    v_if="!selected_agent.active_tasks?.length",
                    classes="text-grey text-caption"
                ).add_child(html.Span("No active tasks"))


def build_agent_detail_view() -> None:
    """Build agent detail view (GAP-UI-040, GAP-UI-041)."""
    with v3.VCard(
        v_if="active_view === 'agents' && show_agent_detail && selected_agent",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "agent-detail"}
    ):
        # Header
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_agent_detail = false; selected_agent = null",
                __properties=["data-testid"],
                **{"data-testid": "agent-detail-back-btn"}
            )
            with v3.VAvatar(
                color=(
                    "selected_agent.status === 'ACTIVE' ? 'success' : 'grey'",
                ),
                size="32",
                classes="mr-2"
            ):
                v3.VIcon("mdi-robot", color="white", size="small")
            html.Span(
                "{{ selected_agent.name || selected_agent.agent_id }}",
                __properties=["data-testid"],
                **{"data-testid": "agent-detail-name"}
            )
            v3.VSpacer()
            v3.VChip(
                v_text="selected_agent.status",
                color=(
                    "selected_agent.status === 'ACTIVE' ? 'success' : 'grey'",
                ),
                __properties=["data-testid"],
                **{"data-testid": "agent-detail-status"}
            )

        with v3.VCardText():
            # Metrics at top
            build_agent_metrics_card()

            # Config display
            build_agent_config_card()

            # Relations
            build_agent_relations_card()


def build_agents_view() -> None:
    """
    Build the complete Agents view including list and detail.

    This is the main entry point for the agents view module.
    """
    build_agents_list_view()
    build_agent_detail_view()
