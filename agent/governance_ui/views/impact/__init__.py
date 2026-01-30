"""
Impact View Subpackage.

Per RULE-032: File size limit - modularized impact view components.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Module structure:
- header.py: Impact header and rule selector (~55 lines)
- analysis.py: Risk summary and recommendation cards (~115 lines)
- views.py: Graph and list views (~140 lines)
"""

from .header import build_impact_header, build_rule_selector
from .analysis import (
    build_risk_summary_card,
    build_recommendation_card,
    build_analysis_results,
)
from .views import build_graph_view, build_list_view, build_empty_state, build_global_overview

__all__ = [
    "build_impact_header",
    "build_rule_selector",
    "build_risk_summary_card",
    "build_recommendation_card",
    "build_analysis_results",
    "build_graph_view",
    "build_list_view",
    "build_empty_state",
    "build_global_overview",
]
