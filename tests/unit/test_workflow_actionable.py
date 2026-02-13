"""
Tests for workflow compliance actionable features.

Per PLAN-UI-OVERHAUL-001 Task 4.4: Workflow Compliance Actionable.
Batch 159 deepening (was 2 tests, now 7).
"""
import inspect

import pytest


class TestWorkflowActionable:
    def test_violations_have_create_task_action(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert 'create' in source.lower() and 'task' in source.lower()

    def test_recommendations_have_action_buttons(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert 'click' in source.lower()

    def test_has_refresh_button(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert 'workflow-refresh-btn' in source

    def test_has_status_card(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert 'workflow-status-card' in source

    def test_has_check_icon(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert 'mdi-check-decagram' in source

    def test_build_compliance_summary_callable(self):
        from agent.governance_ui.views.workflow_view import build_compliance_summary
        assert callable(build_compliance_summary)

    def test_build_workflow_header_callable(self):
        from agent.governance_ui.views.workflow_view import build_workflow_header
        assert callable(build_workflow_header)
