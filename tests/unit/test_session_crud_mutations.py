"""
Unit tests for TypeDB Session Mutation Operations.

Batch 124: Tests for governance/typedb/queries/sessions/crud_mutations.py
- SessionMutationOperations.update_session: field updates, COMPLETED status
- SessionMutationOperations.delete_session: relations cleanup, entity delete
"""

import sys
from datetime import datetime
from unittest.mock import patch, MagicMock, call

import pytest


_MOD = "governance.typedb.queries.sessions.crud_mutations"


def _make_typedb_mocks():
    """Create mock typedb.driver with TransactionType."""
    mock_typedb = MagicMock()
    mock_typedb.TransactionType = MagicMock()
    mock_typedb.TransactionType.WRITE = "WRITE"
    return mock_typedb


def _make_mixin(session_exists=True, session_data=None):
    """Create a mock object with SessionMutationOperations mixed in."""
    from governance.typedb.queries.sessions.crud_mutations import SessionMutationOperations

    class MockClient(SessionMutationOperations):
        pass

    client = MockClient()
    client.database = "test-db"
    client._driver = MagicMock()

    if session_data:
        client.get_session = MagicMock(return_value=session_data)
    elif session_exists:
        client.get_session = MagicMock(return_value={
            "session_id": "S-1",
            "description": "Test",
            "status": "ACTIVE",
        })
    else:
        client.get_session = MagicMock(return_value=None)

    return client


def _setup_tx(client):
    """Set up a mock transaction context manager on client._driver."""
    mock_tx = MagicMock()
    mock_tx.query.return_value.resolve.return_value = None
    mock_tx.__enter__ = MagicMock(return_value=mock_tx)
    mock_tx.__exit__ = MagicMock(return_value=False)
    client._driver.transaction.return_value = mock_tx
    return mock_tx


# ── update_session ───────────────────────────────────────


