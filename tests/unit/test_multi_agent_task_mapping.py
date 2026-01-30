"""
Tests for multi-agent task mapping display.

Per PLAN-UI-OVERHAUL-001 Task 3.4: Multi-Agent Task Mapping.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestMultiAgentTaskMapping:
    """Verify tasks show multiple agents involved in execution."""

    def test_task_forms_show_agent_pipeline(self):
        """Task linked items should show agent pipeline."""
        from agent.governance_ui.views.tasks import forms
        source = inspect.getsource(forms)
        assert 'agent_pipeline' in source or 'involved_agents' in source or (
            'agents' in source.lower() and 'pipeline' in source.lower()
        ), "Task forms should show agent pipeline"

    def test_task_forms_show_multiple_agents(self):
        """Task linked items should display multiple agents."""
        from agent.governance_ui.views.tasks import forms
        source = inspect.getsource(forms)
        assert 'mdi-robot' in source, (
            "Task forms should show robot icons for agents"
        )

    def test_task_detail_has_agent_section(self):
        """Task detail should have an agent involvement section."""
        from agent.governance_ui.views.tasks import forms
        source = inspect.getsource(forms)
        assert 'Agent' in source, (
            "Task forms should have agent section"
        )
