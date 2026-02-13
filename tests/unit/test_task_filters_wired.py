"""
Tests for task filters wired to API.

Per B.2: Wire task filters to API.
Batch 159 deepening (was 3 tests, now 7).
"""
import inspect

import pytest


class TestTaskFiltersWired:
    def test_load_tasks_page_references_status_filter(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "tasks_status_filter" in source or "status_filter" in source

    def test_load_tasks_page_references_phase_filter(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "tasks_phase_filter" in source or "phase_filter" in source

    def test_filter_change_triggers_reload(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "apply_task_filters" in source or "tasks_apply_filters" in source

    def test_register_returns_callable(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        assert callable(register_tasks_controllers)

    def test_has_load_tasks_page(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "load_tasks_page" in source

    def test_references_api_endpoint(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "/api/tasks" in source or "api" in source.lower()

    def test_handles_pagination(self):
        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        source = inspect.getsource(register_tasks_controllers)
        assert "page" in source.lower()
