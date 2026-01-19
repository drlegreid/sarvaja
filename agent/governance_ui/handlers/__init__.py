"""
Governance UI Handlers Module.

Per GAP-UI-ORPHAN-HANDLERS-001: Most handlers moved to controllers/.
Only trace_bar_handlers remains here as it's used by controllers/__init__.py.

Usage:
    from governance_ui.handlers import register_trace_bar_handlers
    register_trace_bar_handlers(ctrl, state)
"""

from .common_handlers import register_trace_bar_handlers

__all__ = [
    "register_trace_bar_handlers",
]
