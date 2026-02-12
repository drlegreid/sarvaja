"""
Unit tests for TypeDB Task Status Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/tasks/status.py module.
Tests: update_task_status — status change, agent_id, evidence,
       resolution, auto-reset, claimed_at, completed_at.
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


from governance.typedb.queries.tasks.status import update_task_status


def _make_task(task_id="T-1", status="OPEN", agent_id=None,
               evidence=None, resolution=None, claimed_at=None,
               completed_at=None):
    t = MagicMock()
    t.task_id = task_id
    t.status = status
    t.agent_id = agent_id
    t.evidence = evidence
    t.resolution = resolution
    t.claimed_at = claimed_at
    t.completed_at = completed_at
    return t


def _make_client(current_task=None, updated_task=None):
    client = MagicMock()
    client.database = "test-db"
    client.get_task.side_effect = [current_task, updated_task or current_task]
    tx = MagicMock()
    query_result = MagicMock()
    query_result.resolve.return_value = None
    tx.query.return_value = query_result
    client._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
    client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
    return client, tx


class TestUpdateTaskStatus:
    def test_task_not_found(self):
        client = MagicMock()
        client.get_task.return_value = None
        result = update_task_status(client, "NONEXISTENT", "DONE")
        assert result is None

    def test_basic_status_change(self):
        task = _make_task(status="OPEN")
        updated = _make_task(status="IN_PROGRESS")
        client, tx = _make_client(task, updated)
        result = update_task_status(client, "T-1", "IN_PROGRESS")
        assert result is not None
        # Verify delete+insert queries for status
        assert tx.query.call_count >= 2

    def test_with_agent_id(self):
        task = _make_task(status="OPEN", agent_id=None)
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "IN_PROGRESS", agent_id="code-agent")
        # Should have status queries + agent_id insert
        assert tx.query.call_count >= 3

    def test_replace_existing_agent(self):
        task = _make_task(status="OPEN", agent_id="old-agent")
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "IN_PROGRESS", agent_id="new-agent")
        # Should delete old agent then insert new
        assert tx.query.call_count >= 4

    def test_with_evidence(self):
        task = _make_task(status="IN_PROGRESS", evidence=None)
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "DONE", evidence="Test passed")
        assert tx.query.call_count >= 3

    def test_replace_existing_evidence(self):
        task = _make_task(status="IN_PROGRESS", evidence="old evidence")
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "DONE", evidence="new evidence")
        # Delete old evidence + insert new
        assert tx.query.call_count >= 4

    def test_evidence_escapes_quotes(self):
        task = _make_task(status="IN_PROGRESS", evidence=None)
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "DONE", evidence='Fix "bug" here')
        assert tx.query.called

    def test_with_resolution(self):
        task = _make_task(status="IN_PROGRESS", resolution=None)
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "DONE", resolution="IMPLEMENTED")
        assert tx.query.call_count >= 3

    def test_replace_existing_resolution(self):
        task = _make_task(status="IN_PROGRESS", resolution="DEFERRED")
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "DONE", resolution="IMPLEMENTED")
        # Delete old resolution + insert new
        assert tx.query.call_count >= 4

    def test_auto_reset_resolution_on_reopen(self):
        task = _make_task(status="DONE", resolution="IMPLEMENTED")
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "OPEN")
        # Should reset resolution to NONE
        assert tx.query.call_count >= 4  # status change + resolution reset

    def test_no_reset_when_already_none(self):
        task = _make_task(status="DONE", resolution="NONE")
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "OPEN")
        # Should NOT reset since already NONE
        assert tx.query.call_count == 2  # status delete + insert only

    def test_claimed_at_set_on_in_progress(self):
        task = _make_task(status="OPEN", claimed_at=None)
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "IN_PROGRESS")
        # Should set claimed_at
        assert tx.query.call_count >= 3

    def test_claimed_at_not_overwritten(self):
        task = _make_task(status="OPEN", claimed_at="2026-01-01")
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "IN_PROGRESS")
        # Should NOT set claimed_at again
        assert tx.query.call_count == 2  # Only status change

    def test_completed_at_set_on_done(self):
        task = _make_task(status="IN_PROGRESS", completed_at=None)
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "DONE")
        assert tx.query.call_count >= 3

    def test_completed_at_set_on_closed(self):
        task = _make_task(status="IN_PROGRESS", completed_at=None)
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "CLOSED")
        assert tx.query.call_count >= 3

    def test_completed_at_not_overwritten(self):
        task = _make_task(status="IN_PROGRESS", completed_at="2026-01-01")
        client, tx = _make_client(task)
        update_task_status(client, "T-1", "DONE")
        assert tx.query.call_count == 2  # Only status change

    def test_transaction_failure(self):
        task = _make_task(status="OPEN")
        client = MagicMock()
        client.get_task.return_value = task
        client._driver.transaction.side_effect = Exception("db error")
        result = update_task_status(client, "T-1", "DONE")
        assert result is None
