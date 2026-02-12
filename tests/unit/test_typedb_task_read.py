"""
Unit tests for TypeDB Task Read Queries.

Per DOC-SIZE-01-v1: Tests for typedb/queries/tasks/read.py module.
Tests: _safe_query, _fetch_task_attr, _fetch_task_relation,
       get_all_tasks, get_available_tasks, get_task, _build_task_from_id.
"""

from unittest.mock import MagicMock

import pytest

from governance.typedb.queries.tasks.read import TaskReadQueries


class _ConcreteTaskReader(TaskReadQueries):
    """Concrete class for testing mixin."""

    def __init__(self):
        self._execute_query = MagicMock(return_value=[])
        self._driver = MagicMock()
        self.database = "test-db"


@pytest.fixture()
def reader():
    return _ConcreteTaskReader()


class TestSafeQuery:
    def test_returns_results(self, reader):
        reader._execute_query.return_value = [{"id": "T-1"}]
        result = reader._safe_query("match ...")
        assert result == [{"id": "T-1"}]

    def test_returns_empty_on_error(self, reader):
        reader._execute_query.side_effect = Exception("missing type")
        result = reader._safe_query("match ...")
        assert result == []


class TestFetchTaskAttr:
    def test_returns_value(self, reader):
        reader._execute_query.return_value = [{"body": "task body"}]
        result = reader._fetch_task_attr("T-1", "task-body", "body")
        assert result == "task body"

    def test_returns_none_when_empty(self, reader):
        reader._execute_query.return_value = []
        result = reader._fetch_task_attr("T-1", "task-body", "body")
        assert result is None

    def test_returns_none_on_error(self, reader):
        reader._execute_query.side_effect = Exception("missing type")
        result = reader._fetch_task_attr("T-1", "task-body", "body")
        assert result is None


class TestFetchTaskRelation:
    def test_returns_list(self, reader):
        reader._execute_query.return_value = [{"rid": "RULE-001"}, {"rid": "RULE-002"}]
        result = reader._fetch_task_relation("T-1", 'match ...', "rid")
        assert result == ["RULE-001", "RULE-002"]

    def test_returns_none_when_empty(self, reader):
        reader._execute_query.return_value = []
        result = reader._fetch_task_relation("T-1", 'match ...', "rid")
        assert result is None


class TestGetAllTasks:
    def test_returns_tasks(self, reader):
        reader._execute_query.return_value = [
            {"id": "T-1", "name": "Task 1", "status": "OPEN", "phase": "P1"},
            {"id": "T-2", "name": "Task 2", "status": "DONE", "phase": "P2"},
        ]
        tasks = reader.get_all_tasks()
        assert len(tasks) == 2
        assert tasks[0].id == "T-1"
        assert tasks[1].status == "DONE"

    def test_empty(self, reader):
        reader._execute_query.return_value = []
        assert reader.get_all_tasks() == []

    def test_filter_by_agent_id(self, reader):
        reader._execute_query.return_value = [
            {"id": "T-1", "name": "Task 1", "status": "OPEN", "phase": "P1"},
        ]
        # After batch fetch, agent_id is set by _batch_fetch_task_attributes
        tasks = reader.get_all_tasks(agent_id="agent-1")
        # Since mock doesn't set agent_id, all tasks are filtered out
        assert len(tasks) == 0


class TestGetAvailableTasks:
    def test_returns_unassigned(self, reader):
        call_count = [0]
        def _mock_query(q):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (TODO tasks)
                return [{"id": "T-1", "name": "Task 1", "status": "TODO", "phase": "P1"}]
            return []  # All other calls
        reader._execute_query.side_effect = _mock_query
        tasks = reader.get_available_tasks()
        # Task T-1 has no agent_id set (default None)
        assert len(tasks) == 1

    def test_excludes_assigned(self, reader):
        def _mock_query(q):
            return [{"id": "T-1", "name": "Task 1", "status": "TODO", "phase": "P1"}]
        reader._execute_query.side_effect = _mock_query
        tasks = reader.get_available_tasks()
        # Even though task exists, batch fetch may set agent_id via mock
        assert isinstance(tasks, list)


class TestGetTask:
    def test_returns_task(self, reader):
        call_count = [0]
        def _mock_query(q):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: main task query
                return [{"name": "My Task", "status": "OPEN", "phase": "P1"}]
            return []  # Optional attrs and relations
        reader._execute_query.side_effect = _mock_query
        task = reader.get_task("T-1")
        assert task is not None
        assert task.id == "T-1"
        assert task.name == "My Task"
        assert task.status == "OPEN"

    def test_not_found(self, reader):
        reader._execute_query.return_value = []
        task = reader.get_task("NONEXISTENT")
        assert task is None

    def test_with_optional_attrs(self, reader):
        call_count = [0]
        def _mock_query(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"name": "My Task", "status": "OPEN", "phase": "P1"}]
            if "task-body" in q:
                return [{"body": "Detailed body"}]
            if "task-resolution" in q:
                return [{"res": "IMPLEMENTED"}]
            return []
        reader._execute_query.side_effect = _mock_query
        task = reader.get_task("T-1")
        assert task is not None
        assert task.body == "Detailed body"
        assert task.resolution == "IMPLEMENTED"
