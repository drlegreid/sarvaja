"""
Data Access Layer for Governance UI
====================================
Re-exports from data_access/ package for backward compatibility.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Modularized 1170→~35 lines (97% reduction)

Original monolith extracted to:
- data_access/core.py - MCP registry, core data access
- data_access/backlog.py - Agent task backlog (TODO-6)
- data_access/filters.py - Filter & transform pure functions
- data_access/impact.py - Rule impact analysis (P9.4)
- data_access/trust.py - Agent trust dashboard (P9.5, RULE-011)
- data_access/monitoring.py - Real-time monitoring (P9.6)
- data_access/journey.py - Journey pattern analyzer (P9.7)
- data_access/executive.py - Executive reports (GAP-UI-044)

Created: 2024-12-28
"""

# Re-export everything from the package
from agent.governance_ui.data_access import *  # noqa: F401, F403

# Explicit re-exports for IDE support
