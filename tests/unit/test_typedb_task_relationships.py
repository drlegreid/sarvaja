"""
Unit tests for TypeDB Task Relationship Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/tasks/relationships.py module.
Tests: TaskRelationshipOperations — link_parent_task, link_blocking_task,
       link_related_tasks, get_task_children, get_task_parent,
       get_tasks_blocking, get_tasks_blocked_by, get_related_tasks.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

_mock_typedb_driver = MagicMock()
_mock_typedb_driver.TransactionType.WRITE = "write"


@pytest.fixture(autouse=True)
def _mock_typedb():
    with patch.dict(sys.modules, {
        "typedb": MagicMock(),
        "typedb.driver": _mock_typedb_driver,
    }):
        yield


from governance.typedb.queries.tasks.relationships import TaskRelationshipOperations


class _ConcreteRelator(TaskRelationshipOperations):
    """Concrete class for testing the mixin."""

    def __init__(self):
        self._driver = MagicMock()
        self.database = "test-db"
        self._query_results = []

    def _execute_query(self, query):
        return self._query_results

    def _setup_tx(self):
        tx = MagicMock()
        query_result = MagicMock()
        query_result.resolve.return_value = None
        tx.query.return_value = query_result
        self._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        self._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        return tx


class TestLinkParentTask:
    def test_success(self):
        r = _ConcreteRelator()
        r._setup_tx()
        result = r.link_parent_task("CHILD-1", "PARENT-1")
        assert result is True

    def test_failure(self):
        r = _ConcreteRelator()
        r._driver.transaction.side_effect = Exception("db error")
        result = r.link_parent_task("CHILD-1", "PARENT-1")
        assert result is False

    def test_query_contains_ids(self):
        r = _ConcreteRelator()
        tx = r._setup_tx()
        r.link_parent_task("CHILD-1", "PARENT-1")
        query_str = tx.query.call_args[0][0]
        assert "CHILD-1" in query_str
        assert "PARENT-1" in query_str


class TestLinkBlockingTask:
    def test_success(self):
        r = _ConcreteRelator()
        r._setup_tx()
        result = r.link_blocking_task("BLOCKER-1", "BLOCKED-1")
        assert result is True

    def test_failure(self):
        r = _ConcreteRelator()
        r._driver.transaction.side_effect = Exception("db error")
        result = r.link_blocking_task("BLOCKER-1", "BLOCKED-1")
        assert result is False


class TestLinkRelatedTasks:
    def test_success(self):
        r = _ConcreteRelator()
        r._setup_tx()
        result = r.link_related_tasks("TASK-A", "TASK-B")
        assert result is True

    def test_failure(self):
        r = _ConcreteRelator()
        r._driver.transaction.side_effect = Exception("db error")
        result = r.link_related_tasks("TASK-A", "TASK-B")
        assert result is False


class TestGetTaskChildren:
    def test_with_children(self):
        r = _ConcreteRelator()
        r._query_results = [{"cid": "CHILD-1"}, {"cid": "CHILD-2"}]
        result = r.get_task_children("PARENT-1")
        assert result == ["CHILD-1", "CHILD-2"]

    def test_empty(self):
        r = _ConcreteRelator()
        r._query_results = []
        result = r.get_task_children("PARENT-1")
        assert result == []

    def test_filters_none(self):
        r = _ConcreteRelator()
        r._query_results = [{"cid": "CHILD-1"}, {"cid": None}, {"other": "val"}]
        result = r.get_task_children("PARENT-1")
        assert result == ["CHILD-1"]


class TestGetTaskParent:
    def test_found(self):
        r = _ConcreteRelator()
        r._query_results = [{"pid": "PARENT-1"}]
        result = r.get_task_parent("CHILD-1")
        assert result == "PARENT-1"

    def test_not_found(self):
        r = _ConcreteRelator()
        r._query_results = []
        result = r.get_task_parent("ORPHAN-1")
        assert result is None


class TestGetTasksBlocking:
    def test_with_blockers(self):
        r = _ConcreteRelator()
        r._query_results = [{"bid": "BLOCKER-1"}, {"bid": "BLOCKER-2"}]
        result = r.get_tasks_blocking("BLOCKED-1")
        assert result == ["BLOCKER-1", "BLOCKER-2"]

    def test_empty(self):
        r = _ConcreteRelator()
        r._query_results = []
        result = r.get_tasks_blocking("TASK-1")
        assert result == []


class TestGetTasksBlockedBy:
    def test_with_results(self):
        r = _ConcreteRelator()
        r._query_results = [{"bid": "BLOCKED-1"}]
        result = r.get_tasks_blocked_by("BLOCKER-1")
        assert result == ["BLOCKED-1"]

    def test_empty(self):
        r = _ConcreteRelator()
        r._query_results = []
        result = r.get_tasks_blocked_by("TASK-1")
        assert result == []


class TestGetRelatedTasks:
    def test_with_results(self):
        r = _ConcreteRelator()
        r._query_results = [{"oid": "TASK-B"}, {"oid": "TASK-C"}]
        result = r.get_related_tasks("TASK-A")
        assert result == ["TASK-B", "TASK-C"]

    def test_empty(self):
        r = _ConcreteRelator()
        r._query_results = []
        result = r.get_related_tasks("TASK-A")
        assert result == []

    def test_filters_none(self):
        r = _ConcreteRelator()
        r._query_results = [{"oid": "TASK-B"}, {"oid": None}]
        result = r.get_related_tasks("TASK-A")
        assert result == ["TASK-B"]
