"""
Tests for agent relations card component.

Per GAP-UI-041: Agent-to-session/task relation links.
Batch 165: New coverage for views/agents/relations.py (0->8 tests).
"""
import inspect

import pytest


class TestAgentsRelationsComponents:
    def test_build_agent_relations_card_callable(self):
        from agent.governance_ui.views.agents.relations import build_agent_relations_card
        assert callable(build_agent_relations_card)


class TestAgentsRelationsContent:
    def test_has_relations_card_testid(self):
        from agent.governance_ui.views.agents import relations
        source = inspect.getsource(relations)
        assert "agent-relations-card" in source

    def test_has_recent_sessions(self):
        from agent.governance_ui.views.agents import relations
        source = inspect.getsource(relations)
        assert "Recent Sessions" in source

    def test_has_active_tasks(self):
        from agent.governance_ui.views.agents import relations
        source = inspect.getsource(relations)
        assert "Active Tasks" in source

    def test_has_calendar_clock_icon(self):
        from agent.governance_ui.views.agents import relations
        source = inspect.getsource(relations)
        assert "mdi-calendar-clock" in source

    def test_has_checkbox_icon(self):
        from agent.governance_ui.views.agents import relations
        source = inspect.getsource(relations)
        assert "mdi-checkbox-marked-circle-outline" in source

    def test_has_empty_sessions_fallback(self):
        from agent.governance_ui.views.agents import relations
        source = inspect.getsource(relations)
        assert "No sessions found" in source

    def test_has_empty_tasks_fallback(self):
        from agent.governance_ui.views.agents import relations
        source = inspect.getsource(relations)
        assert "No active tasks" in source
