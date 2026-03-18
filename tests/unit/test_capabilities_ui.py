"""
Tests for agent capabilities card component.

Per RULE-012: Single Responsibility - verifies capabilities.py UI structure.
Tests for agent/governance_ui/views/agents/capabilities.py.
"""
import inspect

import pytest


class TestAgentCapabilitiesComponents:
    """Verify the build function exists and is callable."""

    def test_build_agent_capabilities_card_callable(self):
        from agent.governance_ui.views.agents.capabilities import (
            build_agent_capabilities_card,
        )
        assert callable(build_agent_capabilities_card)

    def test_build_function_takes_no_args(self):
        from agent.governance_ui.views.agents.capabilities import (
            build_agent_capabilities_card,
        )
        sig = inspect.signature(build_agent_capabilities_card)
        assert len(sig.parameters) == 0

    def test_build_function_has_docstring(self):
        from agent.governance_ui.views.agents.capabilities import (
            build_agent_capabilities_card,
        )
        assert build_agent_capabilities_card.__doc__ is not None
        assert "capabilities" in build_agent_capabilities_card.__doc__.lower()


class TestAgentCapabilitiesTestIds:
    """Verify data-testid attributes for E2E selector targeting."""

    def test_has_capabilities_card_testid(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "agent-capabilities-card" in source

    def test_has_capabilities_list_testid(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "capabilities-list" in source

    def test_has_capability_item_testid(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "capability-item" in source


class TestAgentCapabilitiesContent:
    """Verify UI content strings and icons are present."""

    def test_has_governing_rules_title(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "Governing Rules" in source

    def test_has_shield_key_icon(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "mdi-shield-key" in source

    def test_has_gavel_icon(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "mdi-gavel" in source

    def test_has_shield_off_outline_icon(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "mdi-shield-off-outline" in source

    def test_has_bindings_chip_text(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "bindings" in source

    def test_has_empty_state_message(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "No governance rules bound to this agent" in source


class TestAgentCapabilitiesStructure:
    """Verify Vuetify component usage and reactive bindings."""

    def test_uses_vcard(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "VCard(" in source

    def test_uses_vlist(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "VList(" in source

    def test_uses_vlistitem(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "VListItem(" in source

    def test_uses_vchip(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "VChip(" in source

    def test_uses_vprogress_linear(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "VProgressLinear(" in source

    def test_has_loading_state_binding(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "agent_capabilities_loading" in source

    def test_has_agent_capabilities_binding(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "agent_capabilities" in source

    def test_has_v_for_capabilities(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "v_for" in source
        assert "cap in agent_capabilities" in source

    def test_has_status_color_condition(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "cap.status === 'active'" in source

    def test_has_category_fallback(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "cap.category || 'general'" in source

    def test_has_rule_id_key(self):
        from agent.governance_ui.views.agents import capabilities
        source = inspect.getsource(capabilities)
        assert "cap.rule_id" in source

    def test_module_docstring_present(self):
        from agent.governance_ui.views.agents import capabilities
        assert capabilities.__doc__ is not None
        assert "Capabilities" in capabilities.__doc__
