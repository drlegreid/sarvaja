"""
RF-004: Robot Framework Library for UI Navigation Context.

Wraps agent.governance_ui.state and view functions for Robot Framework tests.
Per UI-NAV-01-v1: Entity Navigation Context.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class UINavContextLibrary:
    """Robot Framework library for UI Navigation Context testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._state = None
        self._triggers = []

    def get_initial_state(self) -> Dict[str, Any]:
        """Get the initial UI state."""
        from agent.governance_ui.state.initial import get_initial_state
        return get_initial_state()

    def state_contains_key(self, key: str) -> bool:
        """Check if initial state contains a key."""
        state = self.get_initial_state()
        return key in state

    def state_key_value_is_none(self, key: str) -> bool:
        """Check if state key value is None."""
        state = self.get_initial_state()
        return state.get(key) is None

    def get_registered_triggers(self) -> List[str]:
        """Register task controllers and return list of triggers."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        registered_triggers = []

        class MockState:
            def __setattr__(self, name, value):
                pass

            def __getattr__(self, name):
                if name == "tasks":
                    return []
                return None

        class MockCtrl:
            def set(self, name):
                def decorator(func):
                    return func
                return decorator

            def trigger(self, name):
                def decorator(func):
                    registered_triggers.append(name)
                    return func
                return decorator

        register_tasks_controllers(MockState(), MockCtrl(), "http://localhost:8082")
        return registered_triggers

    def trigger_is_registered(self, trigger_name: str) -> bool:
        """Check if a trigger is registered."""
        triggers = self.get_registered_triggers()
        return trigger_name in triggers

    def get_view_source(self, module_path: str) -> str:
        """Get source code of a view module.

        Args:
            module_path: Dot-separated module path (e.g., 'agent.governance_ui.views.sessions.tasks')

        Returns:
            Source code as string
        """
        import importlib
        import inspect

        module = importlib.import_module(module_path)
        return inspect.getsource(module)

    def view_source_contains(self, module_path: str, search_text: str) -> bool:
        """Check if view source contains a string.

        Args:
            module_path: Dot-separated module path
            search_text: Text to search for

        Returns:
            True if text found in source
        """
        source = self.get_view_source(module_path)
        return search_text in source

    def tasks_view_has_sessions_source(self) -> bool:
        """Check if tasks view passes 'sessions' as source_view."""
        return self.view_source_contains(
            "agent.governance_ui.views.sessions.tasks",
            "'sessions'"
        )

    def tasks_view_has_session_id_source(self) -> bool:
        """Check if tasks view passes selected_session.session_id as source_id."""
        return self.view_source_contains(
            "agent.governance_ui.views.sessions.tasks",
            "selected_session.session_id"
        )

    def task_detail_has_back_to_source_button(self) -> bool:
        """Check if task detail has back-to-source testid."""
        return self.view_source_contains(
            "agent.governance_ui.views.tasks.detail",
            "task-detail-back-to-source"
        )

    def task_detail_has_back_to_source_trigger(self) -> bool:
        """Check if task detail triggers navigate_back_to_source."""
        return self.view_source_contains(
            "agent.governance_ui.views.tasks.detail",
            "navigate_back_to_source"
        )

    def task_detail_has_nav_source_conditionals(self) -> bool:
        """Check if task detail has both nav_source_view conditionals."""
        source = self.get_view_source("agent.governance_ui.views.tasks.detail")
        has_if = 'v_if="nav_source_view"' in source
        has_else = 'v_if="!nav_source_view"' in source
        return has_if and has_else

    def rules_view_has_rules_source(self) -> bool:
        """Check if rules view passes 'rules' as source_view."""
        return self.view_source_contains(
            "agent.governance_ui.views.rules_view",
            "'rules'"
        )

    def rules_view_has_rule_id_source(self) -> bool:
        """Check if rules view passes selected_rule.rule_id as source_id."""
        return self.view_source_contains(
            "agent.governance_ui.views.rules_view",
            "selected_rule.rule_id"
        )
