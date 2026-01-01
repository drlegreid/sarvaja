"""
Impact View for Governance Dashboard.

Per RULE-012: Single Responsibility - only rule impact analysis UI.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Extracted from governance_dashboard.py lines 1376-1607.
"""

from trame.widgets import vuetify3 as v3, html


def build_impact_header() -> None:
    """Build impact analyzer header with view toggle."""
    with v3.VCardTitle(classes="d-flex align-center"):
        html.Span("Rule Impact Analyzer")
        v3.VSpacer()
        # Graph/List toggle
        with v3.VBtnToggle(
            v_model="show_graph_view",
            density="compact",
            color="primary",
            mandatory=True,
            __properties=["data-testid"],
            **{"data-testid": "impact-view-toggle"}
        ):
            v3.VBtn(
                icon="mdi-graph",
                value=True,
                __properties=["data-testid"],
                **{"data-testid": "impact-graph-btn"}
            )
            v3.VBtn(
                icon="mdi-format-list-bulleted",
                value=False,
                __properties=["data-testid"],
                **{"data-testid": "impact-list-btn"}
            )


def build_rule_selector() -> None:
    """Build rule selector dropdown."""
    with v3.VRow():
        with v3.VCol(cols=4):
            v3.VSelect(
                v_model="impact_selected_rule",
                items=("rules.map(r => r.rule_id || r.id)",),
                label="Select Rule to Analyze",
                variant="outlined",
                density="compact",
                clearable=True,
                change="analyze_rule_impact($event)",
                __properties=["data-testid"],
                **{"data-testid": "impact-rule-select"}
            )


def build_risk_summary_card() -> None:
    """Build risk assessment card."""
    with v3.VCol(cols=4):
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
    """Build recommendation and critical rules card."""
    with v3.VCol(cols=8):
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


def build_graph_view() -> None:
    """Build the dependency graph view."""
    with v3.VRow(v_if="show_graph_view && dependency_graph"):
        with v3.VCol(cols=12):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "impact-graph-card"}
            ):
                v3.VCardTitle("Dependency Graph")
                with v3.VCardText():
                    # Mermaid diagram display
                    html.Pre(
                        "{{ mermaid_diagram }}",
                        style=(
                            "background: #f5f5f5; padding: 16px; "
                            "border-radius: 4px; overflow-x: auto;"
                        ),
                        __properties=["data-testid"],
                        **{"data-testid": "impact-mermaid"}
                    )
                    # Graph stats
                    with v3.VRow(classes="mt-2"):
                        with v3.VCol(cols=3):
                            v3.VChip(
                                v_text=(
                                    "'Nodes: ' + "
                                    "(dependency_graph.stats?.total_nodes || 0)"
                                ),
                                size="small",
                                color="primary",
                            )
                        with v3.VCol(cols=3):
                            v3.VChip(
                                v_text=(
                                    "'Dependencies: ' + "
                                    "(dependency_graph.stats?.dependency_edges || 0)"
                                ),
                                size="small",
                                color="info",
                            )
                        with v3.VCol(cols=3):
                            v3.VChip(
                                v_text=(
                                    "'Conflicts: ' + "
                                    "(dependency_graph.stats?.conflict_edges || 0)"
                                ),
                                size="small",
                                color="warning",
                            )


def build_list_view() -> None:
    """Build the list view for dependencies."""
    with v3.VRow(v_if="!show_graph_view && impact_analysis"):
        # Dependents list
        with v3.VCol(cols=6):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "impact-dependents-list"}
            ):
                v3.VCardTitle("Rules That Depend on This Rule")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        v3.VListItem(
                            v_for="ruleId in impact_analysis.direct_dependents",
                            key=("ruleId",),
                            v_text="ruleId",
                            prepend_icon="mdi-arrow-right",
                            click=(
                                "selected_rule = rules.find("
                                "r => (r.rule_id || r.id) === ruleId); "
                                "show_rule_detail = true; active_view = 'rules'"
                            ),
                            __properties=["data-testid"],
                            **{"data-testid": "impact-dependent-item"}
                        )
                        v3.VListItem(
                            v_if=(
                                "!impact_analysis.direct_dependents || "
                                "impact_analysis.direct_dependents.length === 0"
                            ),
                            title="No dependents",
                            prepend_icon="mdi-check-circle",
                            disabled=True,
                        )

        # Dependencies list
        with v3.VCol(cols=6):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "impact-dependencies-list"}
            ):
                v3.VCardTitle("Rules This Rule Depends On")
                with v3.VCardText():
                    with v3.VList(density="compact"):
                        v3.VListItem(
                            v_for="ruleId in impact_analysis.dependencies",
                            key=("ruleId",),
                            v_text="ruleId",
                            prepend_icon="mdi-arrow-left",
                            click=(
                                "selected_rule = rules.find("
                                "r => (r.rule_id || r.id) === ruleId); "
                                "show_rule_detail = true; active_view = 'rules'"
                            ),
                            __properties=["data-testid"],
                            **{"data-testid": "impact-dependency-item"}
                        )
                        v3.VListItem(
                            v_if=(
                                "!impact_analysis.dependencies || "
                                "impact_analysis.dependencies.length === 0"
                            ),
                            title="No dependencies",
                            prepend_icon="mdi-check-circle",
                            disabled=True,
                        )


def build_empty_state() -> None:
    """Build empty state when no rule is selected."""
    with v3.VRow(v_if="!impact_analysis"):
        with v3.VCol(cols=12, classes="text-center py-8"):
            v3.VIcon("mdi-graph-outline", size="64", color="grey")
            html.P(
                "Select a rule above to analyze its impact",
                classes="text-grey mt-4",
                __properties=["data-testid"],
                **{"data-testid": "impact-empty-state"}
            )


def build_impact_view() -> None:
    """
    Build the Rule Impact Analyzer view.

    This is the main entry point for the impact view module.
    Per P9.4: Rule Impact Analysis.
    """
    with v3.VCard(
        v_if="active_view === 'impact'",
        classes="fill-height",
        __properties=["data-testid"],
        **{"data-testid": "impact-analyzer"}
    ):
        build_impact_header()

        with v3.VCardText():
            # Rule selector
            build_rule_selector()

            # Analysis results
            build_analysis_results()

            # Graph view
            build_graph_view()

            # List view
            build_list_view()

            # Empty state
            build_empty_state()
