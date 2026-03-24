"""
UI Navigation Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Tests for navigation configuration.
Per FEAT-008: Added routing coverage tests.
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


class TestNavigationRoutingCoverage:
    """FEAT-008: Verify all nav items have route registry entries."""

    @pytest.mark.unit
    def test_all_nav_items_routable(self):
        """Every NAVIGATION_ITEMS view must be registered in RouteRegistry."""
        from agent.governance_ui import NAVIGATION_ITEMS
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        missing = []
        for item in NAVIGATION_ITEMS:
            if not registry.is_known_view(item["value"]):
                missing.append(item["value"])
        assert missing == [], f"Nav items without route config: {missing}"

    @pytest.mark.unit
    def test_route_sync_js_exists(self):
        """route_sync.js should exist in static directory."""
        from pathlib import Path
        js_path = Path(__file__).parent.parent.parent.parent / \
            "agent" / "governance_ui" / "static" / "route_sync.js"
        assert js_path.exists(), f"Missing: {js_path}"

    @pytest.mark.unit
    def test_dashboard_injects_route_sync_js(self):
        """Dashboard build_ui should inject route_sync.js."""
        import inspect
        from agent.governance_dashboard import GovernanceDashboard
        source = inspect.getsource(GovernanceDashboard.build_ui)
        assert "route_sync.js" in source
