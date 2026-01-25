"""
RF-004: Robot Framework Library for UI Constants.

Wraps tests/unit/ui/test_ui_constants.py for Robot Framework tests.
Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
"""

import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class UIConstantsLibrary:
    """Robot Framework library for UI Constants testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def status_colors_exported(self) -> Dict[str, Any]:
        """Test STATUS_COLORS is exported."""
        from agent.governance_ui import STATUS_COLORS
        return {
            "is_dict": isinstance(STATUS_COLORS, dict),
            "count": len(STATUS_COLORS)
        }

    def priority_colors_exported(self) -> Dict[str, Any]:
        """Test PRIORITY_COLORS is exported."""
        from agent.governance_ui import PRIORITY_COLORS
        return {
            "is_dict": isinstance(PRIORITY_COLORS, dict),
            "count": len(PRIORITY_COLORS)
        }

    def category_icons_exported(self) -> Dict[str, Any]:
        """Test CATEGORY_ICONS is exported."""
        from agent.governance_ui import CATEGORY_ICONS
        return {
            "is_dict": isinstance(CATEGORY_ICONS, dict),
            "count": len(CATEGORY_ICONS)
        }

    def rule_categories_exported(self) -> Dict[str, Any]:
        """Test RULE_CATEGORIES is exported."""
        from agent.governance_ui import RULE_CATEGORIES
        return {
            "is_list": isinstance(RULE_CATEGORIES, list),
            "count": len(RULE_CATEGORIES)
        }

    def rule_priorities_exported(self) -> Dict[str, Any]:
        """Test RULE_PRIORITIES is exported."""
        from agent.governance_ui import RULE_PRIORITIES
        return {
            "is_list": isinstance(RULE_PRIORITIES, list),
            "count": len(RULE_PRIORITIES)
        }

    def rule_statuses_exported(self) -> Dict[str, Any]:
        """Test RULE_STATUSES is exported."""
        from agent.governance_ui import RULE_STATUSES
        return {
            "is_list": isinstance(RULE_STATUSES, list),
            "count": len(RULE_STATUSES)
        }
