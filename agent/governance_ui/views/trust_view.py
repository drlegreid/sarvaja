"""
Trust View for Governance Dashboard.

Per RULE-012: Single Responsibility - only trust scores/leaderboard UI.
Per RULE-011: Multi-Agent Governance Protocol.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 1610-1890.
"""

from trame.widgets import vuetify3 as v3, html


def build_trust_header() -> None:
    """Build trust dashboard header with refresh button."""
    with v3.VCardTitle(classes="d-flex align-center"):
        html.Span("Agent Trust Dashboard")
        v3.VSpacer()
        v3.VBtn(
            "Refresh Data",
            prepend_icon="mdi-refresh",
            variant="outlined",
            size="small",
            click="trigger('load_trust_data')",
            __properties=["data-testid"],
            **{"data-testid": "trust-refresh-btn"}
        )


def build_governance_stats() -> None:
    """Build governance stats cards row."""
    with v3.VRow():
        # Total Agents
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color="primary",
                __properties=["data-testid"],
                **{"data-testid": "trust-stat-agents"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ governance_stats.total_agents || 0 }}",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Total Agents", classes="text-subtitle-2")
        # Avg Trust Score
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color="success",
                __properties=["data-testid"],
                **{"data-testid": "trust-stat-avg"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ (governance_stats.avg_trust_score * 100 || 0).toFixed(1) }}%",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Avg Trust Score", classes="text-subtitle-2")
        # Pending Proposals
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color="info",
                __properties=["data-testid"],
                **{"data-testid": "trust-stat-pending"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ governance_stats.pending_proposals || 0 }}",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Pending Proposals", classes="text-subtitle-2")
        # Escalated
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color="warning",
                __properties=["data-testid"],
                **{"data-testid": "trust-stat-escalated"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ escalated_proposals.length || 0 }}",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Escalated", classes="text-subtitle-2")


def build_trust_leaderboard() -> None:
    """Build trust leaderboard card."""
    with v3.VCol(cols=6):
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": "trust-leaderboard"}
        ):
            v3.VCardTitle("Trust Leaderboard")
            with v3.VCardText():
                with v3.VList(density="compact"):
                    with v3.VListItem(
                        v_for="agent in trust_leaderboard",
                        key=("agent.agent_id",),
                        click="selected_agent = agent; show_agent_detail = true",
                        __properties=["data-testid"],
                        **{"data-testid": "trust-agent-item"}
                    ):
                        with html.Template(v_slot_prepend=True):
                            with v3.VAvatar(
                                color=(
                                    "agent.trust_level === 'HIGH' ? 'success' : "
                                    "agent.trust_level === 'MEDIUM' ? 'warning' : 'error'"
                                ),
                                size="32"
                            ):
                                html.Span(
                                    "{{ agent.rank }}",
                                    classes="text-white font-weight-bold"
                                )
                        with html.Template(v_slot_default=True):
                            v3.VListItemTitle("{{ agent.name || agent.agent_id }}")
                            v3.VListItemSubtitle("{{ agent.agent_type }}")
                        with html.Template(v_slot_append=True):
                            v3.VChip(
                                v_text="(agent.trust_score * 100).toFixed(0) + '%'",
                                color=(
                                    "agent.trust_level === 'HIGH' ? 'success' : "
                                    "agent.trust_level === 'MEDIUM' ? 'warning' : 'error'"
                                ),
                                size="small",
                            )
                    # Empty state
                    v3.VListItem(
                        v_if="!trust_leaderboard || trust_leaderboard.length === 0",
                        title="No agents registered",
                        prepend_icon="mdi-robot-off",
                        disabled=True,
                    )


def build_proposals_panel() -> None:
    """Build recent proposals panel."""
    with v3.VCol(cols=6):
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": "trust-proposals"}
        ):
            v3.VCardTitle("Recent Proposals")
            with v3.VCardText():
                with v3.VList(density="compact"):
                    with v3.VListItem(
                        v_for="prop in proposals.slice(0, 5)",
                        key=("prop.proposal_id",),
                        __properties=["data-testid"],
                        **{"data-testid": "trust-proposal-item"}
                    ):
                        with html.Template(v_slot_prepend=True):
                            v3.VIcon(
                                icon=(
                                    "prop.proposal_type === 'create' ? 'mdi-plus-circle' : "
                                    "prop.proposal_type === 'modify' ? 'mdi-pencil-circle' : "
                                    "'mdi-close-circle'"
                                ),
                                color=(
                                    "prop.proposal_status === 'approved' ? 'success' : "
                                    "prop.proposal_status === 'rejected' ? 'error' : 'info'"
                                ),
                            )
                        with html.Template(v_slot_default=True):
                            v3.VListItemTitle("{{ prop.proposal_id }}")
                            v3.VListItemSubtitle(
                                "{{ prop.affected_rule }} - {{ prop.proposal_status }}"
                            )
                        with html.Template(v_slot_append=True):
                            v3.VChip(
                                v_text="prop.proposal_status",
                                color=(
                                    "prop.proposal_status === 'approved' ? 'success' : "
                                    "prop.proposal_status === 'rejected' ? 'error' : "
                                    "prop.proposal_status === 'pending' ? 'info' : 'warning'"
                                ),
                                size="x-small",
                            )
                    # Empty state
                    v3.VListItem(
                        v_if="!proposals || proposals.length === 0",
                        title="No proposals",
                        prepend_icon="mdi-file-document-outline",
                        disabled=True,
                    )


