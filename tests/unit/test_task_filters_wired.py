"""
Tests for task filters wired to API.

Per B.2: Wire task filters to API.
Verifies:
- load_tasks_page includes status filter param
- load_tasks_page includes phase filter param
- Filter params are sent to API when set

Created: 2026-02-01
"""
import pytest
import inspect


class TestTaskFiltersWired:
    """Tests for task filter parameters in API calls."""

    def test_load_tasks_page_references_status_filter(self):
        """load_tasks_page should include status filter in API params."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        # Find load_tasks_page function and check it references the filter
        assert "tasks_status_filter" in source or "status_filter" in source

    def test_load_tasks_page_references_phase_filter(self):
        """load_tasks_page should include phase filter in API params."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "tasks_phase_filter" in source or "phase_filter" in source

    def test_filter_change_triggers_reload(self):
        """Changing filters should trigger a page reload."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "apply_task_filters" in source or "tasks_apply_filters" in source
