"""
Unit tests for deep link entity loading (P13: URL-Based Entity Routing).

Per TEST-FIX-01-v1: TDD — tests define contract before implementation.
Per FEAT-008: Named URI routing for dashboard navigation.
Per SRVJ-FEAT-015: Same-view deep link entity loading.
Per SRVJ-FEAT-016: Cross-nav route hash push.

Tests:
1. Same-view entity loading from route change (task + session)
2. Entity not found shows error
3. Same-view back clears detail
4. Same-view syncs route_hash to prevent JS overwrite
5. Cross-view delegates to on_view_change (no duplicate loading)
6. _load_entity_for_deep_link helper
"""

import pytest
from unittest.mock import patch, MagicMock


class MockState:
    """Minimal mock of Trame state for routing tests."""

    def __init__(self, **kwargs):
        self._data = {
            "active_view": "rules",
            "route_hash": "",
            "cross_nav_in_progress": False,
            "_pending_entity_id": None,
            "show_task_detail": False,
            "show_session_detail": False,
            "show_rule_detail": False,
            "show_agent_detail": False,
            "show_decision_detail": False,
            "show_workspace_detail": False,
            "selected_task": None,
            "selected_session": None,
            "current_project_id": "WS-9147535A",
            "has_error": False,
            "error_message": "",
        }
        self._data.update(kwargs)

    def __getattr__(self, name):
        if name.startswith("_") and name != "_pending_entity_id":
            return super().__getattribute__(name)
        return self._data.get(name)

    def __setattr__(self, name, value):
        if name.startswith("_") and name != "_pending_entity_id":
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def dirty(self, key):
        pass


class MockCtrl:
    """Minimal mock of Trame controller."""

    def __init__(self):
        self.triggers = {}

    def trigger(self, name):
        def decorator(func):
            self.triggers[name] = func
            return func
        return decorator


@pytest.fixture
def state():
    return MockState()


@pytest.fixture
def ctrl():
    return MockCtrl()


API_URL = "http://localhost:8082"


# =============================================================================
# Test: Same-view entity loading (SRVJ-FEAT-015)
# =============================================================================
class TestSameViewEntityLoading:
    """When hash changes within the same view, on_route_change must load entity."""

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_same_view_task_detail_loads_entity(self, mock_load, state, ctrl):
        """#/tasks -> #/tasks/BUG-012: entity loaded from API."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        mock_load.return_value = {"task_id": "BUG-012", "name": "Test"}
        state.active_view = "tasks"

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/BUG-012")

        mock_load.assert_called_once_with(API_URL, "BUG-012")
        assert state.selected_task == {"task_id": "BUG-012", "name": "Test"}
        assert state.show_task_detail is True

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_session_from_api")
    def test_same_view_session_detail_loads_entity(self, mock_load, state, ctrl):
        """#/sessions -> #/sessions/SESSION-X: entity loaded from API."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        mock_load.return_value = {"session_id": "SESSION-X", "topic": "Test"}
        state.active_view = "sessions"

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/sessions/SESSION-X")

        mock_load.assert_called_once_with(API_URL, "SESSION-X")
        assert state.selected_session == {"session_id": "SESSION-X", "topic": "Test"}
        assert state.show_session_detail is True

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_same_view_clears_pending_entity_id(self, mock_load, state, ctrl):
        """Same-view nav must clear _pending_entity_id after consuming it."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        mock_load.return_value = {"task_id": "X", "name": "X"}
        state.active_view = "tasks"

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/X")

        assert state._pending_entity_id is None

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_complex_entity_id_preserved(self, mock_load, state, ctrl):
        """Entity IDs with many hyphens (sessions) are preserved."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        cid = "SESSION-2026-03-23-MCP-AUTO-abc123"
        mock_load.return_value = None  # Won't find it as task, that's OK
        state.active_view = "sessions"

        register_routing_controller(state, ctrl, api_base_url=API_URL)

        with patch(
            "agent.governance_ui.controllers.tasks_navigation._load_session_from_api"
        ) as mock_sess:
            mock_sess.return_value = {"session_id": cid, "topic": "Auto"}
            ctrl.triggers["on_route_change"](
                f"#/projects/WS-9147535A/sessions/{cid}"
            )
            mock_sess.assert_called_once_with(API_URL, cid)


# =============================================================================
# Test: Same-view back to list (browser back button)
# =============================================================================
class TestSameViewBackToList:
    """Browser back from detail to list within same view."""

    @pytest.mark.unit
    def test_back_to_task_list_clears_detail(self, state, ctrl):
        """#/tasks/BUG-012 -> #/tasks: detail flag cleared."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state.active_view = "tasks"
        state.show_task_detail = True
        state.selected_task = {"task_id": "BUG-012"}

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks")

        assert state.show_task_detail is False
        assert state._pending_entity_id is None

    @pytest.mark.unit
    def test_back_to_session_list_clears_detail(self, state, ctrl):
        """#/sessions/SESSION-X -> #/sessions: detail flag cleared."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state.active_view = "sessions"
        state.show_session_detail = True
        state.selected_session = {"session_id": "SESSION-X"}

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/sessions")

        assert state.show_session_detail is False