class TestUpdateSession:
    """Tests for update_session() method."""

    def test_session_not_found(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin(session_exists=False)
            result = client.update_session("MISSING")
            assert result is None
            client.get_session.assert_called_with("MISSING")

    def test_update_description(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            result = client.update_session("S-1", description="New desc")
            assert result is not None
            # Should have called query at least twice (delete old + insert new)
            assert mock_tx.query.call_count >= 2
            mock_tx.commit.assert_called_once()

    def test_update_agent_id(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            result = client.update_session("S-1", agent_id="research-agent")
            assert result is not None
            mock_tx.commit.assert_called_once()
            # Verify agent_id appears in one of the queries
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("research-agent" in q for q in queries)

    def test_update_start_time(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            result = client.update_session("S-1", start_time="2026-02-11T10:00:00")
            assert result is not None
            mock_tx.commit.assert_called_once()
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("started-at" in q for q in queries)

    def test_update_end_time(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            result = client.update_session("S-1", end_time="2026-02-11T12:00:00")
            assert result is not None
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("completed-at" in q for q in queries)

    def test_completed_status_sets_completed_at(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            result = client.update_session("S-1", status="COMPLETED")
            assert result is not None
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("completed-at" in q for q in queries)

    def test_completed_with_end_time_no_double_set(self):
        """When both status=COMPLETED and end_time are given, end_time takes precedence."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            client.update_session(
                "S-1", status="COMPLETED", end_time="2026-02-11T15:00:00"
            )
            # end_time sets completed-at, status=COMPLETED should NOT also set it
            # (condition: status == "COMPLETED" and end_time is None)
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            completed_at_inserts = [q for q in queries
                                     if "completed-at" in q and "insert" in q.lower()]
            # Should only have ONE insert with completed-at (from end_time)
            assert len(completed_at_inserts) == 1

    def test_description_escapes_quotes(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            client.update_session("S-1", description='Has "quotes" inside')
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            insert_queries = [q for q in queries if "session-description" in q and "insert" in q.lower()]
            assert len(insert_queries) == 1
            assert '\\"quotes\\"' in insert_queries[0]

    def test_update_multiple_fields(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            result = client.update_session(
                "S-1",
                description="Updated",
                agent_id="new-agent",
                start_time="2026-02-11T08:00:00",
            )
            assert result is not None
            mock_tx.commit.assert_called_once()
            # At least 6 queries: delete+insert for each of 3 fields
            assert mock_tx.query.call_count >= 6

    def test_exception_returns_none(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            client._driver.transaction.side_effect = Exception("TypeDB down")

            result = client.update_session("S-1", description="fail")
            assert result is None

    def test_start_time_truncated_to_19_chars(self):
        """start_time[:19] should strip fractional seconds."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = _setup_tx(client)

            client.update_session("S-1", start_time="2026-02-11T10:00:00.123456")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            insert_qs = [q for q in queries if "started-at" in q and "insert" in q.lower()]
            assert len(insert_qs) == 1
            assert ".123456" not in insert_qs[0]
            assert "2026-02-11T10:00:00" in insert_qs[0]


# ── delete_session ───────────────────────────────────────


class TestDeleteSession:
    """Tests for delete_session() method."""

    def test_session_not_found(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin(session_exists=False)
            result = client.delete_session("MISSING")
            assert result is False

    def test_successful_delete(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = MagicMock()
            mock_tx.query.return_value.resolve.return_value = None
            mock_tx.__enter__ = MagicMock(return_value=mock_tx)
            mock_tx.__exit__ = MagicMock(return_value=False)
            client._driver.transaction.return_value = mock_tx

            result = client.delete_session("S-1")
            assert result is True
            # 4 relation deletes + 1 entity delete = 5 transactions
            assert client._driver.transaction.call_count == 5

    def test_relation_delete_errors_ignored(self):
        """Individual relation deletes may fail (relation doesn't exist) — should continue."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()

            call_count = [0]

            def make_tx(*args, **kwargs):
                call_count[0] += 1
                mock_tx = MagicMock()
                mock_tx.__enter__ = MagicMock(return_value=mock_tx)
                mock_tx.__exit__ = MagicMock(return_value=False)
                if call_count[0] <= 4:
                    # First 4 calls (relation deletes) raise
                    mock_tx.query.side_effect = Exception("Relation not found")
                else:
                    # Last call (entity delete) succeeds
                    mock_tx.query.return_value.resolve.return_value = None
                return mock_tx

            client._driver.transaction.side_effect = make_tx

            result = client.delete_session("S-1")
            assert result is True

    def test_entity_delete_failure(self):
        """If the entity delete itself fails, should return False."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()

            call_count = [0]

            def make_tx(*args, **kwargs):
                call_count[0] += 1
                mock_tx = MagicMock()
                mock_tx.__enter__ = MagicMock(return_value=mock_tx)
                mock_tx.__exit__ = MagicMock(return_value=False)
                if call_count[0] <= 4:
                    mock_tx.query.return_value.resolve.return_value = None
                else:
                    mock_tx.query.side_effect = Exception("Delete failed")
                return mock_tx

            client._driver.transaction.side_effect = make_tx

            result = client.delete_session("S-1")
            assert result is False

    def test_deletes_four_relation_types(self):
        """Verify all 4 relation types are cleaned up."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_mixin()
            mock_tx = MagicMock()
            mock_tx.query.return_value.resolve.return_value = None
            mock_tx.__enter__ = MagicMock(return_value=mock_tx)
            mock_tx.__exit__ = MagicMock(return_value=False)
            client._driver.transaction.return_value = mock_tx

            client.delete_session("S-1")

            all_queries = [c.args[0] for c in mock_tx.query.call_args_list]
            relation_names = ["has-evidence", "session-applied-rule",
                              "session-decision", "completed-in"]
            for rel in relation_names:
                assert any(rel in q for q in all_queries), f"Missing cleanup for {rel}"

    def test_returns_updated_session_after_update(self):
        """update_session returns get_session result after successful update."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            updated_data = {"session_id": "S-1", "description": "Updated"}
            client = _make_mixin()
            # First call returns existing, second returns updated
            client.get_session = MagicMock(
                side_effect=[{"session_id": "S-1"}, updated_data]
            )
            mock_tx = _setup_tx(client)

            result = client.update_session("S-1", description="Updated")
            assert result == updated_data
            assert client.get_session.call_count == 2
