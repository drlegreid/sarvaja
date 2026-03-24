"""
Unit tests for Route models (TDD — written before implementation).

Per FEAT-008: Named URI routing for dashboard navigation.
Per TEST-E2E-01-v1: Tier 1 unit tests.
"""
import pytest


class TestRouteState:
    """Tests for RouteState dataclass."""

    @pytest.mark.unit
    def test_route_state_creation_minimal(self):
        """RouteState can be created with just a view."""
        from agent.governance_ui.routing.models import RouteState

        route = RouteState(view="tasks")
        assert route.view == "tasks"
        assert route.entity_id is None
        assert route.project_id is None

    @pytest.mark.unit
    def test_route_state_creation_full(self):
        """RouteState can be created with all fields."""
        from agent.governance_ui.routing.models import RouteState

        route = RouteState(
            view="tasks",
            entity_id="FEAT-008",
            project_id="WS-9147535A",
        )
        assert route.view == "tasks"
        assert route.entity_id == "FEAT-008"
        assert route.project_id == "WS-9147535A"

    @pytest.mark.unit
    def test_route_state_is_detail(self):
        """is_detail should be True when entity_id is present."""
        from agent.governance_ui.routing.models import RouteState

        list_route = RouteState(view="tasks")
        detail_route = RouteState(view="tasks", entity_id="FEAT-008")

        assert list_route.is_detail is False
        assert detail_route.is_detail is True

    @pytest.mark.unit
    def test_route_state_equality(self):
        """Two RouteStates with same values should be equal."""
        from agent.governance_ui.routing.models import RouteState

        r1 = RouteState(view="tasks", entity_id="FEAT-008")
        r2 = RouteState(view="tasks", entity_id="FEAT-008")
        assert r1 == r2

    @pytest.mark.unit
    def test_route_state_inequality(self):
        """RouteStates with different values should not be equal."""
        from agent.governance_ui.routing.models import RouteState

        r1 = RouteState(view="tasks", entity_id="FEAT-008")
        r2 = RouteState(view="sessions", entity_id="SESSION-123")
        assert r1 != r2

    @pytest.mark.unit
    def test_route_state_immutable(self):
        """RouteState should be frozen (immutable)."""
        from agent.governance_ui.routing.models import RouteState

        route = RouteState(view="tasks")
        with pytest.raises(AttributeError):
            route.view = "sessions"

    @pytest.mark.unit
    def test_route_state_nested_path(self):
        """RouteState supports nested views like tests/reports."""
        from agent.governance_ui.routing.models import RouteState

        route = RouteState(
            view="tests",
            sub_view="reports",
            entity_id="RPT-001",
        )
        assert route.view == "tests"
        assert route.sub_view == "reports"
        assert route.entity_id == "RPT-001"


class TestRouteConfig:
    """Tests for RouteConfig (view metadata)."""

    @pytest.mark.unit
    def test_route_config_creation(self):
        """RouteConfig stores view-to-segment mapping."""
        from agent.governance_ui.routing.models import RouteConfig

        config = RouteConfig(
            view_name="tasks",
            uri_segment="tasks",
            has_detail=True,
        )
        assert config.view_name == "tasks"
        assert config.uri_segment == "tasks"
        assert config.has_detail is True

    @pytest.mark.unit
    def test_route_config_standalone_view(self):
        """Standalone views (no detail) like executive."""
        from agent.governance_ui.routing.models import RouteConfig

        config = RouteConfig(
            view_name="executive",
            uri_segment="executive",
            has_detail=False,
        )
        assert config.has_detail is False

    @pytest.mark.unit
    def test_route_config_nested_segments(self):
        """Nested segments like tests/reports."""
        from agent.governance_ui.routing.models import RouteConfig

        config = RouteConfig(
            view_name="tests",
            uri_segment="tests",
            has_detail=False,
            sub_views={"reports": "reports"},
        )
        assert config.sub_views == {"reports": "reports"}
