"""
Governance UI Handlers Module.

Per GAP-UI-ORPHAN-HANDLERS-001: Most handlers moved to controllers/.
Trace and rule detail handlers remain here.

Usage:
    from governance_ui.handlers import register_trace_bar_handlers
    register_trace_bar_handlers(ctrl, state)
"""

from .common_handlers import (
    register_trace_bar_handlers,
    register_rule_detail_handlers,
)

__all__ = [
    "register_trace_bar_handlers",
    "register_rule_detail_handlers",
]
