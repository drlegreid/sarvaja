"""
Governance UI Components Module.

Reusable UI components per RULE-012 (DSP Hygiene).
Per RULE-019: UI/UX Standards - consistent component patterns.

Usage:
    from governance_ui.components import build_navigation, build_status_banner
"""

from .navigation import build_navigation
from .dialogs import build_confirm_dialog, build_error_dialog
from .cards import build_entity_card, build_stat_card
from .list_styles import inject_list_styles

__all__ = [
    "build_navigation",
    "build_confirm_dialog",
    "build_error_dialog",
    "build_entity_card",
    "build_stat_card",
    "inject_list_styles",
]
