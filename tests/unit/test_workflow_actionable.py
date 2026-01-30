"""
Tests for workflow compliance actionable features.

Per PLAN-UI-OVERHAUL-001 Task 4.4: Workflow Compliance Actionable.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestWorkflowActionable:
    """Verify workflow compliance has action buttons."""

    def test_violations_have_create_task_action(self):
        """Violations should have a 'Create Task' action button."""
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert 'create' in source.lower() and 'task' in source.lower(), (
            "Workflow violations should have Create Task action"
        )

    def test_recommendations_have_action_buttons(self):
        """Recommendations should have action buttons."""
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert 'click' in source.lower(), (
            "Workflow view should have clickable action elements"
        )
