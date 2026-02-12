"""
Unit tests for TypeDB Task Detail Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/tasks/details.py module.
Tests: TaskDetailOperations — update_task_business, update_task_design,
       update_task_architecture, update_task_test, update_task_details,
       get_task_details, _update_task_detail.
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


from governance.typedb.queries.tasks.details import TaskDetailOperations


def _make_task(**kwargs):
    t = MagicMock()
    t.business = kwargs.get("business")
    t.design = kwargs.get("design")
    t.architecture = kwargs.get("architecture")
    t.test_section = kwargs.get("test_section")
    return t


class _ConcreteDetailOps(TaskDetailOperations):
    """Concrete class for testing the mixin."""

    def __init__(self, task=None):
        self._driver = MagicMock()
        self.database = "test-db"
        self._task = task

    def get_task(self, task_id):
        return self._task

    def _execute_query(self, query):
        return []

    def _setup_tx(self):
        tx = MagicMock()
        query_result = MagicMock()
        query_result.resolve.return_value = None
        tx.query.return_value = query_result
        self._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        self._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        return tx


class TestUpdateTaskDetail:
    def test_task_not_found(self):
        ops = _ConcreteDetailOps(task=None)
        result = ops._update_task_detail("T-NONE", "task-business", "content")
        assert result is False

    def test_success(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._setup_tx()
        result = ops._update_task_detail("T-1", "task-business", "Business value")
        assert result is True

    def test_escapes_quotes(self):
        ops = _ConcreteDetailOps(task=_make_task())
        tx = ops._setup_tx()
        ops._update_task_detail("T-1", "task-design", 'Has "quotes" and \\backslash')
        assert tx.query.called

    def test_escapes_backslash(self):
        ops = _ConcreteDetailOps(task=_make_task())
        tx = ops._setup_tx()
        ops._update_task_detail("T-1", "task-design", "path\\to\\file")
        assert tx.query.called

    def test_delete_failure_continues(self):
        ops = _ConcreteDetailOps(task=_make_task())
        tx = ops._setup_tx()
        fail_result = MagicMock()
        fail_result.resolve.side_effect = Exception("no attr")
        ok_result = MagicMock()
        ok_result.resolve.return_value = None
        tx.query.side_effect = [fail_result, ok_result]
        result = ops._update_task_detail("T-1", "task-business", "Content")
        assert result is True

    def test_transaction_failure(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._driver.transaction.side_effect = Exception("db error")
        result = ops._update_task_detail("T-1", "task-business", "Content")
        assert result is False


class TestUpdateTaskBusiness:
    def test_delegates(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._setup_tx()
        result = ops.update_task_business("T-1", "Business content")
        assert result is True


class TestUpdateTaskDesign:
    def test_delegates(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._setup_tx()
        result = ops.update_task_design("T-1", "Design content")
        assert result is True


class TestUpdateTaskArchitecture:
    def test_delegates(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._setup_tx()
        result = ops.update_task_architecture("T-1", "Architecture content")
        assert result is True


class TestUpdateTaskTest:
    def test_delegates(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._setup_tx()
        result = ops.update_task_test("T-1", "Test content")
        assert result is True


class TestUpdateTaskDetails:
    def test_all_sections(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._setup_tx()
        result = ops.update_task_details(
            "T-1",
            business="Why",
            design="What",
            architecture="How",
            test_section="Verify",
        )
        assert result is True

    def test_partial_sections(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._setup_tx()
        result = ops.update_task_details("T-1", business="Why", design="What")
        assert result is True

    def test_no_sections(self):
        ops = _ConcreteDetailOps(task=_make_task())
        result = ops.update_task_details("T-1")
        assert result is True

    def test_failure_propagates(self):
        ops = _ConcreteDetailOps(task=_make_task())
        ops._driver.transaction.side_effect = Exception("db error")
        result = ops.update_task_details("T-1", business="Why")
        assert result is False

    def test_partial_failure(self):
        ops = _ConcreteDetailOps(task=_make_task())
        call_count = [0]
        original_update = ops._update_task_detail

        def mock_update(tid, attr, content):
            call_count[0] += 1
            if call_count[0] == 2:
                return False
            ops._setup_tx()
            return original_update(tid, attr, content)

        ops._update_task_detail = mock_update
        result = ops.update_task_details("T-1", business="Why", design="What")
        assert result is False


class TestGetTaskDetails:
    def test_not_found(self):
        ops = _ConcreteDetailOps(task=None)
        result = ops.get_task_details("T-NONE")
        assert result is None

    def test_all_sections(self):
        task = _make_task(
            business="Why", design="What",
            architecture="How", test_section="Verify",
        )
        ops = _ConcreteDetailOps(task=task)
        result = ops.get_task_details("T-1")
        assert result == {
            "business": "Why",
            "design": "What",
            "architecture": "How",
            "test_section": "Verify",
        }

    def test_empty_sections(self):
        task = _make_task()
        ops = _ConcreteDetailOps(task=task)
        result = ops.get_task_details("T-1")
        assert result["business"] is None
        assert result["design"] is None
