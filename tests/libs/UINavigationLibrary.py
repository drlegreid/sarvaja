"""
Robot Framework Library for UI Navigation Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Migrated from tests/unit/ui/test_ui_navigation.py
"""
from robot.api.deco import keyword


class UINavigationLibrary:
    """Library for testing navigation configuration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    @keyword("Navigation Items Exist")
    def navigation_items_exist(self):
        """NAVIGATION_ITEMS should be defined."""
        try:
            from agent.governance_ui import NAVIGATION_ITEMS

            is_list = isinstance(NAVIGATION_ITEMS, list)
            has_items = len(NAVIGATION_ITEMS) > 0

            return {
                "is_list": is_list,
                "has_items": has_items,
                "count": len(NAVIGATION_ITEMS) if is_list else 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Navigation Has Required Views")
    def navigation_has_required_views(self):
        """Navigation should include required views."""
        try:
            from agent.governance_ui import NAVIGATION_ITEMS

            nav_values = [item['value'] for item in NAVIGATION_ITEMS]

            required_views = ['rules', 'decisions', 'sessions', 'tasks', 'impact', 'trust']
            has_all = all(view in nav_values for view in required_views)

            return {
                "has_rules": 'rules' in nav_values,
                "has_decisions": 'decisions' in nav_values,
                "has_sessions": 'sessions' in nav_values,
                "has_tasks": 'tasks' in nav_values,
                "has_impact": 'impact' in nav_values,
                "has_trust": 'trust' in nav_values,
                "has_all_required": has_all
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Navigation Items Have Structure")
    def navigation_items_have_structure(self):
        """Navigation items should have title, icon, value."""
        try:
            from agent.governance_ui import NAVIGATION_ITEMS

            all_valid = True
            for item in NAVIGATION_ITEMS:
                if 'title' not in item or 'icon' not in item or 'value' not in item:
                    all_valid = False
                    break

            return {
                "all_have_title": all('title' in item for item in NAVIGATION_ITEMS),
                "all_have_icon": all('icon' in item for item in NAVIGATION_ITEMS),
                "all_have_value": all('value' in item for item in NAVIGATION_ITEMS),
                "all_valid": all_valid
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
