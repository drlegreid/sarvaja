"""
Integration tests for URI routing system.

Per FEAT-008: Named URI routing for dashboard navigation.
Per TEST-E2E-01-v1: Tier 2 integration tests.

Tests the full pipeline: URL hash → parse → RouteState → sync → state → build → URL hash
"""
import pytest


class MockState:
    """Simulates Trame state for integration testing."""

    def __init__(self, **kwargs):
        self._data = {
            "active_view": "rules",
            "selected_task": None,
            "selected_session": None,
            "selected_rule": None,
            "selected_agent": None,
            "selected_decision": None,
            "selected_workspace": None,
            "show_task_detail": False,
            "show_session_detail": False,
            "show_rule_detail": False,
            "show_agent_detail": False,
            "show_decision_detail": False,
            "show_workspace_detail": False,
            "nav_source_view": None,
            "nav_source_id": None,
            "nav_source_label": None,
            "current_project_id": None,
            "_pending_entity_id": None,
        }
        self._data.update(kwargs)

    def __getattr__(self, name):
        if name.startswith("_") and name != "_pending_entity_id":
            return super().__getattribute__(name)
        return self._data.get(name)

    def __setattr__(self, name, value):
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value


# =============================================================================
# Full Pipeline: URL → State → URL (Roundtrip)
# =============================================================================


class TestRoutingPipelineRoundtrip:
    """Full pipeline roundtrip: hash → state → hash."""

    @pytest.mark.integration
    def test_task_list_roundtrip(self):
        """Navigate to tasks list via URL, then verify hash regeneration."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState()

        # URL → State
        bridge.hash_to_state("#/projects/WS-9147535A/tasks", state)
        assert state.active_view == "tasks"
        assert state.show_task_detail is False

        # State → URL (should match original)
        result = bridge.state_to_hash(state)
        assert result == "#/projects/WS-9147535A/tasks"

    @pytest.mark.integration
    def test_task_detail_roundtrip(self):
        """Navigate to task detail via URL, simulate load, verify hash."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState()

        # URL → State
        bridge.hash_to_state("#/projects/WS-9147535A/tasks/FEAT-008", state)
        assert state.active_view == "tasks"
        assert state.show_task_detail is True
        assert state._pending_entity_id == "FEAT-008"

        # Simulate controller loading the task
        state.selected_task = {"task_id": "FEAT-008", "summary": "Named URI routing"}

        # State → URL (should regenerate same hash)
        result = bridge.state_to_hash(state)
        assert result == "#/projects/WS-9147535A/tasks/FEAT-008"

    @pytest.mark.integration
    def test_session_detail_roundtrip(self):
        """Session detail roundtrip."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState()

        session_id = "SESSION-2026-03-23-MCP-AUTO-abc123"
        bridge.hash_to_state(f"#/projects/WS-9147535A/sessions/{session_id}", state)
        assert state.active_view == "sessions"
        assert state.show_session_detail is True

        state.selected_session = {"session_id": session_id}
        result = bridge.state_to_hash(state)
        assert session_id in result

    @pytest.mark.integration
    def test_standalone_view_roundtrip(self):
        """Standalone views survive roundtrip."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        for view in ["executive", "monitor", "workflow", "chat", "trust",
                       "audit", "infra", "metrics"]:
            state = MockState()
            bridge.hash_to_state(f"#/{view}", state)
            assert state.active_view == view
            result = bridge.state_to_hash(state)
            assert result == f"#/{view}"


# =============================================================================
# Cross-Entity Navigation
# =============================================================================