# =============================================================================
# Test: Same-view syncs route_hash
# =============================================================================
class TestSameViewRouteHashSync:
    """Same-view nav must update route_hash to prevent JS polling overwrite."""

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_route_hash_updated_on_same_view_detail(self, mock_load, state, ctrl):
        """route_hash reflects new state after same-view detail nav."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        mock_load.return_value = {"task_id": "BUG-012", "name": "X"}
        state.active_view = "tasks"

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/BUG-012")

        assert state.route_hash != ""
        assert "tasks" in state.route_hash

    @pytest.mark.unit
    def test_route_hash_updated_on_same_view_list(self, state, ctrl):
        """route_hash reflects list state after same-view back nav."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state.active_view = "tasks"
        state.show_task_detail = True

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks")

        assert state.route_hash != ""
        assert "tasks" in state.route_hash


# =============================================================================
# Test: Cross-view delegates to on_view_change (no duplicate load)
# =============================================================================
class TestCrossViewDelegation:
    """When view changes, on_route_change should NOT load entity directly."""

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_cross_view_does_not_call_load(self, mock_load, state, ctrl):
        """rules -> tasks/BUG-012: entity load deferred to on_view_change."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state.active_view = "rules"  # Different from target 'tasks'

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/BUG-012")

        # Should NOT call load — on_view_change will handle via _pending_entity_id
        mock_load.assert_not_called()

    @pytest.mark.unit
    def test_cross_view_preserves_pending_entity_id(self, state, ctrl):
        """Cross-view nav keeps _pending_entity_id for on_view_change."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state.active_view = "rules"

        register_routing_controller(state, ctrl, api_base_url=API_URL)
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/BUG-012")

        # pending_id preserved for on_view_change to consume
        assert state._pending_entity_id == "BUG-012"


# =============================================================================
# Test: _load_entity_for_deep_link helper
# =============================================================================
class TestLoadEntityForDeepLink:
    """Unit tests for the entity loading helper function."""

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_loads_task_sets_state(self, mock_load, state):
        """Task entity loaded and state populated."""
        from agent.governance_ui.controllers.routing import _load_entity_for_deep_link

        mock_load.return_value = {"task_id": "BUG-012", "name": "Test"}
        _load_entity_for_deep_link(state, API_URL, "tasks", "BUG-012")

        assert state.selected_task == {"task_id": "BUG-012", "name": "Test"}
        assert state.show_task_detail is True
        assert state.has_error is False

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_session_from_api")
    def test_loads_session_sets_state(self, mock_load, state):
        """Session entity loaded and state populated."""
        from agent.governance_ui.controllers.routing import _load_entity_for_deep_link

        mock_load.return_value = {"session_id": "SESSION-X", "topic": "Test"}
        _load_entity_for_deep_link(state, API_URL, "sessions", "SESSION-X")

        assert state.selected_session == {"session_id": "SESSION-X", "topic": "Test"}
        assert state.show_session_detail is True
        assert state.has_error is False

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_task_not_found_shows_error(self, mock_load, state):
        """404 task: detail cleared, error shown."""
        from agent.governance_ui.controllers.routing import _load_entity_for_deep_link

        mock_load.return_value = None
        _load_entity_for_deep_link(state, API_URL, "tasks", "GONE-001")

        assert state.show_task_detail is False
        assert state.has_error is True
        assert "GONE-001" in state.error_message

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_session_from_api")
    def test_session_not_found_shows_error(self, mock_load, state):
        """404 session: detail cleared, error shown."""
        from agent.governance_ui.controllers.routing import _load_entity_for_deep_link

        mock_load.return_value = None
        _load_entity_for_deep_link(state, API_URL, "sessions", "GONE-002")

        assert state.show_session_detail is False
        assert state.has_error is True
        assert "GONE-002" in state.error_message

    @pytest.mark.unit
    def test_unknown_view_is_noop(self, state):
        """Unknown views: no crash, no error."""
        from agent.governance_ui.controllers.routing import _load_entity_for_deep_link

        _load_entity_for_deep_link(state, API_URL, "unknown_view", "X")
        assert state.has_error is False
        assert state.selected_task is None
        assert state.selected_session is None


# =============================================================================
# Test: api_base_url=None backward compatibility
# =============================================================================
class TestBackwardCompatibility:
    """register_routing_controller without api_base_url still works."""

    @pytest.mark.unit
    def test_no_api_url_still_registers_triggers(self, state, ctrl):
        """Without api_base_url, triggers are registered (no entity loading)."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        bridge = register_routing_controller(state, ctrl)  # No api_base_url
        assert "on_route_change" in ctrl.triggers
        assert "push_route" in ctrl.triggers

    @pytest.mark.unit
    @patch("agent.governance_ui.controllers.tasks_navigation._load_task_from_api")
    def test_no_api_url_skips_entity_loading(self, mock_load, state, ctrl):
        """Without api_base_url, same-view nav skips entity load (no crash)."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state.active_view = "tasks"
        register_routing_controller(state, ctrl)  # No api_base_url

        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/BUG-012")

        mock_load.assert_not_called()
