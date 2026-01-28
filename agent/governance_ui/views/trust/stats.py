"""
Trust Dashboard Stats Components.

Per RULE-012: Single Responsibility - governance stats display.
Per RULE-032: File size limit (<300 lines).
Per RULE-011: Multi-Agent Governance Protocol.
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
    """Build governance stats cards. Per UI-RESP-01-v1: Responsive."""
    with v3.VRow():
        # Total Agents
        with v3.VCol(cols=6, sm=3):
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
        with v3.VCol(cols=6, sm=3):
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
        with v3.VCol(cols=6, sm=3):
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
        with v3.VCol(cols=6, sm=3):
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
