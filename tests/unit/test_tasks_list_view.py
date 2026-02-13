"""
Tests for tasks list view component.

Per GAP-FILE-001: Modularization of governance_dashboard.py.
Batch 161: New coverage for views/tasks/list.py (0→8 tests).
"""
import inspect

import pytest


class TestTasksListViewComponents:
    def test_build_tasks_list_view_callable(self):
        from agent.governance_ui.views.tasks.list import build_tasks_list_view
        assert callable(build_tasks_list_view)


class TestTasksListViewContent:
    def test_has_tasks_list_testid(self):
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert "tasks-list" in source

    def test_has_agent_id_input(self):
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert "tasks-agent-id" in source

    def test_has_add_button(self):
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert "tasks-add-btn" in source

    def test_has_robot_icon(self):
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert "mdi-robot" in source

    def test_has_status_filter(self):
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert "status" in source.lower()

    def test_has_refresh_or_load_trigger(self):
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert "trigger" in source

    def test_has_data_table(self):
        from agent.governance_ui.views.tasks import list as tasks_list
        source = inspect.getsource(tasks_list)
        assert "VDataTable" in source or "VList" in source
