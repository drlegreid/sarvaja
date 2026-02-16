"""
Trust Dashboard Panels Components.

Per RULE-012: Single Responsibility - leaderboard and proposals display.
Per RULE-032: File size limit (<300 lines).
Per RULE-011: Multi-Agent Governance Protocol.
"""

from trame.widgets import vuetify3 as v3, html


def build_trust_leaderboard() -> None:
    """Build trust leaderboard card. Per UI-RESP-01-v1: Responsive."""
    with v3.VCol(cols=12, md=6):
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
                        click="trigger('select_agent', [agent.agent_id])",
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
    """Build recent proposals panel. Per UI-RESP-01-v1: Responsive."""
    with v3.VCol(cols=12, md=6):
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
