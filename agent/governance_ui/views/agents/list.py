"""
Agents List View Component.

Per RULE-012: Single Responsibility - only agents list UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
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
