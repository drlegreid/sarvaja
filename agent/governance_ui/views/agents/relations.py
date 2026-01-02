"""
Agent Relations Card Component.

Per RULE-012: Single Responsibility - only agent relations display.
Per RULE-032: File size limit (<300 lines).
Per GAP-UI-041: Agent-to-session/task relation links.
"""

from trame.widgets import vuetify3 as v3, html


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
