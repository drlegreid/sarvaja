"""
Tests for agent configuration card component.

Per GAP-UI-040: Effective config display.
Batch 165: New coverage for views/agents/config.py (0->8 tests).
"""
import inspect

import pytest


class TestAgentsConfigComponents:
    def test_build_agent_config_card_callable(self):
        from agent.governance_ui.views.agents.config import build_agent_config_card
        assert callable(build_agent_config_card)


class TestAgentsConfigContent:
    def test_has_config_card_testid(self):
        from agent.governance_ui.views.agents import config
        source = inspect.getsource(config)
        assert "agent-config-card" in source

    def test_has_identifier_icon(self):
        from agent.governance_ui.views.agents import config
        source = inspect.getsource(config)
        assert "mdi-identifier" in source

    def test_has_cog_icon(self):
        from agent.governance_ui.views.agents import config
        source = inspect.getsource(config)
        assert "mdi-cog" in source

    def test_has_brain_icon(self):
        from agent.governance_ui.views.agents import config
        source = inspect.getsource(config)
        assert "mdi-brain" in source

    def test_has_instructions_testid(self):
        from agent.governance_ui.views.agents import config
        source = inspect.getsource(config)
        assert "agent-instructions-full" in source

    def test_has_tools_section(self):
        from agent.governance_ui.views.agents import config
        source = inspect.getsource(config)
        assert "mdi-wrench" in source

    def test_has_expansion_panel(self):
        from agent.governance_ui.views.agents import config
        source = inspect.getsource(config)
        assert "VExpansionPanel" in source
