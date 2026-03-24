"""
Unit tests for RouteSyncBridge (TDD — written before implementation).

Per FEAT-008: Named URI routing for dashboard navigation.
Per TEST-E2E-01-v1: Tier 1 unit tests.

RouteSyncBridge is the bidirectional bridge between:
    - Trame state (active_view, selected_task, etc.)
    - URL hash (#/projects/WS-123/tasks/FEAT-008)
"""
import pytest
from unittest.mock import MagicMock, patch


class MockState:
    """Minimal mock of Trame state for testing."""

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
        }
        self._data.update(kwargs)
        self._dirty_keys = []

    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._data.get(name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def dirty(self, key):
        self._dirty_keys.append(key)


class TestRouteSyncBridge:
    """Tests for RouteSyncBridge — state ↔ URL sync."""

    @pytest.mark.unit
    def test_state_to_hash_list_view(self):
        """State with active_view='tasks' produces correct hash."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState(active_view="tasks")
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        result = bridge.state_to_hash(state)
        assert result == "#/projects/WS-9147535A/tasks"

    @pytest.mark.unit
    def test_state_to_hash_detail_view(self):
        """State with selected_task produces detail hash."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState(
            active_view="tasks",
            show_task_detail=True,
            selected_task={"task_id": "FEAT-008"},
        )
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        result = bridge.state_to_hash(state)
        assert result == "#/projects/WS-9147535A/tasks/FEAT-008"

    @pytest.mark.unit
    def test_state_to_hash_session_detail(self):
        """Session detail produces correct hash."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState(
            active_view="sessions",
            show_session_detail=True,
            selected_session={"session_id": "SESSION-2026-03-23"},
        )
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        result = bridge.state_to_hash(state)
        assert result == "#/projects/WS-9147535A/sessions/SESSION-2026-03-23"

    @pytest.mark.unit
    def test_state_to_hash_standalone_view(self):
        """Standalone views produce simple hashes."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState(active_view="executive")
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        result = bridge.state_to_hash(state)
        assert result == "#/executive"

    @pytest.mark.unit
    def test_hash_to_state_list_view(self):
        """Hash for list view updates state correctly."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState()
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        bridge.hash_to_state("#/projects/WS-9147535A/tasks", state)

        assert state.active_view == "tasks"
        assert state.show_task_detail is False

    @pytest.mark.unit
    def test_hash_to_state_detail_view(self):
        """Hash for detail view sets show_*_detail and selected_*."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState()
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        bridge.hash_to_state("#/projects/WS-9147535A/tasks/FEAT-008", state)

        assert state.active_view == "tasks"
        assert state.show_task_detail is True
        # Entity ID is stored for controller to load
        assert state._pending_entity_id == "FEAT-008"

    @pytest.mark.unit
    def test_hash_to_state_session_detail(self):
        """Session detail hash sets session state."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState()
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        bridge.hash_to_state("#/projects/WS-9147535A/sessions/SESSION-2026-03-23", state)

        assert state.active_view == "sessions"
        assert state.show_session_detail is True
        assert state._pending_entity_id == "SESSION-2026-03-23"

    @pytest.mark.unit
    def test_hash_to_state_standalone(self):
        """Standalone view hash sets active_view."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState()
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        bridge.hash_to_state("#/executive", state)
        assert state.active_view == "executive"

    @pytest.mark.unit
    def test_extract_entity_id_task(self):
        """Extract entity ID from task object."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        assert bridge._extract_entity_id("tasks", {"task_id": "FEAT-008"}) == "FEAT-008"

    @pytest.mark.unit
    def test_extract_entity_id_session(self):
        """Extract entity ID from session object."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        result = bridge._extract_entity_id("sessions", {"session_id": "S-123"})
        assert result == "S-123"

    @pytest.mark.unit
    def test_extract_entity_id_rule(self):
        """Extract entity ID from rule — uses 'id' field."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        result = bridge._extract_entity_id("rules", {"id": "TEST-GUARD-01"})
        assert result == "TEST-GUARD-01"

    @pytest.mark.unit
    def test_extract_entity_id_none_entity(self):
        """None entity returns None."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        assert bridge._extract_entity_id("tasks", None) is None

    @pytest.mark.unit
    def test_detail_flag_mapping(self):
        """Each entity view maps to correct show_*_detail flag."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        assert bridge._detail_flag("tasks") == "show_task_detail"
        assert bridge._detail_flag("sessions") == "show_session_detail"
        assert bridge._detail_flag("rules") == "show_rule_detail"
        assert bridge._detail_flag("agents") == "show_agent_detail"
        assert bridge._detail_flag("decisions") == "show_decision_detail"
        assert bridge._detail_flag("workspaces") == "show_workspace_detail"

    @pytest.mark.unit
    def test_detail_flag_standalone_returns_none(self):
        """Standalone views have no detail flag."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        assert bridge._detail_flag("executive") is None
        assert bridge._detail_flag("monitor") is None

    @pytest.mark.unit
    def test_generates_js_hash_update(self):
        """generate_js_push produces correct JS code."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        js = bridge.generate_js_push("#/projects/WS-9147535A/tasks/FEAT-008")
        assert "window.location.hash" in js
        assert "FEAT-008" in js

    @pytest.mark.unit
    def test_generates_js_hashchange_listener(self):
        """generate_js_listener produces hashchange event handler."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        bridge = RouteSyncBridge(default_project_id="WS-9147535A")
        js = bridge.generate_js_listener("on_hash_change")
        assert "hashchange" in js
        assert "on_hash_change" in js

    @pytest.mark.unit
    def test_state_to_hash_rule_detail(self):
        """Rule detail with 'id' field."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState(
            active_view="rules",
            show_rule_detail=True,
            selected_rule={"id": "GOV-RULE-01"},
        )
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        result = bridge.state_to_hash(state)
        assert result == "#/projects/WS-9147535A/rules/GOV-RULE-01"

    @pytest.mark.unit
    def test_state_to_hash_agent_detail(self):
        """Agent detail with 'agent_id' field."""
        from agent.governance_ui.routing.sync import RouteSyncBridge

        state = MockState(
            active_view="agents",
            show_agent_detail=True,
            selected_agent={"agent_id": "code-agent"},
        )
        bridge = RouteSyncBridge(default_project_id="WS-9147535A")

        result = bridge.state_to_hash(state)
        assert result == "#/projects/WS-9147535A/agents/code-agent"
