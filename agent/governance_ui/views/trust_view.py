"""
Trust View for Governance Dashboard.

Per RULE-012: Single Responsibility - only trust scores/leaderboard UI.
Per RULE-011: Multi-Agent Governance Protocol.
Per RULE-032: File size limit - modularized into trust/ subpackage.
Per GAP-FILE-001: Modularization of governance_dashboard.py.

Module structure (RULE-032 compliant):
- trust/stats.py: Header and governance stats (~85 lines)
- trust/panels.py: Leaderboard and proposals (~140 lines)
- trust/dashboard.py: Main dashboard layout (~40 lines)
- trust/agent_detail.py: Agent detail view (~115 lines)
"""

from .trust import build_trust_dashboard_view, build_agent_detail_view


def build_trust_view() -> None:
    """
    Build the complete Trust Dashboard view.

    This is the main entry point for the trust view module.
    Per RULE-011: Multi-Agent Governance Protocol.
    Per P9.5: Trust Dashboard implementation.
    """
    build_trust_dashboard_view()
    build_agent_detail_view()
