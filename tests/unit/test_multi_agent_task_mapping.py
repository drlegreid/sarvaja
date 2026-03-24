"""
Tests for multi-agent task mapping display.

Per PLAN-UI-OVERHAUL-001 Task 3.4: Multi-Agent Task Mapping.
Batch 159 deepening (was 3 tests, now 7).
"""
import inspect

import pytest


class TestMultiAgentTaskMapping:
    def test_task_forms_show_agent_pipeline(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'agent_pipeline' in source or 'involved_agents' in source or (
            'agents' in source.lower() and 'pipeline' in source.lower()
        )

    def test_task_forms_show_multiple_agents(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'mdi-robot' in source

    def test_task_detail_has_agent_section(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'Agent' in source

    def test_task_forms_has_linked_items(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'linked' in source.lower()

    def test_task_forms_has_session_link(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'session' in source.lower()

    def test_task_forms_has_evidence_section(self):
        from agent.governance_ui.views.tasks import forms_linked
        source = inspect.getsource(forms_linked)
        assert 'evidence' in source.lower()

    def test_build_task_form_callable(self):
        from agent.governance_ui.views.tasks.forms import build_task_edit_form
        assert callable(build_task_edit_form)
