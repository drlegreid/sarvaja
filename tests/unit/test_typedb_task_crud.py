"""
Unit tests for TypeDB Task CRUD Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/tasks/crud.py module.
Tests: _update_attribute, insert_task, update_task, delete_task.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from governance.typedb.queries.tasks.crud import _update_attribute, TaskCRUDOperations


# Mock typedb.driver in sys.modules for in-function imports
_mock_typedb_driver = MagicMock()
_mock_typedb_driver.TransactionType.WRITE = "write"
_mock_typedb_driver.TransactionType.READ = "read"


@pytest.fixture(autouse=True)
def _mock_typedb():
    with patch.dict(sys.modules, {
        "typedb": MagicMock(),
        "typedb.driver": _mock_typedb_driver,
    }):
        yield


class TestUpdateAttribute:
    def test_insert_only_when_no_old_value(self):
        tx = MagicMock()
        tx.query.return_value = MagicMock(resolve=MagicMock())
        _update_attribute(tx, "T-1", "task-status", None, "DONE")
        assert tx.query.call_count == 1
        assert 'insert' in tx.query.call_args[0][0].lower()

    def test_delete_and_insert_with_old_value(self):
        tx = MagicMock()
        tx.query.return_value = MagicMock(resolve=MagicMock())
        _update_attribute(tx, "T-1", "task-status", "OPEN", "DONE")
        assert tx.query.call_count == 2

    def test_escapes_quotes(self):
        tx = MagicMock()
        tx.query.return_value = MagicMock(resolve=MagicMock())
        _update_attribute(tx, "T-1", "task-name", None, 'Fix "bug"')
        query = tx.query.call_args[0][0]
        assert '\\"bug\\"' in query


class _ConcreteTaskCRUD(TaskCRUDOperations):
    def __init__(self):
        self._driver = MagicMock()
        self._execute_query = MagicMock(return_value=[])
        self.database = "test-db"
        self._mock_tasks = {}

    def get_task(self, task_id):
        return self._mock_tasks.get(task_id)


@pytest.fixture()
def crud():
    c = _ConcreteTaskCRUD()
    tx = MagicMock()
    tx.query.return_value = MagicMock(resolve=MagicMock())
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=tx)
    ctx.__exit__ = MagicMock(return_value=False)
    c._driver.transaction.return_value = ctx
    c._tx = tx
    return c


class TestInsertTask:
    def test_basic_insert(self, crud):
        from governance.typedb.entities import Task
        crud._mock_tasks["T-1"] = Task(id="T-1", name="Test", status="OPEN", phase="P1")
        result = crud.insert_task("T-1", "Test", "OPEN", "P1")
        assert result is not None
        assert result.id == "T-1"

    def test_insert_with_optional_fields(self, crud):
        from governance.typedb.entities import Task
        crud._mock_tasks["T-2"] = Task(id="T-2", name="Full", status="OPEN", phase="P2")
        result = crud.insert_task(
            "T-2", "Full", "OPEN", "P2",
            body="Detailed body",
            gap_id="GAP-001",
            resolution="NONE",
            item_type="task",
            agent_id="code-agent",
        )
        assert result is not None

    def test_insert_with_linked_rules(self, crud):
        from governance.typedb.entities import Task
        crud._mock_tasks["T-3"] = Task(id="T-3", name="Linked", status="OPEN", phase="P1")
        result = crud.insert_task(
            "T-3", "Linked", "OPEN", "P1",
            linked_rules=["RULE-001", "RULE-002"],
        )
        assert result is not None
        # 1 insert + 2 rule relations = 3 queries
        assert crud._tx.query.call_count >= 3

    def test_insert_failure_returns_none(self, crud):
        crud._driver.transaction.side_effect = Exception("TypeDB error")
        result = crud.insert_task("T-ERR", "Error", "OPEN", "P1")
        assert result is None


class TestUpdateTask:
    def test_update_status(self, crud):
        from governance.typedb.entities import Task
        crud._mock_tasks["T-1"] = Task(id="T-1", name="Test", status="OPEN", phase="P1")
        result = crud.update_task("T-1", status="IN_PROGRESS")
        assert result is True

    def test_update_not_found(self, crud):
        result = crud.update_task("NONEXISTENT", status="DONE")
        assert result is False

    def test_update_no_changes(self, crud):
        from governance.typedb.entities import Task
        crud._mock_tasks["T-1"] = Task(id="T-1", name="Test", status="OPEN", phase="P1")
        # Update with same status — no _update_attribute call
        result = crud.update_task("T-1", status="OPEN")
        assert result is True

    def test_update_failure_returns_false(self, crud):
        from governance.typedb.entities import Task
        crud._mock_tasks["T-1"] = Task(id="T-1", name="Test", status="OPEN", phase="P1")
        crud._driver.transaction.side_effect = Exception("TypeDB error")
        result = crud.update_task("T-1", status="DONE")
        assert result is False


class TestDeleteTask:
    def test_delete_success(self, crud):
        result = crud.delete_task("T-1")
        assert result is True

    def test_delete_failure(self, crud):
        crud._driver.transaction.side_effect = Exception("TypeDB error")
        result = crud.delete_task("T-ERR")
        assert result is False
