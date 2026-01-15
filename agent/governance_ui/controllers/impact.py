"""
Impact Analysis Controllers (GAP-FILE-005)
==========================================
Controller functions for rule impact analysis (P9.4).

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

from typing import Any

from agent.governance_ui import (
    calculate_rule_impact,
    build_dependency_graph,
    generate_mermaid_graph,
)


def register_impact_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register impact analysis controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls (unused but kept for consistency)
    """

    @state.change("impact_selected_rule")
    def on_impact_rule_change(impact_selected_rule, **kwargs):
        """React to rule selection changes (P9.4)."""
        if not impact_selected_rule:
            state.impact_analysis = None
            state.dependency_graph = None
            state.mermaid_diagram = ''
            return

        # Calculate impact using pure functions
        impact = calculate_rule_impact(impact_selected_rule, state.rules)
        state.impact_analysis = impact

        # Build dependency graph for selected rule
        graph = build_dependency_graph(state.rules)
        state.dependency_graph = graph

        # Generate Mermaid diagram
        mermaid = generate_mermaid_graph(graph)
        state.mermaid_diagram = mermaid

    @ctrl.set("toggle_graph_view")
    def toggle_graph_view():
        """Toggle between graph and list view."""
        state.show_graph_view = not state.show_graph_view