class TestCrossEntityNavigation:
    """Test navigating between entities (sessions → tasks → rules)."""

    @pytest.mark.integration
    def test_sessions_to_task_detail(self):
        """Navigate from sessions view to task detail via URL."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState(active_view="sessions")

        # User clicks a task link — new hash pushed
        bridge.hash_to_state("#/projects/WS-9147535A/tasks/FEAT-008", state)
        assert state.active_view == "tasks"
        assert state.show_task_detail is True
        assert state._pending_entity_id == "FEAT-008"

    @pytest.mark.integration
    def test_task_to_session_detail(self):
        """Navigate from task detail to session detail."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState(active_view="tasks", show_task_detail=True)

        bridge.hash_to_state("#/projects/WS-9147535A/sessions/SESSION-123", state)
        assert state.active_view == "sessions"
        assert state.show_session_detail is True
        # Previous detail flags should be cleared
        assert state.show_task_detail is False

    @pytest.mark.integration
    def test_back_navigation_clears_detail(self):
        """Browser back (hash change) from detail to list clears flags."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState(
            active_view="tasks",
            show_task_detail=True,
            selected_task={"task_id": "FEAT-008"},
        )

        # User hits browser back — hash changes to list view
        bridge.hash_to_state("#/projects/WS-9147535A/tasks", state)
        assert state.active_view == "tasks"
        assert state.show_task_detail is False

    @pytest.mark.integration
    def test_view_switch_resets_all_detail_flags(self):
        """Switching views clears all detail flags."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState(
            active_view="tasks",
            show_task_detail=True,
            show_session_detail=True,
        )

        bridge.hash_to_state("#/projects/WS-9147535A/rules", state)
        assert state.active_view == "rules"
        assert state.show_task_detail is False
        assert state.show_session_detail is False
        assert state.show_rule_detail is False


# =============================================================================
# Registry ↔ Navigation Items Alignment
# =============================================================================


