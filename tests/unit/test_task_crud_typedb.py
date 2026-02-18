"""
Unit tests for TypeDB Task CRUD Operations.

Batch 125: Tests for governance/typedb/queries/tasks/crud.py
- _update_attribute(): DRY helper for TypeDB 3.x attribute updates
- TaskCRUDOperations.insert_task: full insertion with optional fields
- TaskCRUDOperations.update_task_status: delegates to status.py
- TaskCRUDOperations.update_task: general attribute update
- TaskCRUDOperations.delete_task: relation cleanup + entity delete
"""

import sys
from unittest.mock import patch, MagicMock, call

import pytest


_MOD = "governance.typedb.queries.tasks.crud"


def _make_typedb_mocks():
    """Create mock typedb.driver with TransactionType."""
    mock_typedb = MagicMock()
    mock_typedb.TransactionType = MagicMock()
    mock_typedb.TransactionType.WRITE = "WRITE"
    return mock_typedb


def _make_tx():
    """Create a mock transaction context manager."""
    mock_tx = MagicMock()
    mock_tx.query.return_value.resolve.return_value = None
    mock_tx.__enter__ = MagicMock(return_value=mock_tx)
    mock_tx.__exit__ = MagicMock(return_value=False)
    return mock_tx


def _make_client(task_exists=True, task_data=None):
    """Create a mock client with TaskCRUDOperations mixed in."""
    from governance.typedb.queries.tasks.crud import TaskCRUDOperations

    class MockClient(TaskCRUDOperations):
        pass

    client = MockClient()
    client.database = "test-db"
    client._driver = MagicMock()
    client._execute_query = MagicMock(return_value=[])

    if task_data:
        client.get_task = MagicMock(return_value=task_data)
    elif task_exists:
        task = MagicMock()
        task.id = "T-1"
        task.name = "Test Task"
        task.status = "OPEN"
        task.phase = "P1"
        task.item_type = None
        task.document_path = None
        client.get_task = MagicMock(return_value=task)
    else:
        client.get_task = MagicMock(return_value=None)

    return client


# ── _update_attribute ────────────────────────────────────


