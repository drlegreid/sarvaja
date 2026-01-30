"""
Tests for grid/data table views across all tabs.

Per PLAN-UI-OVERHAUL-001 Tasks 1.1-1.3: Grid views with columns.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestRulesGridView:
    """Verify rules view uses VDataTable with proper columns."""

    def test_rules_view_uses_data_table(self):
        """Rules list should use VDataTable, not VList."""
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view.build_rules_list_view)
        assert 'VDataTable' in source or 'v3.VDataTable' in source, (
            "Rules list should use VDataTable for grid layout"
        )

    def test_rules_grid_has_required_columns(self):
        """Rules grid headers should include key columns."""
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view.build_rules_list_view)
        required_keys = ['id', 'name', 'status', 'category', 'priority']
        for key in required_keys:
            assert key in source, f"Rules grid missing column key: {key}"

    def test_rules_view_full_width(self):
        """Rules list should not be constrained to narrow column."""
        from agent.governance_ui.views import rules_view
        source = inspect.getsource(rules_view.build_rules_list_view)
        # Should NOT have cols=8 or similar constraint
        assert 'cols=8' not in source or 'cols=12' in source


class TestSessionsGridView:
    """Verify sessions view uses VDataTable with proper columns."""

    def test_sessions_view_uses_data_table(self):
        """Sessions list should use VDataTable."""
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        assert 'VDataTable' in source or 'v3.VDataTable' in source, (
            "Sessions list should use VDataTable for grid layout"
        )

    def test_sessions_grid_has_required_columns(self):
        """Sessions grid headers should include key columns."""
        from agent.governance_ui.views.sessions import list as sessions_list
        source = inspect.getsource(sessions_list)
        required_keys = ['session_id', 'start_time', 'status']
        for key in required_keys:
            assert key in source, f"Sessions grid missing column key: {key}"


class TestTasksGridView:
    """Verify tasks view has enhanced grid columns."""

    def test_tasks_view_has_status_column(self):
        """Tasks grid should show status column."""
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert 'status' in source

    def test_tasks_view_has_agent_column(self):
        """Tasks grid should show agent column."""
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert 'agent' in source.lower()
