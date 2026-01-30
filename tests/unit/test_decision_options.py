"""
Tests for decision options/pros-cons display.

Per PLAN-UI-OVERHAUL-001 Task 4.2: Decision Log - Operator Steering.
TDD: Tests written to validate implementation.
"""

import pytest
import inspect


class TestDecisionOptions:
    """Verify decision detail shows options with pros/cons."""

    def test_decision_detail_has_options_section(self):
        """Decision detail should display options considered."""
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert 'options' in source.lower() and 'considered' in source.lower(), (
            "Decision detail should have 'Options Considered' section"
        )

    def test_decision_detail_has_pros_cons(self):
        """Decision detail should show pros and cons for each option."""
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert 'pros' in source and 'cons' in source, (
            "Decision detail should show pros and cons"
        )

    def test_decision_detail_marks_chosen_option(self):
        """Decision detail should indicate which option was chosen."""
        from agent.governance_ui.views.decisions import detail
        source = inspect.getsource(detail)
        assert 'chosen' in source, (
            "Decision detail should mark chosen option"
        )


class TestRulesGridColumns:
    """Verify rules grid has task and session count columns."""

    def test_rules_grid_has_tasks_count(self):
        """Rules grid should have Tasks count column."""
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert 'linked_tasks_count' in source, (
            "Rules grid should have linked_tasks_count column"
        )

    def test_rules_grid_has_sessions_count(self):
        """Rules grid should have Sessions count column."""
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view)
        assert 'linked_sessions_count' in source, (
            "Rules grid should have linked_sessions_count column"
        )


class TestTasksGridColumns:
    """Verify tasks grid has all required columns."""

    def test_tasks_grid_has_description_column(self):
        """Tasks grid should have Description column matching API field."""
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert 'description' in source, (
            "Tasks grid should have description column"
        )

    def test_tasks_grid_has_updated_column(self):
        """Tasks grid should have Updated/Last Changed column."""
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert 'completed_at' in source or 'updated' in source.lower(), (
            "Tasks grid should have updated/completed_at column"
        )