class TestUpdateAttribute:
    """Tests for _update_attribute helper function."""

    def test_with_old_value_deletes_then_inserts(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.queries.tasks.crud import _update_attribute
            mock_tx = MagicMock()
            mock_tx.query.return_value.resolve.return_value = None

            _update_attribute(mock_tx, "T-1", "task-status", "OPEN", "CLOSED")
            assert mock_tx.query.call_count == 2
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("delete" in q.lower() for q in queries)
            assert any("insert" in q.lower() for q in queries)

    def test_without_old_value_inserts_only(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.queries.tasks.crud import _update_attribute
            mock_tx = MagicMock()
            mock_tx.query.return_value.resolve.return_value = None

            _update_attribute(mock_tx, "T-1", "item-type", None, "gap")
            assert mock_tx.query.call_count == 1
            q = mock_tx.query.call_args_list[0].args[0]
            assert "insert" in q.lower()

    def test_escapes_quotes(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.queries.tasks.crud import _update_attribute
            mock_tx = MagicMock()
            mock_tx.query.return_value.resolve.return_value = None

            _update_attribute(mock_tx, "T-1", "task-name", 'old "name"', 'new "name"')
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            insert_q = [q for q in queries if "insert" in q.lower()][0]
            assert '\\"name\\"' in insert_q


# ── insert_task ──────────────────────────────────────────


class TestInsertTask:
    """Tests for insert_task() method."""

    def test_basic_insert(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.insert_task("T-1", "Test Task", "OPEN", "P1")
            assert result is not None
            mock_tx.commit.assert_called_once()
            # get_task called to return the created task
            client.get_task.assert_called_with("T-1")

    def test_insert_with_all_optional_fields(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.insert_task(
                "T-2", "Full Task", "IN_PROGRESS", "P2",
                body="Detailed body",
                gap_id="GAP-001",
                resolution="IMPLEMENTED",
                item_type="gap",
                document_path="docs/README.md",
                agent_id="code-agent",
            )
            assert result is not None
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            insert_q = queries[0]
            assert "task-body" in insert_q
            assert "gap-reference" in insert_q
            assert "task-resolution" in insert_q
            assert "item-type" in insert_q
            assert "document-path" in insert_q
            assert "agent-id" in insert_q

    def test_insert_with_linked_rules(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            client.insert_task(
                "T-3", "Rule Task", "OPEN", "P1",
                linked_rules=["RULE-001", "RULE-002"],
            )
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            rule_queries = [q for q in queries if "implements-rule" in q]
            assert len(rule_queries) == 2

    def test_insert_with_linked_sessions(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            client.insert_task(
                "T-4", "Session Task", "OPEN", "P1",
                linked_sessions=["SESSION-2026-02-11-TEST"],
            )
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            session_queries = [q for q in queries if "completed-in" in q]
            assert len(session_queries) == 1

    def test_insert_escapes_name(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            client.insert_task("T-5", 'Task with "quotes"', "OPEN", "P1")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any('\\"quotes\\"' in q for q in queries)

    def test_insert_exception_returns_none(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            client._driver.transaction.side_effect = Exception("TypeDB down")

            result = client.insert_task("T-6", "Fail", "OPEN", "P1")
            assert result is None

    def test_insert_includes_timestamp(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            client.insert_task("T-7", "Timestamped", "OPEN", "P1")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("task-created-at" in q for q in queries)


# ── update_task_status ───────────────────────────────────


class TestUpdateTaskStatus:
    """Tests for update_task_status() delegation."""

    @patch(f"{_MOD}._update_task_status")
    def test_delegates_to_status_module(self, mock_delegate):
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        class MockClient(TaskCRUDOperations):
            pass

        client = MockClient()
        mock_delegate.return_value = MagicMock()

        client.update_task_status("T-1", "IN_PROGRESS", agent_id="a1", evidence="done")
        mock_delegate.assert_called_once_with(
            client, "T-1", "IN_PROGRESS", "a1", "done", None
        )

    @patch(f"{_MOD}._update_task_status")
    def test_passes_resolution(self, mock_delegate):
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations

        class MockClient(TaskCRUDOperations):
            pass

        client = MockClient()
        client.update_task_status("T-1", "CLOSED", resolution="VALIDATED")
        mock_delegate.assert_called_once_with(
            client, "T-1", "CLOSED", None, None, "VALIDATED"
        )


# ── update_task ──────────────────────────────────────────


class TestUpdateTask:
    """Tests for update_task() method."""

    def test_task_not_found(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(task_exists=False)
            result = client.update_task("MISSING", status="CLOSED")
            assert result is False

    def test_update_status(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.update_task("T-1", status="IN_PROGRESS")
            assert result is True
            mock_tx.commit.assert_called_once()
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("task-status" in q for q in queries)

    def test_same_status_skipped(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            # Current status is OPEN, passing OPEN should skip
            result = client.update_task("T-1", status="OPEN")
            assert result is True
            # Only commit, no attribute queries
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert not any("task-status" in q for q in queries)

    def test_update_name(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.update_task("T-1", name="New Name")
            assert result is True
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("task-name" in q and "New Name" in q for q in queries)

    def test_update_item_type(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.update_task("T-1", item_type="rd")
            assert result is True
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("item-type" in q for q in queries)

    def test_update_document_path(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.update_task("T-1", document_path="docs/new.md")
            assert result is True
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("document-path" in q for q in queries)

    def test_exception_returns_false(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            client._driver.transaction.side_effect = Exception("fail")

            result = client.update_task("T-1", status="CLOSED")
            assert result is False


# ── delete_task ──────────────────────────────────────────


class TestDeleteTask:
    """Tests for delete_task() method."""

    def test_successful_delete(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.delete_task("T-1")
            assert result is True
            # 3 commits: 2 relationship cleanup transactions + 1 entity delete
            assert mock_tx.commit.call_count == 3

    def test_cleans_up_relations(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            client.delete_task("T-1")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("implements-rule" in q for q in queries)
            assert any("completed-in" in q for q in queries)

    def test_relation_errors_ignored(self):
        """Relation delete failures should not prevent entity delete."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = MagicMock()
            call_count = [0]

            def query_side_effect(q):
                call_count[0] += 1
                result = MagicMock()
                if call_count[0] <= 2:
                    result.resolve.side_effect = Exception("No relation")
                else:
                    result.resolve.return_value = None
                return result

            mock_tx.query = query_side_effect
            mock_tx.__enter__ = MagicMock(return_value=mock_tx)
            mock_tx.__exit__ = MagicMock(return_value=False)
            client._driver.transaction.return_value = mock_tx

            result = client.delete_task("T-1")
            assert result is True

    def test_entity_delete_failure(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = MagicMock()
            mock_tx.query.side_effect = Exception("Delete failed")
            mock_tx.__enter__ = MagicMock(return_value=mock_tx)
            mock_tx.__exit__ = MagicMock(return_value=False)
            client._driver.transaction.return_value = mock_tx

            result = client.delete_task("T-1")
            assert result is False
