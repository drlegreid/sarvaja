"""
Governance UI Handlers Module.

Modular handler factories for UI actions per RULE-012 (DSP Hygiene).
Each entity has its own handler module following Single Responsibility Principle.

Usage:
    from governance_ui.handlers import register_rule_handlers
    register_rule_handlers(ctrl, state)
"""

from .rule_handlers import register_rule_handlers
from .task_handlers import register_task_handlers
from .session_handlers import register_session_handlers
from .common_handlers import register_common_handlers

__all__ = [
    "register_rule_handlers",
    "register_task_handlers",
    "register_session_handlers",
    "register_common_handlers",
]
