"""
State Management for Governance UI
===================================
Backward-compatible re-exports from modular state package.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-004: Refactored from 1547 lines to 11 modules (~98% reduction)

Original: 1547 lines
Refactored: ~30 lines (re-exports only)

Module structure in agent/governance_ui/state/:
    - constants.py: All color/icon constants (~180 lines)
    - initial.py: get_initial_state() factory (~130 lines)
    - core.py: Core transforms and helpers (~165 lines)
    - trust.py: Trust dashboard state (~115 lines)
    - monitor.py: Monitoring state (~115 lines)
    - journey.py: Journey analyzer state (~155 lines)
    - backlog.py: Task backlog state (~115 lines)
    - executive.py: Executive reports state (~145 lines)
    - chat.py: Agent chat state (~215 lines)
    - file_viewer.py: File viewer state (~75 lines)
    - execution.py: Task execution state (~80 lines)

Created: 2024-12-25
Updated: 2024-12-28 - Modularized per RULE-012

Usage remains unchanged:
    from agent.governance_ui.state import get_initial_state, with_loading
    from agent.governance_ui.state import STATUS_COLORS, NAVIGATION_ITEMS
"""

# Re-export everything from the state package for backward compatibility
from agent.governance_ui.state import *  # noqa: F401, F403
