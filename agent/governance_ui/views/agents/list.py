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
                "Register Agent",
                prepend_icon="mdi-plus",
                color="primary",
                size="small",
                click="show_agent_registration = true",
                classes="mr-2",
                __properties=["data-testid"],
                **{"data-testid": "agents-register-btn"}
            )
            v3.VBtn(
                "Refresh",
                prepend_icon="mdi-refresh",
                variant="outlined",
                size="small",
                click="trigger('refresh_data')",
                __properties=["data-testid"],
                **{"data-testid": "agents-refresh-btn"}
            )

        # Governance trust stats (PLAN-UI-OVERHAUL-001 Task 5.4: Merge Trust)
        with v3.VCardText(classes="pb-0"):
            with v3.VRow(dense=True, classes="mb-2"):
                with v3.VCol(cols=6, sm=3):
                    with v3.VCard(variant="tonal", classes="text-center pa-2"):
                        html.Div("{{ agents.length || 0 }}", classes="text-h6")
                        html.Div("Total Agents", classes="text-caption")
                with v3.VCol(cols=6, sm=3):
                    with v3.VCard(variant="tonal", classes="text-center pa-2"):
                        html.Div(
                            "{{ governance_stats.avg_trust_score "
                            "? (governance_stats.avg_trust_score * 100).toFixed(0) + '%' "
                            ": '0%' }}",
                            classes="text-h6"
                        )
                        html.Div("Avg Trust", classes="text-caption")
                with v3.VCol(cols=6, sm=3):
                    with v3.VCard(variant="tonal", classes="text-center pa-2"):
                        html.Div(
                            "{{ governance_stats.pending_proposals || 0 }}",
                            classes="text-h6"
                        )
                        html.Div("Pending Proposals", classes="text-caption")
                with v3.VCol(cols=6, sm=3):
                    with v3.VCard(variant="tonal", classes="text-center pa-2"):
                        html.Div(
                            "{{ governance_stats.escalated_count || 0 }}",
                            classes="text-h6"
                        )
                        html.Div("Escalated", classes="text-caption")

        # Loading indicator (GAP-UI-005)
        v3.VProgressLinear(
            v_if="is_loading",
            indeterminate=True,
            color="primary",
            __properties=["data-testid"],
            **{"data-testid": "agents-loading"}
        )

        # Skeleton loaders (GAP-UI-PAGING-001: Loading states)
        with v3.VCardText(v_if="is_loading", style="max-height: 500px;"):
            with v3.VList(density="compact"):
                # Show 5 skeleton items while loading
                with v3.VListItem(v_for="n in 5", **{":key": "'skeleton-' + n"}):
                    with html.Template(v_slot_prepend=True):
                        v3.VSkeletonLoader(type="avatar", width=40, height=40)
                    with v3.VListItemTitle():
                        v3.VSkeletonLoader(type="text", width="40%")
                    with v3.VListItemSubtitle():
                        v3.VSkeletonLoader(type="text", width="70%")
                    with html.Template(v_slot_append=True):
                        v3.VSkeletonLoader(type="chip", width=60, height=24)

        # Agents list content (GAP-UI-036: scrollable)
        with v3.VCardText(v_if="!is_loading", style="max-height: 500px; overflow-y: auto;"):
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
                        # Agent metrics (GAP-UI-035: with last_active date)
                        html.Span(
                            "{{ agent.agent_type }} | "
                            "Tasks: {{ agent.tasks_executed || 0 }} | "
                            "Trust: {{ ((agent.trust_score || 0) * 100).toFixed(0) }}%"
                        )
                        html.Span(
                            v_if="agent.last_active",
                            v_text="' | Last: ' + agent.last_active",
                            classes="text-caption"
                        )
                    with html.Template(v_slot_append=True):
                        v3.VChip(
                            v_text="agent.status",
                            color=(
                                "agent.status === 'ACTIVE' ? 'success' : 'grey'",
                            ),
                            size="small",
                        )
