"""
Tests for agent registration and configuration.

Per PLAN-UI-OVERHAUL-001 Task 3.3: Agent Configuration & New Types.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestAgentRegistration:
    """Verify agent registration form exists and has required fields."""

    def test_register_agent_button_in_list(self):
        """Agents list should have a Register Agent button."""
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'register' in source.lower(), (
            "Agents list should have a Register Agent button"
        )

    def test_agent_registration_form_exists(self):
        """An agent registration form module should exist."""
        from agent.governance_ui.views.agents import registration
        assert hasattr(registration, 'build_agent_registration_form'), (
            "registration module should export build_agent_registration_form"
        )

    def test_registration_form_has_name_field(self):
        """Registration form should have a name field."""
        from agent.governance_ui.views.agents import registration
        source = inspect.getsource(registration)
        assert 'name' in source.lower(), (
            "Registration form should have agent name field"
        )

    def test_registration_form_has_type_field(self):
        """Registration form should have an agent type field."""
        from agent.governance_ui.views.agents import registration
        source = inspect.getsource(registration)
        assert 'agent_type' in source or 'type' in source.lower(), (
            "Registration form should have agent type field"
        )

    def test_registration_form_has_rules_bundle(self):
        """Registration form should support rules bundle selection."""
        from agent.governance_ui.views.agents import registration
        source = inspect.getsource(registration)
        assert 'rule' in source.lower(), (
            "Registration form should support rules bundle"
        )
