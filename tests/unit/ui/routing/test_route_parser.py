"""
Unit tests for Route parser (TDD — written before implementation).

Per FEAT-008: Named URI routing for dashboard navigation.
Per TEST-E2E-01-v1: Tier 1 unit tests.
"""
import pytest


class TestParseHash:
    """Tests for parse_hash() — converts URL hash to RouteState."""

    @pytest.mark.unit
    def test_parse_empty_hash(self):
        """Empty hash returns default route (rules list)."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("")
        assert route.view == "rules"
        assert route.entity_id is None

    @pytest.mark.unit
    def test_parse_bare_hash(self):
        """Bare '#' returns default route."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#")
        assert route.view == "rules"

    @pytest.mark.unit
    def test_parse_root_hash(self):
        """'#/' returns default route."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/")
        assert route.view == "rules"

    @pytest.mark.unit
    def test_parse_list_view(self):
        """Parse a simple list view: #/projects/{id}/tasks."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/tasks")
        assert route.view == "tasks"
        assert route.project_id == "WS-9147535A"
        assert route.entity_id is None

    @pytest.mark.unit
    def test_parse_detail_view(self):
        """Parse a detail view: #/projects/{id}/tasks/{task_id}."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/tasks/FEAT-008")
        assert route.view == "tasks"
        assert route.project_id == "WS-9147535A"
        assert route.entity_id == "FEAT-008"
        assert route.is_detail is True

    @pytest.mark.unit
    def test_parse_sessions_detail(self):
        """Parse session detail: #/projects/{id}/sessions/{session_id}."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/sessions/SESSION-2026-03-23")
        assert route.view == "sessions"
        assert route.entity_id == "SESSION-2026-03-23"

    @pytest.mark.unit
    def test_parse_rules_detail(self):
        """Parse rule detail: #/projects/{id}/rules/{rule_id}."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/rules/TEST-GUARD-01")
        assert route.view == "rules"
        assert route.entity_id == "TEST-GUARD-01"

    @pytest.mark.unit
    def test_parse_agents_detail(self):
        """Parse agent detail."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/agents/code-agent")
        assert route.view == "agents"
        assert route.entity_id == "code-agent"

    @pytest.mark.unit
    def test_parse_decisions_detail(self):
        """Parse decision detail."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/decisions/DECISION-003")
        assert route.view == "decisions"
        assert route.entity_id == "DECISION-003"

    @pytest.mark.unit
    def test_parse_nested_tests_reports(self):
        """Parse nested: #/projects/{id}/tests/reports/{report_id}."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/tests/reports/RPT-001")
        assert route.view == "tests"
        assert route.sub_view == "reports"
        assert route.entity_id == "RPT-001"

    @pytest.mark.unit
    def test_parse_standalone_view(self):
        """Parse standalone view without project: #/executive."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/executive")
        assert route.view == "executive"
        assert route.project_id is None
        assert route.entity_id is None

    @pytest.mark.unit
    def test_parse_monitor_standalone(self):
        """Standalone views: monitor, workflow, metrics, etc."""
        from agent.governance_ui.routing.parser import parse_hash

        for view in ["monitor", "workflow", "metrics", "infra", "audit", "chat"]:
            route = parse_hash(f"#/{view}")
            assert route.view == view, f"Failed for {view}"

    @pytest.mark.unit
    def test_parse_unknown_view_returns_default(self):
        """Unknown view segment returns default route."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/nonexistent")
        assert route.view == "rules"

    @pytest.mark.unit
    def test_parse_without_hash_prefix(self):
        """Parser handles paths without # prefix gracefully."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("/projects/WS-9147535A/tasks/FEAT-008")
        assert route.view == "tasks"
        assert route.entity_id == "FEAT-008"

    @pytest.mark.unit
    def test_parse_preserves_entity_id_with_hyphens(self):
        """Entity IDs with hyphens (SESSION-2026-03-23-MCP-AUTO-xxx) preserved."""
        from agent.governance_ui.routing.parser import parse_hash

        session_id = "SESSION-2026-03-23-MCP-AUTO-abc123"
        route = parse_hash(f"#/projects/WS-9147535A/sessions/{session_id}")
        assert route.entity_id == session_id

    @pytest.mark.unit
    def test_parse_trims_trailing_slash(self):
        """Trailing slash is ignored."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/tasks/")
        assert route.view == "tasks"
        assert route.entity_id is None

    @pytest.mark.unit
    def test_parse_workspaces_view(self):
        """Workspaces is a valid entity view."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects/WS-9147535A/workspaces/WS-ABCDEF")
        assert route.view == "workspaces"
        assert route.entity_id == "WS-ABCDEF"

    @pytest.mark.unit
    def test_parse_projects_list(self):
        """Projects list (no project context needed)."""
        from agent.governance_ui.routing.parser import parse_hash

        route = parse_hash("#/projects")
        assert route.view == "projects"
        assert route.project_id is None
