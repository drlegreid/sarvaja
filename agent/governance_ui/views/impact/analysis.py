"""
Impact Analysis Components.

Per RULE-012: Single Responsibility - only impact analysis cards UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
"""

from trame.widgets import vuetify3 as v3, html


def build_risk_summary_card() -> None:
    """Build risk assessment card. Per UI-RESP-01-v1: Responsive."""
    with v3.VCol(cols=12, md=4):
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": "impact-risk-card"}
        ):
            with v3.VCardTitle(classes="d-flex align-center"):
                html.Span("Risk Assessment")
                v3.VSpacer()
                v3.VChip(
                    v_text="impact_analysis.risk_level",
                    color=(
                        "impact_analysis.risk_level === 'CRITICAL' ? 'error' : "
                        "impact_analysis.risk_level === 'HIGH' ? 'warning' : "
                        "impact_analysis.risk_level === 'MEDIUM' ? 'info' : 'success'"
                    ),
                    size="large",
                    __properties=["data-testid"],
                    **{"data-testid": "impact-risk-chip"}
                )
            with v3.VCardText():
                with v3.VList(density="compact"):
                    v3.VListItem(
                        title="Total Rules Affected",
                        subtitle=("impact_analysis.total_affected + ' rules'",),
                        prepend_icon="mdi-alert-circle-outline",
                        __properties=["data-testid"],
                        **{"data-testid": "impact-total-affected"}
                    )
                    v3.VListItem(
                        title="Direct Dependents",
                        subtitle=(
                            "(impact_analysis.direct_dependents || []).length + ' rules'",
                        ),
                        prepend_icon="mdi-arrow-right-bold",
                        __properties=["data-testid"],
                        **{"data-testid": "impact-direct-deps"}
                    )
                    v3.VListItem(
                        title="Dependencies",
                        subtitle=(
                            "(impact_analysis.dependencies || []).length + ' rules'",
                        ),
                        prepend_icon="mdi-arrow-left-bold",
                        __properties=["data-testid"],
                        **{"data-testid": "impact-dependencies"}
                    )


def build_recommendation_card() -> None:
    """Build recommendation and critical rules. Per UI-RESP-01-v1: Responsive."""
    with v3.VCol(cols=12, md=8):
        with v3.VCard(
            variant="outlined",
            __properties=["data-testid"],
            **{"data-testid": "impact-recommendation-card"}
        ):
            v3.VCardTitle("Recommendation")
            with v3.VCardText():
                v3.VAlert(
                    v_text="impact_analysis.recommendation",
                    type=(
                        "impact_analysis.risk_level === 'CRITICAL' ? 'error' : "
                        "impact_analysis.risk_level === 'HIGH' ? 'warning' : 'info'"
                    ),
                    variant="tonal",
                    __properties=["data-testid"],
                    **{"data-testid": "impact-recommendation"}
                )

                # Critical rules affected
                with v3.VCard(
                    v_if=(
                        "impact_analysis.critical_rules_affected && "
                        "impact_analysis.critical_rules_affected.length > 0"
                    ),
                    variant="outlined",
                    color="error",
                    classes="mt-4",
                    __properties=["data-testid"],
                    **{"data-testid": "impact-critical-rules"}
                ):
                    v3.VCardTitle("Critical Rules Affected", density="compact")
                    with v3.VCardText():
                        with v3.VChipGroup():
                            v3.VChip(
                                v_for="ruleId in impact_analysis.critical_rules_affected",
                                key=("ruleId",),
                                v_text="ruleId",
                                color="error",
                                size="small",
                                click=(
                                    "selected_rule = rules.find("
                                    "r => (r.rule_id || r.id) === ruleId); "
                                    "show_rule_detail = true; active_view = 'rules'"
                                ),
                                __properties=["data-testid"],
                                **{"data-testid": "impact-critical-rule-chip"}
                            )


def build_analysis_results() -> None:
    """Build analysis results row."""
    with v3.VRow(v_if="impact_analysis"):
        build_risk_summary_card()
        build_recommendation_card()
