"""
Trust Agent Detail Components.

Per RULE-012: Single Responsibility - agent detail display.
Per RULE-032: File size limit (<300 lines).
Per RULE-011: Multi-Agent Governance Protocol.
Per P9.5: Trust Dashboard implementation.
"""

from trame.widgets import vuetify3 as v3, html


def build_agent_detail_metrics() -> None:
    """Build agent trust metrics. Per UI-RESP-01-v1: Responsive."""
    with v3.VRow():
        # Trust Score
        with v3.VCol(cols=6, sm=3):
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
        with v3.VCol(cols=6, sm=3):
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
        with v3.VCol(cols=6, sm=3):
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
        with v3.VCol(cols=6, sm=3):
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
