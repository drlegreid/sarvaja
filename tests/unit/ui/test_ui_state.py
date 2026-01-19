"""
UI State Management Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Tests for state management pure functions.
"""
import pytest


class TestStateFunctions:
    """Tests for state management pure functions."""

    @pytest.mark.unit
    def test_get_initial_state_factory(self):
        """get_initial_state should return fresh state each call."""
        from agent.governance_ui import get_initial_state

        state1 = get_initial_state()
        state2 = get_initial_state()

        # Should be different objects
        assert state1 is not state2

        # Modify one, other unchanged
        state1['active_view'] = 'modified'
        assert state2['active_view'] == 'rules'

    @pytest.mark.unit
    def test_initial_state_has_required_keys(self):
        """Initial state should have all required keys."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()

        assert 'active_view' in state
        assert 'rules' in state
        assert 'decisions' in state
        assert 'sessions' in state
        assert 'selected_rule' in state
        assert 'search_query' in state

    @pytest.mark.unit
    def test_with_loading_transform(self):
        """with_loading should return new state with loading flag."""
        from agent.governance_ui import get_initial_state, with_loading

        state = get_initial_state()
        new_state = with_loading(state, True)

        assert state is not new_state
        assert new_state['is_loading'] is True
        assert state['is_loading'] is False

    @pytest.mark.unit
    def test_with_error_transform(self):
        """with_error should return new state with error set."""
        from agent.governance_ui import get_initial_state, with_error

        state = get_initial_state()
        new_state = with_error(state, "Test error")

        assert new_state['has_error'] is True
        assert new_state['error_message'] == "Test error"

    @pytest.mark.unit
    def test_clear_error_transform(self):
        """clear_error should return new state with error cleared."""
        from agent.governance_ui import get_initial_state, with_error, clear_error

        state = with_error(get_initial_state(), "Test error")
        new_state = clear_error(state)

        assert new_state['has_error'] is False
        assert new_state['error_message'] == ''
