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

    @ctrl.set("analyze_rule_impact")
    def analyze_rule_impact(rule_id):
        """Analyze impact for selected rule (P9.4)."""
        if not rule_id:
            state.impact_selected_rule = None
            state.impact_analysis = None
            state.dependency_graph = None
            state.mermaid_diagram = ''
            return

        state.impact_selected_rule = rule_id
        # Calculate impact using pure functions
        impact = calculate_rule_impact(rule_id, state.rules)
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
