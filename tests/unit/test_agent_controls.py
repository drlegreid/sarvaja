"""
Tests for agent stop/control actions.

Per PLAN-UI-OVERHAUL-001 Task 3.2: Agent Stop/Control.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestAgentControlActions:
    """Verify agent detail has control action buttons."""

    def test_agent_detail_has_control_buttons(self):
        """Agent detail should include control action buttons."""
        from agent.governance_ui.views.agents import detail
        source = inspect.getsource(detail)
        assert 'control' in source.lower() or 'action' in source.lower(), (
            "Agent detail should reference control/action components"
        )

    def test_agent_controls_module_exists(self):
        """An agent controls module should exist."""
        from agent.governance_ui.views.agents import controls
        assert hasattr(controls, 'build_agent_controls_card'), (
            "controls module should export build_agent_controls_card"
        )

    def test_agent_controls_has_stop_task(self):
        """Agent controls should have a stop task button."""
        from agent.governance_ui.views.agents import controls
        source = inspect.getsource(controls)
        assert 'stop' in source.lower(), (
            "Agent controls should have stop task functionality"
        )

    def test_agent_controls_has_end_session(self):
        """Agent controls should have an end session button."""
        from agent.governance_ui.views.agents import controls
        source = inspect.getsource(controls)
        assert 'end' in source.lower() and 'session' in source.lower(), (
            "Agent controls should have end session functionality"
        )

    def test_agent_controls_has_pause(self):
        """Agent controls should have a pause toggle."""
        from agent.governance_ui.views.agents import controls
        source = inspect.getsource(controls)
        assert 'pause' in source.lower(), (
            "Agent controls should have pause agent functionality"
        )
