"""
Unit tests for TypeDB Session Mutation Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/sessions/crud_mutations.py module.
Tests: SessionMutationOperations — update_session, delete_session.
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


from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations


class _ConcreteMutator(SessionMutationOperations):
    """Concrete class for testing the mixin."""

    def __init__(self):
        self._driver = MagicMock()
        self.database = "test-db"
        self._session_obj = None
        self._get_call_count = 0

    def get_session(self, session_id):
        self._get_call_count += 1
        return self._session_obj

    def _setup_tx(self):
        tx = MagicMock()
        query_result = MagicMock()
        query_result.resolve.return_value = None
        tx.query.return_value = query_result
        self._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        self._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        return tx


def _make_session(session_id="S-1", description="Test", agent_id="code-agent"):
    s = MagicMock()
    s.session_id = session_id
    s.description = description
    s.agent_id = agent_id
    return s


class TestUpdateSession:
    def test_not_found(self):
        m = _ConcreteMutator()
        m._session_obj = None
        result = m.update_session("NONEXISTENT")
        assert result is None

    def test_no_updates(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        m._setup_tx()
        result = m.update_session("S-1")
        assert result is not None

    def test_update_description(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        m.update_session("S-1", description="New desc")
        # delete old + insert new
        assert tx.query.call_count >= 2

    def test_description_escapes_quotes(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        m.update_session("S-1", description='Has "quotes" here')
        assert tx.query.called

    def test_update_agent_id(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        m.update_session("S-1", agent_id="new-agent")
        assert tx.query.call_count >= 2

    def test_update_start_time(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        m.update_session("S-1", start_time="2026-01-01T10:00:00.000")
        assert tx.query.call_count >= 2

    def test_update_end_time(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        m.update_session("S-1", end_time="2026-01-01T11:00:00.000")
        assert tx.query.call_count >= 2

    def test_completed_status_sets_timestamp(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        m.update_session("S-1", status="COMPLETED")
        # Should set completed-at automatically
        assert tx.query.call_count >= 2

    def test_completed_status_no_timestamp_when_end_time(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        # When end_time is provided, status="COMPLETED" shouldn't add another
        m.update_session("S-1", status="COMPLETED", end_time="2026-01-01T11:00:00")
        # end_time sets completed-at; status=COMPLETED is skipped because end_time set
        queries_called = tx.query.call_count
        assert queries_called >= 2

    def test_multiple_updates(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        m.update_session("S-1", description="New", agent_id="agent",
                         start_time="2026-01-01T10:00:00")
        # Each attribute: delete + insert = 2 queries each, 3 attributes = 6+
        assert tx.query.call_count >= 6

    def test_returns_updated_session(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        m._setup_tx()
        result = m.update_session("S-1", description="Updated")
        assert result is not None
        # get_session called twice: once to check exists, once to return
        assert m._get_call_count == 2

    def test_transaction_failure(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        m._driver.transaction.side_effect = Exception("db error")
        result = m.update_session("S-1", description="New")
        assert result is None

    def test_delete_query_failure_continues(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        tx = m._setup_tx()
        # Make first query fail (the delete), second (insert) succeed
        fail_result = MagicMock()
        fail_result.resolve.side_effect = Exception("no attr")
        ok_result = MagicMock()
        ok_result.resolve.return_value = None
        tx.query.side_effect = [fail_result, ok_result]
        # Should still succeed (deletes are wrapped in try/except)
        result = m.update_session("S-1", description="New")
        assert result is not None


class TestDeleteSession:
    def test_not_found(self):
        m = _ConcreteMutator()
        m._session_obj = None
        result = m.delete_session("NONEXISTENT")
        assert result is False

    def test_success(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        m._setup_tx()
        result = m.delete_session("S-1")
        assert result is True

    def test_deletes_relations_then_entity(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        m._setup_tx()
        m.delete_session("S-1")
        # 4 relation queries + 1 entity delete = 5 transactions
        assert m._driver.transaction.call_count >= 5

    def test_transaction_failure(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        m._driver.transaction.side_effect = Exception("db error")
        result = m.delete_session("S-1")
        assert result is False

    def test_relation_failure_continues(self):
        m = _ConcreteMutator()
        m._session_obj = _make_session()
        # First 4 calls fail (relations), 5th succeeds (entity delete)
        call_count = [0]
        original_tx = MagicMock()
        ok_result = MagicMock()
        ok_result.resolve.return_value = None
        original_tx.query.return_value = ok_result

        def mock_transaction(*args, **kwargs):
            call_count[0] += 1
            ctx = MagicMock()
            if call_count[0] <= 4:
                ctx.__enter__ = MagicMock(side_effect=Exception("no relation"))
            else:
                ctx.__enter__ = MagicMock(return_value=original_tx)
            ctx.__exit__ = MagicMock(return_value=False)
            return ctx

        m._driver.transaction.side_effect = mock_transaction
        result = m.delete_session("S-1")
        assert result is True
