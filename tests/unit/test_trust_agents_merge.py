"""
Tests for merging trust dashboard into agents tab.

Per PLAN-UI-OVERHAUL-001 Task 5.4: Merge Trust+Agents.
Batch 159 deepening (was 2 tests, now 7).
"""
import inspect

import pytest


class TestTrustAgentsMerge:
    def test_agents_list_has_governance_stats(self):
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'trust' in source.lower() and 'avg' in source.lower()

    def test_agents_list_shows_proposals_count(self):
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'proposal' in source.lower()

    def test_has_agents_list_testid(self):
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'agents-list' in source

    def test_has_register_button(self):
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'agents-register-btn' in source

    def test_has_refresh_button(self):
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'mdi-refresh' in source

    def test_build_agents_callable(self):
        from agent.governance_ui.views.agents.list import build_agents_list_view
        assert callable(build_agents_list_view)

    def test_shows_robot_icon(self):
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'mdi-robot' in source
