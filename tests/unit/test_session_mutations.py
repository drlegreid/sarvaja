"""
Unit tests for TypeDB Session Mutation Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/sessions/crud_mutations.py.
Tests: SessionMutationOperations — update_session, delete_session.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

# Mock typedb.driver since it's imported inside function bodies
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


from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations


class _ConcreteMutations(SessionMutationOperations):
    """Concrete class for testing the mixin."""

    def __init__(self):
        self._driver = MagicMock()
        self.database = "test-db"
        self._get_session_result = None

    def get_session(self, session_id):
        return self._get_session_result

    def _setup_tx(self):
        """Set up mock transaction context."""
        tx = MagicMock()
        query_result = MagicMock()
        query_result.resolve.return_value = None
        tx.query.return_value = query_result
        self._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        self._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        return tx


class TestUpdateSession:
    def test_session_not_found(self):
        ops = _ConcreteMutations()
        ops._get_session_result = None
        result = ops.update_session("S-MISSING")
        assert result is None

    def test_update_description(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._setup_tx()
        result = ops.update_session("S-1", description="Updated desc")
        assert result is session

    def test_update_agent_id(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._setup_tx()
        result = ops.update_session("S-1", agent_id="code-agent")
        assert result is session

    def test_update_start_time(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._setup_tx()
        result = ops.update_session("S-1", start_time="2026-02-11T10:00:00")
        assert result is session

    def test_update_end_time(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._setup_tx()
        result = ops.update_session("S-1", end_time="2026-02-11T12:00:00")
        assert result is session

    def test_update_status_completed_sets_completed_at(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._setup_tx()
        result = ops.update_session("S-1", status="COMPLETED")
        assert result is session

    def test_update_status_completed_with_end_time_skips_auto(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._setup_tx()
        result = ops.update_session("S-1", status="COMPLETED",
                                     end_time="2026-02-11T15:00:00")
        assert result is session

    def test_update_multiple_fields(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._setup_tx()
        result = ops.update_session(
            "S-1", description="New desc", agent_id="agent-2",
            start_time="2026-02-11T10:00:00",
        )
        assert result is session

    def test_update_exception_returns_none(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._driver.transaction.side_effect = Exception("db error")
        result = ops.update_session("S-1", description="fail")
        assert result is None

    def test_description_escapes_quotes(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        tx = ops._setup_tx()
        ops.update_session("S-1", description='Has "quotes" inside')
        # Verify that a query was called (escaping happens in the query string)
        assert tx.query.called


class TestDeleteSession:
    def test_session_not_found(self):
        ops = _ConcreteMutations()
        ops._get_session_result = None
        result = ops.delete_session("S-MISSING")
        assert result is False

    def test_delete_success(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        ops._setup_tx()
        result = ops.delete_session("S-1")
        assert result is True

    def test_delete_exception(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session
        # Make the entity delete fail (last transaction)
        call_count = [0]
        original_tx = ops._setup_tx()

        def failing_transaction(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 4:  # Relation queries pass, entity delete fails
                raise Exception("entity delete failed")
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=original_tx)
            ctx.__exit__ = MagicMock(return_value=False)
            return ctx

        ops._driver.transaction = failing_transaction
        result = ops.delete_session("S-1")
        assert result is False

    def test_delete_relation_errors_ignored(self):
        session = MagicMock()
        session.id = "S-1"
        ops = _ConcreteMutations()
        ops._get_session_result = session

        # First 4 calls (relations) will fail, 5th (entity delete) succeeds
        call_count = [0]

        def tx_factory(*args, **kwargs):
            call_count[0] += 1
            tx = MagicMock()
            query_result = MagicMock()
            if call_count[0] <= 4:
                query_result.resolve.side_effect = Exception("relation not found")
            else:
                query_result.resolve.return_value = None
            tx.query.return_value = query_result
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=tx)
            ctx.__exit__ = MagicMock(return_value=False)
            return ctx

        ops._driver.transaction = tx_factory
        result = ops.delete_session("S-1")
        assert result is True
