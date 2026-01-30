"""
Impact View Components (Graph and List).

Per RULE-012: Single Responsibility - only impact visualization UI.
Per RULE-032: File size limit (<300 lines).
Per GAP-FILE-001: Modularization of governance_dashboard.py.
Per RULE-039: Context Compression Standard (Mermaid diagrams).
"""

from trame.widgets import vuetify3 as v3, html

from agent.governance_ui.components.mermaid import build_mermaid_with_fallback


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
                    # Mermaid diagram with proper rendering
                    build_mermaid_with_fallback("impact-graph", "mermaid_diagram")
                    # Graph stats - Per UI-RESP-01-v1: Responsive
                    with v3.VRow(classes="mt-2"):
                        with v3.VCol(cols=12, sm=4):
                            v3.VChip(
                                v_text=(
                                    "'Nodes: ' + "
                                    "(dependency_graph.stats?.total_nodes || 0)"
                                ),
                                size="small",
                                color="primary",
                            )
                        with v3.VCol(cols=12, sm=4):
                            v3.VChip(
                                v_text=(
                                    "'Dependencies: ' + "
                                    "(dependency_graph.stats?.dependency_edges || 0)"
                                ),
                                size="small",
                                color="info",
                            )
                        with v3.VCol(cols=12, sm=4):
                            v3.VChip(
                                v_text=(
                                    "'Conflicts: ' + "
                                    "(dependency_graph.stats?.conflict_edges || 0)"
                                ),
                                size="small",
                                color="warning",
                            )


def build_list_view() -> None:
    """Build the list view for dependencies. Per UI-RESP-01-v1: Responsive."""
    with v3.VRow(v_if="!show_graph_view && impact_analysis"):
        # Dependents list
        with v3.VCol(cols=12, md=6):
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
        with v3.VCol(cols=12, md=6):
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


def build_global_overview() -> None:
    """Build global overview when no rule is selected.

    Per PLAN-UI-OVERHAUL-001 Task 4.3: Shows dependency statistics,
    orphaned rules, and overall graph health before rule selection.
    """
    with v3.VRow(v_if="!impact_analysis && dependency_overview"):
        # Total dependency stats
        with v3.VCol(cols=12, md=4):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "overview-total-stats"}
            ):
                v3.VCardTitle("Dependency Statistics")
                with v3.VCardText():
                    with html.Div(classes="d-flex flex-column ga-2"):
                        v3.VChip(
                            v_text="'Total Rules: ' + (dependency_overview.total_rules || 0)",
                            color="primary",
                            size="small",
                        )
                        v3.VChip(
                            v_text="'Total Dependencies: ' + (dependency_overview.total_dependencies || 0)",
                            color="info",
                            size="small",
                        )
                        v3.VChip(
                            v_text="'Circular Dependencies: ' + (dependency_overview.circular_count || 0)",
                            v_bind_color="dependency_overview.circular_count > 0 ? 'error' : 'success'",
                            size="small",
                        )

        # Orphaned rules
        with v3.VCol(cols=12, md=8):
            with v3.VCard(
                variant="outlined",
                __properties=["data-testid"],
                **{"data-testid": "overview-orphan-rules"}
            ):
                with v3.VCardTitle(classes="d-flex align-center"):
                    html.Span("Orphaned Rules")
                    v3.VSpacer()
                    v3.VChip(
                        v_text="(dependency_overview.orphan_rules || []).length",
                        size="x-small",
                        color="warning",
                    )
                with v3.VCardText():
                    html.P(
                        "Rules with no dependencies and no dependents.",
                        classes="text-caption text-grey mb-2",
                    )
                    v3.VChip(
                        v_for="rule in (dependency_overview.orphan_rules || [])",
                        v_text="rule",
                        size="small",
                        color="warning",
                        variant="tonal",
                        classes="mr-1 mb-1",
                        prepend_icon="mdi-link-off",
                    )
                    html.Div(
                        "No orphaned rules found",
                        v_if="!dependency_overview.orphan_rules || dependency_overview.orphan_rules.length === 0",
                        classes="text-grey",
                    )

    # Fallback: no overview data loaded yet
    with v3.VRow(v_if="!impact_analysis && !dependency_overview"):
        with v3.VCol(cols=12, classes="text-center py-8"):
            v3.VIcon("mdi-graph-outline", size="64", color="grey")
            html.P(
                "Select a rule above to analyze its impact",
                classes="text-grey mt-4",
                __properties=["data-testid"],
                **{"data-testid": "impact-empty-state"}
            )


def build_empty_state() -> None:
    """Build empty state when no rule is selected (legacy, kept for compatibility)."""
    pass
