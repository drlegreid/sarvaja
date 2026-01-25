"""
RF-004: Robot Framework Library for UI State Management.

Wraps tests/unit/ui/test_ui_state.py for Robot Framework tests.
Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
"""

import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class UIStateLibrary:
    """Robot Framework library for UI State testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def get_initial_state_factory(self) -> Dict[str, Any]:
        """Test get_initial_state returns fresh state each call."""
        from agent.governance_ui import get_initial_state

        state1 = get_initial_state()
        state2 = get_initial_state()

        # Modify one
        state1['active_view'] = 'modified'

        return {
            "different_objects": state1 is not state2,
            "state2_unchanged": state2['active_view'] == 'rules'
        }

    def initial_state_has_required_keys(self) -> Dict[str, Any]:
        """Test initial state has all required keys."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()
        return {
            "has_active_view": 'active_view' in state,
            "has_rules": 'rules' in state,
            "has_decisions": 'decisions' in state,
            "has_sessions": 'sessions' in state,
            "has_selected_rule": 'selected_rule' in state,
            "has_search_query": 'search_query' in state
        }

    def with_loading_transform(self) -> Dict[str, Any]:
        """Test with_loading returns new state with loading flag."""
        from agent.governance_ui import get_initial_state, with_loading

        state = get_initial_state()
        new_state = with_loading(state, True)

        return {
            "different_objects": state is not new_state,
            "new_loading_true": new_state['is_loading'] is True,
            "old_loading_false": state['is_loading'] is False
        }

    def with_error_transform(self) -> Dict[str, Any]:
        """Test with_error returns new state with error set."""
        from agent.governance_ui import get_initial_state, with_error

        state = get_initial_state()
        new_state = with_error(state, "Test error")

        return {
            "has_error": new_state['has_error'] is True,
            "error_message": new_state['error_message']
        }

    def clear_error_transform(self) -> Dict[str, Any]:
        """Test clear_error returns new state with error cleared."""
        from agent.governance_ui import get_initial_state, with_error, clear_error

        state = with_error(get_initial_state(), "Test error")
        new_state = clear_error(state)

        return {
            "has_error": new_state['has_error'],
            "error_message_empty": new_state['error_message'] == ''
        }
