"""
Unit tests for Routing Controller.

Per FEAT-008: Named URI routing for dashboard navigation.
Per TEST-E2E-01-v1: Tier 1 unit tests.
"""
import pytest
from unittest.mock import MagicMock


class MockState:
    """Minimal mock of Trame state."""

    def __init__(self, **kwargs):
        self._data = {"active_view": "rules"}
        self._data.update(kwargs)

    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._data.get(name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._data[name] = value


class MockCtrl:
    """Minimal mock of Trame controller."""

    def __init__(self):
        self.triggers = {}
        self.js_calls = []

    def trigger(self, name):
        def decorator(func):
            self.triggers[name] = func
            return func
        return decorator

    def call_js(self, code):
        self.js_calls.append(code)


class TestRegisterRoutingController:
    """Tests for register_routing_controller."""

    @pytest.mark.unit
    def test_registers_on_route_change_trigger(self):
        """Should register 'on_route_change' trigger."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState()
        ctrl = MockCtrl()
        register_routing_controller(state, ctrl)

        assert "on_route_change" in ctrl.triggers

    @pytest.mark.unit
    def test_registers_push_route_trigger(self):
        """Should register 'push_route' trigger."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState()
        ctrl = MockCtrl()
        register_routing_controller(state, ctrl)

        assert "push_route" in ctrl.triggers

    @pytest.mark.unit
    def test_returns_bridge_instance(self):
        """Should return a RouteSyncBridge instance."""
        from agent.governance_ui.controllers.routing import register_routing_controller
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState()
        ctrl = MockCtrl()
        bridge = register_routing_controller(state, ctrl)

        assert isinstance(bridge, RouteSyncBridge)

    @pytest.mark.unit
    def test_on_route_change_updates_state(self):
        """on_route_change should update state from hash."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState()
        ctrl = MockCtrl()
        register_routing_controller(state, ctrl)

        # Simulate browser back to sessions list
        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/sessions")
        assert state.active_view == "sessions"

    @pytest.mark.unit
    def test_on_route_change_detail_sets_flag(self):
        """on_route_change with entity_id sets detail flag."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState()
        ctrl = MockCtrl()
        register_routing_controller(state, ctrl)

        ctrl.triggers["on_route_change"]("#/projects/WS-9147535A/tasks/FEAT-008")
        assert state.active_view == "tasks"
        assert state.show_task_detail is True

    @pytest.mark.unit
    def test_push_route_sets_route_hash_state(self):
        """push_route should set route_hash state variable."""
        from agent.governance_ui.controllers.routing import register_routing_controller

        state = MockState(active_view="tasks")
        ctrl = MockCtrl()
        register_routing_controller(state, ctrl)

        ctrl.triggers["push_route"]()
        assert "tasks" in state.route_hash


class TestRoutingControllerSourceCode:
    """Source code structural tests for routing controller."""

    @pytest.mark.unit
    def test_imports_routing_sync(self):
        """Controller should import from routing.sync."""
        import inspect
        from agent.governance_ui.controllers import routing
        source = inspect.getsource(routing)
        assert "RouteSyncBridge" in source

    @pytest.mark.unit
    def test_uses_default_workspace_id(self):
        """Controller should use DEFAULT_WORKSPACE_ID from constants."""
        import inspect
        from agent.governance_ui.controllers import routing
        source = inspect.getsource(routing)
        assert "DEFAULT_WORKSPACE_ID" in source
