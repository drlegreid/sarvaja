"""
Agents View Subpackage.

Per RULE-012: DSP Hygiene - modular code structure.
Per RULE-032: File size limit (<300 lines per file).

This package splits the agents_view.py (464 lines) into focused modules:
- list.py: Agents list view (~72 lines)
- config.py: Agent configuration card (~82 lines)
- metrics.py: Metrics and trust history (~210 lines)
- relations.py: Agent relations card (~60 lines)
- detail.py: Agent detail view (~70 lines)
"""

from .list import build_agents_list_view
from .detail import build_agent_detail_view
from .capabilities import build_agent_capabilities_card

__all__ = [
    "build_agents_list_view",
    "build_agent_detail_view",
    "build_agent_capabilities_card",
]