def build_escalated_proposals_alert() -> None:
    """Build escalated proposals alert section."""
    with v3.VRow(
        v_if="escalated_proposals && escalated_proposals.length > 0",
        classes="mt-4"
    ):
        with v3.VCol(cols=12):
            v3.VAlert(
                type="warning",
                title="Human Escalation Required",
                text=("escalated_proposals.length + ' proposals require human review'",),
                variant="tonal",
                __properties=["data-testid"],
                **{"data-testid": "trust-escalation-alert"}
            )
            with v3.VCard(
                variant="outlined",
                color="warning",
                classes="mt-2",
                __properties=["data-testid"],
                **{"data-testid": "trust-escalated-list"}
            ):
                with v3.VList(density="compact"):
                    v3.VListItem(
                        v_for="esc in escalated_proposals",
                        key=("esc.proposal_id",),
                        title=("esc.proposal_id",),
                        subtitle=("'Trigger: ' + (esc.escalation_trigger || 'Unknown')",),
                        prepend_icon="mdi-alert-circle",
                    )


def build_trust_dashboard_view() -> None:
    """Build the main trust dashboard view."""
    with v3.VCard(
        v_if="active_view === 'trust' && !show_agent_detail",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "trust-dashboard"}
    ):
        build_trust_header()

        with v3.VCardText():
            # Governance stats cards
            build_governance_stats()

            # Trust leaderboard and proposals
            with v3.VRow(classes="mt-4"):
                build_trust_leaderboard()
                build_proposals_panel()

            # Escalated proposals alert
            build_escalated_proposals_alert()


def build_agent_detail_metrics() -> None:
    """Build agent trust metrics row."""
    with v3.VRow():
        # Trust Score
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="tonal",
                color=(
                    "selected_agent.trust_score >= 0.8 ? 'success' : "
                    "selected_agent.trust_score >= 0.5 ? 'warning' : 'error'"
                ),
                __properties=["data-testid"],
                **{"data-testid": "agent-trust-score"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ (selected_agent.trust_score * 100).toFixed(1) }}%",
                        classes="text-h4 font-weight-bold"
                    )
                    html.Div("Trust Score", classes="text-subtitle-2")
        # Compliance
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "agent-compliance"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ (selected_agent.compliance_rate * 100 || 0).toFixed(1) }}%",
                        classes="text-h5"
                    )
                    html.Div("Compliance (40%)", classes="text-caption")
        # Accuracy
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "agent-accuracy"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ (selected_agent.accuracy_rate * 100 || 0).toFixed(1) }}%",
                        classes="text-h5"
                    )
                    html.Div("Accuracy (30%)", classes="text-caption")
        # Tenure
        with v3.VCol(cols=3):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "agent-tenure"}
            ):
                with v3.VCardText(classes="text-center"):
                    html.Div(
                        "{{ selected_agent.tenure_days || 0 }}",
                        classes="text-h5"
                    )
                    html.Div("Tenure Days (10%)", classes="text-caption")


def build_trust_formula_card() -> None:
    """Build trust formula explanation card."""
    v3.VDivider(classes="my-4")
    with v3.VCard(
        variant="outlined",
        classes="bg-grey-lighten-4",
        __properties=["data-testid"],
        **{"data-testid": "agent-trust-formula"}
    ):
        v3.VCardTitle("RULE-011 Trust Formula", density="compact")
        with v3.VCardText():
            html.Code(
                "Trust = (Compliance × 0.4) + (Accuracy × 0.3) + "
                "(Consistency × 0.2) + (Tenure × 0.1)",
                style="font-size: 14px;"
            )


def build_agent_detail_view() -> None:
    """Build the agent detail view (P9.5)."""
    with v3.VCard(
        v_if="active_view === 'trust' && show_agent_detail && selected_agent",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "trust-agent-detail"}
    ):
        with v3.VCardTitle(classes="d-flex align-center"):
            v3.VBtn(
                icon="mdi-arrow-left",
                variant="text",
                click="show_agent_detail = false; selected_agent = null",
                __properties=["data-testid"],
                **{"data-testid": "agent-detail-back-btn"}
            )
            html.Span("{{ selected_agent.name || selected_agent.agent_id }}")
            v3.VSpacer()
            v3.VChip(
                v_text="selected_agent.agent_type",
                color="primary",
                size="small",
            )

        with v3.VCardText():
            # Trust metrics
            build_agent_detail_metrics()

            # Trust formula explanation
            build_trust_formula_card()


def build_trust_view() -> None:
    """
    Build the complete Trust Dashboard view.

    This is the main entry point for the trust view module.
    Per RULE-011: Multi-Agent Governance Protocol.
    Per P9.5: Trust Dashboard implementation.
    """
    build_trust_dashboard_view()
    build_agent_detail_view()
