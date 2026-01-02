"""
Impact View for Governance Dashboard.

Per RULE-012: Single Responsibility - only rule impact analysis UI.
Per RULE-032: File size limit - modularized into impact/ subpackage.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Module structure (RULE-032 compliant):
- impact/header.py: Impact header and rule selector (~55 lines)
- impact/analysis.py: Risk summary and recommendation cards (~115 lines)
- impact/views.py: Graph and list views (~140 lines)
"""

from trame.widgets import vuetify3 as v3

from .impact import (
    build_impact_header,
    build_rule_selector,
    build_analysis_results,
    build_graph_view,
    build_list_view,
    build_empty_state,
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
