"""
Unit tests for RouteRegistry (TDD — written before implementation).

Per FEAT-008: Named URI routing for dashboard navigation.
Per TEST-E2E-01-v1: Tier 1 unit tests.
"""
import pytest


class TestRouteRegistry:
    """Tests for RouteRegistry — single source of route config."""

    @pytest.mark.unit
    def test_registry_has_all_navigation_views(self):
        """Registry should cover all NAVIGATION_ITEMS views."""
        from agent.governance_ui.routing.registry import RouteRegistry
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS

        registry = RouteRegistry()
        nav_values = {item["value"] for item in NAVIGATION_ITEMS}

        for view in nav_values:
            assert registry.is_known_view(view), f"Missing route for view: {view}"

    @pytest.mark.unit
    def test_registry_entity_views(self):
        """Entity views (with detail pages) should be flagged."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        entity_views = ["tasks", "sessions", "rules", "agents", "decisions", "workspaces"]

        for view in entity_views:
            config = registry.get_config(view)
            assert config is not None, f"Missing config for {view}"
            assert config.has_detail is True, f"{view} should have detail"

    @pytest.mark.unit
    def test_registry_standalone_views(self):
        """Standalone views (no detail) flagged correctly."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        standalone = ["executive", "monitor", "workflow", "chat", "impact",
                       "trust", "audit", "infra", "metrics", "tests"]

        for view in standalone:
            config = registry.get_config(view)
            assert config is not None, f"Missing config for {view}"
            assert config.has_detail is False, f"{view} should NOT have detail"

    @pytest.mark.unit
    def test_registry_get_segment(self):
        """get_segment returns URI segment for view name."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        assert registry.get_segment("tasks") == "tasks"
        assert registry.get_segment("infra") == "infra"

    @pytest.mark.unit
    def test_registry_get_view_by_segment(self):
        """Reverse lookup: URI segment → view name."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        assert registry.get_view_by_segment("tasks") == "tasks"
        assert registry.get_view_by_segment("sessions") == "sessions"

    @pytest.mark.unit
    def test_registry_unknown_segment_returns_none(self):
        """Unknown segment returns None."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        assert registry.get_view_by_segment("nonexistent") is None

    @pytest.mark.unit
    def test_registry_unknown_view_returns_none(self):
        """Unknown view returns None for config."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        assert registry.get_config("nonexistent") is None

    @pytest.mark.unit
    def test_registry_is_singleton_data(self):
        """Two registries should have identical configs."""
        from agent.governance_ui.routing.registry import RouteRegistry

        r1 = RouteRegistry()
        r2 = RouteRegistry()
        assert r1.all_views() == r2.all_views()

    @pytest.mark.unit
    def test_registry_sub_views(self):
        """Tests view has 'reports' sub_view."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        config = registry.get_config("tests")
        assert config is not None
        assert "reports" in (config.sub_views or {})

    @pytest.mark.unit
    def test_registry_projects_is_special(self):
        """Projects view: entity view but also standalone list."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        config = registry.get_config("projects")
        assert config is not None
        # projects is a list view, shown standalone at #/projects
        assert config.standalone is True
