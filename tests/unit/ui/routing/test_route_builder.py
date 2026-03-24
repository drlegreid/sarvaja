"""
Unit tests for Route builder (TDD — written before implementation).

Per FEAT-008: Named URI routing for dashboard navigation.
Per TEST-E2E-01-v1: Tier 1 unit tests.
"""
import pytest


class TestBuildHash:
    """Tests for build_hash() — converts RouteState to URL hash."""

    @pytest.mark.unit
    def test_build_default_route(self):
        """Default route produces empty or root hash."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash

        route = RouteState(view="rules")
        assert build_hash(route) == "#/rules"

    @pytest.mark.unit
    def test_build_list_view_with_project(self):
        """List view with project context."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash

        route = RouteState(view="tasks", project_id="WS-9147535A")
        assert build_hash(route) == "#/projects/WS-9147535A/tasks"

    @pytest.mark.unit
    def test_build_detail_view(self):
        """Detail view with project + entity."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash

        route = RouteState(
            view="tasks",
            entity_id="FEAT-008",
            project_id="WS-9147535A",
        )
        assert build_hash(route) == "#/projects/WS-9147535A/tasks/FEAT-008"

    @pytest.mark.unit
    def test_build_session_detail(self):
        """Session detail hash."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash

        route = RouteState(
            view="sessions",
            entity_id="SESSION-2026-03-23",
            project_id="WS-9147535A",
        )
        assert build_hash(route) == "#/projects/WS-9147535A/sessions/SESSION-2026-03-23"

    @pytest.mark.unit
    def test_build_standalone_view(self):
        """Standalone view (no project, no entity)."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash

        route = RouteState(view="executive")
        assert build_hash(route) == "#/executive"

    @pytest.mark.unit
    def test_build_nested_tests_reports(self):
        """Nested view: tests/reports/{id}."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash

        route = RouteState(
            view="tests",
            sub_view="reports",
            entity_id="RPT-001",
            project_id="WS-9147535A",
        )
        assert build_hash(route) == "#/projects/WS-9147535A/tests/reports/RPT-001"

    @pytest.mark.unit
    def test_build_preserves_complex_entity_id(self):
        """Entity IDs with many hyphens are preserved."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash

        route = RouteState(
            view="sessions",
            entity_id="SESSION-2026-03-23-MCP-AUTO-abc123",
            project_id="WS-9147535A",
        )
        expected = "#/projects/WS-9147535A/sessions/SESSION-2026-03-23-MCP-AUTO-abc123"
        assert build_hash(route) == expected

    @pytest.mark.unit
    def test_build_projects_list(self):
        """Projects list view."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash

        route = RouteState(view="projects")
        assert build_hash(route) == "#/projects"


class TestRoundTrip:
    """Parse → build and build → parse should be identity."""

    @pytest.mark.unit
    def test_roundtrip_list_view(self):
        """parse(build(route)) == route for list views."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash
        from agent.governance_ui.routing.parser import parse_hash

        original = RouteState(view="tasks", project_id="WS-9147535A")
        rebuilt = parse_hash(build_hash(original))
        assert rebuilt.view == original.view
        assert rebuilt.project_id == original.project_id

    @pytest.mark.unit
    def test_roundtrip_detail_view(self):
        """parse(build(route)) == route for detail views."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash
        from agent.governance_ui.routing.parser import parse_hash

        original = RouteState(
            view="tasks",
            entity_id="FEAT-008",
            project_id="WS-9147535A",
        )
        rebuilt = parse_hash(build_hash(original))
        assert rebuilt.view == original.view
        assert rebuilt.entity_id == original.entity_id
        assert rebuilt.project_id == original.project_id

    @pytest.mark.unit
    def test_roundtrip_nested_view(self):
        """parse(build(route)) == route for nested views."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash
        from agent.governance_ui.routing.parser import parse_hash

        original = RouteState(
            view="tests",
            sub_view="reports",
            entity_id="RPT-001",
            project_id="WS-9147535A",
        )
        rebuilt = parse_hash(build_hash(original))
        assert rebuilt.view == original.view
        assert rebuilt.sub_view == original.sub_view
        assert rebuilt.entity_id == original.entity_id

    @pytest.mark.unit
    def test_roundtrip_standalone(self):
        """parse(build(route)) for standalone views."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash
        from agent.governance_ui.routing.parser import parse_hash

        for view in ["executive", "monitor", "workflow", "chat"]:
            original = RouteState(view=view)
            rebuilt = parse_hash(build_hash(original))
            assert rebuilt.view == original.view, f"Failed roundtrip for {view}"

    @pytest.mark.unit
    def test_roundtrip_all_entity_views(self):
        """Roundtrip for all entity views with detail."""
        from agent.governance_ui.routing.models import RouteState
        from agent.governance_ui.routing.builder import build_hash
        from agent.governance_ui.routing.parser import parse_hash

        entity_views = {
            "tasks": "FEAT-008",
            "sessions": "SESSION-2026-03-23",
            "rules": "TEST-GUARD-01",
            "agents": "code-agent",
            "decisions": "DECISION-003",
            "workspaces": "WS-ABCDEF",
        }
        for view, entity_id in entity_views.items():
            original = RouteState(
                view=view,
                entity_id=entity_id,
                project_id="WS-9147535A",
            )
            rebuilt = parse_hash(build_hash(original))
            assert rebuilt.view == original.view, f"View mismatch for {view}"
            assert rebuilt.entity_id == original.entity_id, f"Entity mismatch for {view}"
