"""
Agents View for Governance Dashboard.

Per RULE-012: Single Responsibility - only agents list/detail UI.
Per RULE-019: UI/UX Standards - consistent view patterns.
Per RULE-032: File size limit - modularized into agents/ subpackage.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Module structure (RULE-032 compliant):
- agents/list.py: List view (~72 lines)
- agents/config.py: Agent configuration card (~82 lines)
- agents/metrics.py: Metrics and trust history (~210 lines)
- agents/relations.py: Agent relations card (~60 lines)
- agents/detail.py: Agent detail view (~70 lines)
"""

from .agents import build_agents_list_view, build_agent_detail_view


def build_agents_view() -> None:
    """
    Build the complete Agents view including list and detail.

    This is the main entry point for the agents view module.
    """
    build_agents_list_view()
    build_agent_detail_view()
