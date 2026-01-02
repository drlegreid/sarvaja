"""
Trust View Subpackage.

Per RULE-012: DSP Hygiene - modular code structure.
Per RULE-032: File size limit (<300 lines per file).

This package splits the trust_view.py (370 lines) into focused modules:
- stats.py: Header and governance stats (~85 lines)
- panels.py: Leaderboard and proposals (~140 lines)
- dashboard.py: Main dashboard layout (~40 lines)
- agent_detail.py: Agent detail view (~115 lines)
"""

from .dashboard import build_trust_dashboard_view
from .agent_detail import build_agent_detail_view

__all__ = [
    "build_trust_dashboard_view",
    "build_agent_detail_view",
]
