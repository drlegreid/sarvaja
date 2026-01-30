"""
Tests for window state isolation completeness.

Per PLAN-UI-OVERHAUL-001 Task 0.3: Window State Isolation.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestWindowStateIsolation:
    """Verify window state isolator covers all navigation states."""

    def test_isolator_covers_agent_detail(self):
        """Window isolator should cover agent detail state."""
        from agent.governance_ui.components import window_state
        source = inspect.getsource(window_state)
        assert 'show_agent_detail' in source, (
            "Window isolator should cover show_agent_detail"
        )

    def test_isolator_covers_agent_selection(self):
        """Window isolator should cover agent selection."""
        from agent.governance_ui.components import window_state
        source = inspect.getsource(window_state)
        assert 'selected_agent' in source, (
            "Window isolator should cover selected_agent"
        )

    def test_isolator_covers_session_form(self):
        """Window isolator should cover session form state."""
        from agent.governance_ui.components import window_state
        source = inspect.getsource(window_state)
        assert 'show_session_form' in source, (
            "Window isolator should cover show_session_form"
        )

    def test_isolator_covers_agent_registration(self):
        """Window isolator should cover agent registration state."""
        from agent.governance_ui.components import window_state
        source = inspect.getsource(window_state)
        assert 'show_agent_registration' in source, (
            "Window isolator should cover show_agent_registration"
        )
