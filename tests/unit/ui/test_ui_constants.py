"""
UI Constants Export Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Tests that constants are properly exported.
"""
import pytest


class TestConstantsExport:
    """Tests that constants are properly exported."""

    @pytest.mark.unit
    def test_status_colors_exported(self):
        """STATUS_COLORS should be exported."""
        from agent.governance_ui import STATUS_COLORS
        assert isinstance(STATUS_COLORS, dict)

    @pytest.mark.unit
    def test_priority_colors_exported(self):
        """PRIORITY_COLORS should be exported."""
        from agent.governance_ui import PRIORITY_COLORS
        assert isinstance(PRIORITY_COLORS, dict)

    @pytest.mark.unit
    def test_category_icons_exported(self):
        """CATEGORY_ICONS should be exported."""
        from agent.governance_ui import CATEGORY_ICONS
        assert isinstance(CATEGORY_ICONS, dict)

    @pytest.mark.unit
    def test_rule_categories_exported(self):
        """RULE_CATEGORIES should be exported."""
        from agent.governance_ui import RULE_CATEGORIES
        assert isinstance(RULE_CATEGORIES, list)

    @pytest.mark.unit
    def test_rule_priorities_exported(self):
        """RULE_PRIORITIES should be exported."""
        from agent.governance_ui import RULE_PRIORITIES
        assert isinstance(RULE_PRIORITIES, list)

    @pytest.mark.unit
    def test_rule_statuses_exported(self):
        """RULE_STATUSES should be exported."""
        from agent.governance_ui import RULE_STATUSES
        assert isinstance(RULE_STATUSES, list)
