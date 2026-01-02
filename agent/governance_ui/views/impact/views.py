"""
Impact View Components (Graph and List).

Per RULE-012: Single Responsibility - only impact visualization UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
"""

from trame.widgets import vuetify3 as v3, html


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
