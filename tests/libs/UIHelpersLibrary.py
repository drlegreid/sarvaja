"""
RF-004: Robot Framework Library for UI Helpers.

Wraps tests/unit/ui/test_ui_helpers.py for Robot Framework tests.
Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
"""

import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class UIHelpersLibrary:
    """Robot Framework library for UI Helpers testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def get_status_color(self) -> Dict[str, Any]:
        """Test get_status_color maps status to colors."""
        from agent.governance_ui import get_status_color

        return {
            "active": get_status_color('ACTIVE'),
            "draft": get_status_color('DRAFT'),
            "deprecated": get_status_color('DEPRECATED'),
            "unknown": get_status_color('unknown')
        }

    def get_priority_color(self) -> Dict[str, Any]:
        """Test get_priority_color maps priority to colors."""
        from agent.governance_ui import get_priority_color

        return {
            "critical": get_priority_color('CRITICAL'),
            "high": get_priority_color('HIGH'),
            "medium": get_priority_color('MEDIUM'),
            "low": get_priority_color('LOW')
        }

    def get_category_icon(self) -> Dict[str, Any]:
        """Test get_category_icon maps category to icons."""
        from agent.governance_ui import get_category_icon

        return {
            "governance": get_category_icon('governance'),
            "technical": get_category_icon('technical'),
            "unknown": get_category_icon('unknown')
        }

    def format_rule_card(self) -> Dict[str, Any]:
        """Test format_rule_card formats rule for display."""
        from agent.governance_ui import format_rule_card

        rule = {
            'rule_id': 'RULE-001',
            'title': 'Test Rule',
            'status': 'ACTIVE',
            'category': 'governance',
        }

        card = format_rule_card(rule)

        return {
            "has_title": 'title' in card,
            "has_subtitle": 'subtitle' in card,
            "has_color": 'color' in card,
            "has_icon": 'icon' in card
        }
