"""
UI Navigation Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Tests for navigation configuration.
"""
import pytest


class TestNavigationItems:
    """Tests for navigation configuration."""

    @pytest.mark.unit
    def test_navigation_items_exist(self):
        """NAVIGATION_ITEMS should be defined."""
        from agent.governance_ui import NAVIGATION_ITEMS

        assert isinstance(NAVIGATION_ITEMS, list)
        assert len(NAVIGATION_ITEMS) > 0

    @pytest.mark.unit
    def test_navigation_has_required_views(self):
        """Navigation should include required views."""
        from agent.governance_ui import NAVIGATION_ITEMS

        nav_values = [item['value'] for item in NAVIGATION_ITEMS]

        assert 'rules' in nav_values
        assert 'decisions' in nav_values
        assert 'sessions' in nav_values
        assert 'tasks' in nav_values
        assert 'impact' in nav_values
        assert 'trust' in nav_values

    @pytest.mark.unit
    def test_navigation_items_have_structure(self):
        """Navigation items should have title, icon, value."""
        from agent.governance_ui import NAVIGATION_ITEMS

        for item in NAVIGATION_ITEMS:
            assert 'title' in item
            assert 'icon' in item
            assert 'value' in item
