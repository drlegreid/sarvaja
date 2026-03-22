"""
Tests for Phase 4: Task Filters — Hide test tasks, workspace/project filters.

FIX-FILT-001: Hide test tasks toggle
FIX-FILT-002: Workspace filter dropdown
FIX-FILT-003: Project filter dropdown
"""

import pytest
from agent.governance_ui.controllers.tasks import _filter_test_tasks


class TestFilterTestTasks:
    """FIX-FILT-001: _filter_test_tasks removes test tasks."""

    def test_removes_task_type_test(self):
        tasks = [
            {"task_id": "FEAT-001", "task_type": "feature"},
            {"task_id": "BUG-001", "task_type": "bug"},
            {"task_id": "TEST-UNIT-001", "task_type": "test"},
        ]
        result = _filter_test_tasks(tasks)
        assert len(result) == 2
        assert all(t["task_type"] != "test" for t in result)

    def test_removes_crud_prefix(self):
        tasks = [
            {"task_id": "FEAT-001", "task_type": "feature"},
            {"task_id": "CRUD-TASK-001", "task_type": "chore"},
        ]
        result = _filter_test_tasks(tasks)
        assert len(result) == 1
        assert result[0]["task_id"] == "FEAT-001"

    def test_removes_inttest_prefix(self):
        tasks = [
            {"task_id": "FEAT-001", "task_type": "feature"},
            {"task_id": "INTTEST-SESSION-001", "task_type": "chore"},
        ]
        result = _filter_test_tasks(tasks)
        assert len(result) == 1
        assert result[0]["task_id"] == "FEAT-001"

    def test_removes_test_prefix(self):
        tasks = [
            {"task_id": "FEAT-001", "task_type": "feature"},
            {"task_id": "TEST-SUITE-001", "task_type": None},
        ]
        result = _filter_test_tasks(tasks)
        assert len(result) == 1

    def test_keeps_non_test_tasks(self):
        tasks = [
            {"task_id": "FEAT-001", "task_type": "feature"},
            {"task_id": "BUG-001", "task_type": "bug"},
            {"task_id": "EPIC-GOV-RULES-V3", "task_type": "epic"},
        ]
        result = _filter_test_tasks(tasks)
        assert len(result) == 3

    def test_empty_list(self):
        assert _filter_test_tasks([]) == []

    def test_handles_missing_task_id(self):
        tasks = [{"task_type": "test"}, {"task_type": "feature"}]
        result = _filter_test_tasks(tasks)
        assert len(result) == 1

    def test_handles_missing_task_type(self):
        tasks = [{"task_id": "FOO-001"}, {"task_id": "CRUD-001"}]
        result = _filter_test_tasks(tasks)
        assert len(result) == 1
        assert result[0]["task_id"] == "FOO-001"

    def test_both_type_and_prefix(self):
        """Task that has BOTH test type AND test prefix — filtered once."""
        tasks = [
            {"task_id": "TEST-E2E-001", "task_type": "test"},
            {"task_id": "FEAT-001", "task_type": "feature"},
        ]
        result = _filter_test_tasks(tasks)
        assert len(result) == 1
        assert result[0]["task_id"] == "FEAT-001"


class TestInitialState:
    """Verify Phase 4 state variables are in initial state."""

    def test_hide_test_default_true(self):
        from agent.governance_ui.state.initial import get_initial_state
        s = get_initial_state()
        assert s["tasks_hide_test"] is True

    def test_workspace_filter_default_none(self):
        from agent.governance_ui.state.initial import get_initial_state
        s = get_initial_state()
        assert s["tasks_workspace_filter"] is None

    def test_project_filter_default_none(self):
        from agent.governance_ui.state.initial import get_initial_state
        s = get_initial_state()
        assert s["tasks_project_filter"] is None

    def test_workspace_options_default_empty(self):
        from agent.governance_ui.state.initial import get_initial_state
        s = get_initial_state()
        assert s["task_workspace_options"] == []

    def test_project_options_default_empty(self):
        from agent.governance_ui.state.initial import get_initial_state
        s = get_initial_state()
        assert s["task_project_options"] == []