class TestRegistryNavigationAlignment:
    """Verify RouteRegistry stays aligned with NAVIGATION_ITEMS."""

    @pytest.mark.integration
    def test_every_nav_item_has_route(self):
        """All NAVIGATION_ITEMS views should be in RouteRegistry."""
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        for item in NAVIGATION_ITEMS:
            assert registry.is_known_view(item["value"]), \
                f"NAVIGATION_ITEMS view '{item['value']}' missing from RouteRegistry"

    @pytest.mark.integration
    def test_every_route_has_valid_segment(self):
        """All registered routes should have non-empty URI segments."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        for view in registry.all_views():
            segment = registry.get_segment(view)
            assert segment, f"View '{view}' has no URI segment"
            assert "/" not in segment, f"Segment '{segment}' shouldn't contain slashes"

    @pytest.mark.integration
    def test_segments_are_unique(self):
        """No two views should share the same URI segment."""
        from agent.governance_ui.routing.registry import RouteRegistry

        registry = RouteRegistry()
        seen = {}
        for view in registry.all_views():
            segment = registry.get_segment(view)
            assert segment not in seen, \
                f"Segment '{segment}' used by both '{seen[segment]}' and '{view}'"
            seen[segment] = view


# =============================================================================
# Edge Cases
# =============================================================================


class TestRoutingEdgeCases:
    """Edge cases and error handling in the routing pipeline."""

    @pytest.mark.integration
    def test_malformed_hash_defaults_gracefully(self):
        """Garbage hash should not crash, defaults to rules."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState()

        bridge.hash_to_state("#/garbage/invalid/path", state)
        assert state.active_view == "rules"

    @pytest.mark.integration
    def test_empty_hash_defaults_to_rules(self):
        """Empty hash defaults to rules view."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState(active_view="sessions")

        bridge.hash_to_state("", state)
        assert state.active_view == "rules"

    @pytest.mark.integration
    def test_entity_id_with_many_hyphens(self):
        """Complex entity IDs with many hyphens are preserved."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState()

        complex_id = "SESSION-2026-03-23-MCP-AUTO-abc123-def456"
        bridge.hash_to_state(
            f"#/projects/WS-9147535A/sessions/{complex_id}", state
        )
        assert state._pending_entity_id == complex_id

    @pytest.mark.integration
    def test_concurrent_detail_flags_impossible(self):
        """Only one detail flag should be True at a time."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        state = MockState()

        bridge.hash_to_state("#/projects/WS-9147535A/tasks/FEAT-008", state)
        assert state.show_task_detail is True
        assert state.show_session_detail is False
        assert state.show_rule_detail is False

        bridge.hash_to_state("#/projects/WS-9147535A/sessions/S-1", state)
        assert state.show_session_detail is True
        assert state.show_task_detail is False


# =============================================================================
# P13: Deep Link Entity Loading (SRVJ-FEAT-015)
# =============================================================================


class MockCtrl:
    """Minimal mock of Trame controller for integration tests."""

    def __init__(self):
        self.triggers = {}

    def trigger(self, name):
        def decorator(func):
            self.triggers[name] = func
            return func
        return decorator


class TestDeepLinkFullPipeline:
    """Integration: full deep link pipeline through routing controller."""

    @pytest.mark.integration
    @pytest.mark.parametrize("view,entity_id,load_patch,selected_attr,detail_flag", [
        ("tasks", "BUG-012", "agent.governance_ui.controllers.tasks_navigation._load_task_from_api",
         "selected_task", "show_task_detail"),
        ("sessions", "SESSION-X", "agent.governance_ui.controllers.tasks_navigation._load_session_from_api",
         "selected_session", "show_session_detail"),
    ])
    def test_same_view_deep_link_loads_entity(
        self, view, entity_id, load_patch, selected_attr, detail_flag,
    ):
        """Same-view hash change → entity loaded from API → state populated."""
        from unittest.mock import patch
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState(active_view=view)
        state._data["route_hash"] = ""
        state._data["cross_nav_in_progress"] = False
        ctrl = MockCtrl()

        with patch(load_patch) as mock_load:
            mock_load.return_value = {
                ("task_id" if view == "tasks" else "session_id"): entity_id,
            }
            register_routing_controller(state, ctrl, api_base_url="http://localhost:8082")
            ctrl.triggers["on_route_change"](
                f"#/projects/WS-9147535A/{view}/{entity_id}",
            )

        assert getattr(state, selected_attr) is not None
        assert getattr(state, detail_flag) is True
        assert state._pending_entity_id is None  # consumed
        assert state.route_hash != ""  # synced

    @pytest.mark.integration
    def test_cross_view_deep_link_preserves_pending_id(self):
        """Cross-view hash change → pending_id preserved for on_view_change."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState(active_view="rules")
        state._data["route_hash"] = ""
        state._data["cross_nav_in_progress"] = False
        ctrl = MockCtrl()

        register_routing_controller(state, ctrl, api_base_url="http://localhost:8082")
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/FEAT-008")

        assert state.active_view == "tasks"
        assert state._pending_entity_id == "FEAT-008"

    @pytest.mark.integration
    def test_same_view_back_to_list_detail_cleared(self):
        """Same-view back (#/tasks/X → #/tasks): detail cleared, route synced."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState(
            active_view="tasks",
            show_task_detail=True,
            selected_task={"task_id": "BUG-012"},
        )
        state._data["route_hash"] = ""
        state._data["cross_nav_in_progress"] = False
        ctrl = MockCtrl()

        register_routing_controller(state, ctrl, api_base_url="http://localhost:8082")
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks")

        assert state.show_task_detail is False
        assert state._pending_entity_id is None
        assert state.route_hash != ""

    @pytest.mark.integration
    def test_deep_link_back_forward_cycle(self):
        """Simulate: list → detail → back → forward cycle."""
        from unittest.mock import patch
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState(active_view="tasks")
        state._data["route_hash"] = ""
        state._data["cross_nav_in_progress"] = False
        ctrl = MockCtrl()

        task_data = {"task_id": "BUG-012", "name": "Test"}
        api = "http://localhost:8082"

        with patch(
            "agent.governance_ui.controllers.tasks_navigation._load_task_from_api",
            return_value=task_data,
        ):
            register_routing_controller(state, ctrl, api_base_url=api)

            # Step 1: Navigate to detail (same-view)
            ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/BUG-012")
            assert state.show_task_detail is True
            assert state.selected_task == task_data

            # Step 2: Browser back to list (same-view)
            ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks")
            assert state.show_task_detail is False

            # Step 3: Browser forward to detail again (same-view)
            ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/BUG-012")
            assert state.show_task_detail is True
            assert state.selected_task == task_data

    @pytest.mark.integration
    def test_deep_link_entity_not_found_shows_error(self):
        """Deep link to non-existent entity: error shown, detail cleared."""
        from unittest.mock import patch
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState(active_view="tasks")
        state._data["route_hash"] = ""
        state._data["cross_nav_in_progress"] = False
        state._data["has_error"] = False
        state._data["error_message"] = ""
        ctrl = MockCtrl()

        with patch(
            "agent.governance_ui.controllers.tasks_navigation._load_task_from_api",
            return_value=None,
        ):
            register_routing_controller(state, ctrl, api_base_url="http://localhost:8082")
            ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/GONE-001")

        assert state.show_task_detail is False
        assert state.has_error is True
        assert "GONE-001" in state.error_message
