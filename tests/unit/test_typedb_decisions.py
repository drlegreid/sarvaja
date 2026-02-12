"""
Unit tests for TypeDB Decision Queries and CRUD.

Per DOC-SIZE-01-v1: Tests for typedb/queries/rules/decisions.py module.
Tests: get_all_decisions, get_superseded_decisions, create_decision,
       update_decision, delete_decision, link_decision_to_rule.
"""

import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest

from governance.typedb.queries.rules.decisions import DecisionQueries


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


class _ConcreteDecisionClient(DecisionQueries):
    def __init__(self):
        self._execute_query = MagicMock(return_value=[])
        self._execute_write = MagicMock()
        self._driver = MagicMock()
        self.database = "test-db"

    def _setup_tx(self):
        tx = MagicMock()
        tx.query.return_value = MagicMock(resolve=MagicMock())
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=tx)
        ctx.__exit__ = MagicMock(return_value=False)
        self._driver.transaction.return_value = ctx
        return tx


@pytest.fixture()
def client():
    return _ConcreteDecisionClient()


class TestGetAllDecisions:
    def test_returns_decisions(self, client):
        client._execute_query.return_value = [
            {"id": "DECISION-001", "name": "D1", "ctx": "Context",
             "rat": "Rationale", "stat": "APPROVED"},
        ]
        decisions = client.get_all_decisions()
        assert len(decisions) == 1
        assert decisions[0].id == "DECISION-001"
        assert decisions[0].name == "D1"
        assert decisions[0].status == "APPROVED"

    def test_empty(self, client):
        client._execute_query.return_value = []
        assert client.get_all_decisions() == []

    def test_with_date(self, client):
        call_count = [0]
        def _mock(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"id": "D-1", "name": "D1", "ctx": "c", "rat": "r", "stat": "APPROVED"}]
            if "decision-date" in q:
                return [{"date": datetime(2026, 1, 15)}]
            return []
        client._execute_query.side_effect = _mock
        decisions = client.get_all_decisions()
        assert len(decisions) == 1
        assert decisions[0].decision_date == datetime(2026, 1, 15)


class TestGetSupersededDecisions:
    def test_returns_chain(self, client):
        client._execute_query.return_value = [
            {"aid": "DECISION-002", "bid": "DECISION-001"},
        ]
        result = client.get_superseded_decisions()
        assert len(result) == 1
        assert result[0]["superseding"] == "DECISION-002"
        assert result[0]["superseded"] == "DECISION-001"

    def test_empty(self, client):
        client._execute_query.return_value = []
        assert client.get_superseded_decisions() == []


class TestCreateDecision:
    def test_success(self, client):
        client._execute_query.return_value = [
            {"id": "DECISION-010", "name": "New", "ctx": "ctx", "rat": "rat", "stat": "PENDING"}
        ]
        result = client.create_decision("DECISION-010", "New", "ctx", "rat")
        assert result is not None
        assert result.id == "DECISION-010"
        client._execute_write.assert_called_once()

    def test_invalid_status(self, client):
        with pytest.raises(ValueError, match="Invalid status"):
            client.create_decision("D-1", "Name", "ctx", "rat", status="INVALID")

    def test_escapes_quotes(self, client):
        client._execute_query.return_value = []
        client.create_decision("D-1", 'Name "quoted"', 'Context "here"', 'Rationale')
        query = client._execute_write.call_args[0][0]
        assert '\\"quoted\\"' in query

    def test_not_found_after_create(self, client):
        client._execute_query.return_value = []
        result = client.create_decision("D-1", "Name", "ctx", "rat")
        assert result is None


class TestUpdateDecision:
    def test_not_found(self, client):
        client._execute_query.return_value = []
        result = client.update_decision("NONEXISTENT", name="X")
        assert result is None

    def test_no_changes(self, client):
        client._execute_query.return_value = [
            {"id": "D-1", "name": "D1", "ctx": "c", "rat": "r", "stat": "PENDING"}
        ]
        result = client.update_decision("D-1")
        assert result is not None
        assert result.id == "D-1"

    def test_update_name(self, client):
        client._setup_tx()
        client._execute_query.return_value = [
            {"id": "D-1", "name": "Old", "ctx": "c", "rat": "r", "stat": "PENDING"}
        ]
        result = client.update_decision("D-1", name="New Name")
        # Returns the re-fetched decision (same mock data)
        assert result is not None


class TestDeleteDecision:
    def test_success(self, client):
        client._execute_query.return_value = [
            {"id": "D-1", "name": "D1", "ctx": "c", "rat": "r", "stat": "PENDING"}
        ]
        result = client.delete_decision("D-1")
        assert result is True
        client._execute_write.assert_called_once()

    def test_not_found(self, client):
        client._execute_query.return_value = []
        result = client.delete_decision("NONEXISTENT")
        assert result is False
        client._execute_write.assert_not_called()


class TestLinkDecisionToRule:
    def test_success(self, client):
        # First call: READ tx returns results (entities found)
        # Second call: WRITE tx for insert
        call_count = [0]
        def _ctx_mgr(*args, **kwargs):
            call_count[0] += 1
            ctx = MagicMock()
            tx = MagicMock()
            if call_count[0] == 1:
                # READ tx — entities exist
                tx.query.return_value = MagicMock(
                    resolve=MagicMock(return_value=[{"d": "D", "r": "R"}])
                )
            else:
                # WRITE tx
                tx.query.return_value = MagicMock(resolve=MagicMock())
            ctx.__enter__ = MagicMock(return_value=tx)
            ctx.__exit__ = MagicMock(return_value=False)
            return ctx

        client._driver.transaction.side_effect = _ctx_mgr
        result = client.link_decision_to_rule("D-1", "RULE-001")
        assert result is True

    def test_entities_not_found(self, client):
        tx = MagicMock()
        tx.query.return_value = MagicMock(
            resolve=MagicMock(return_value=[])
        )
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=tx)
        ctx.__exit__ = MagicMock(return_value=False)
        client._driver.transaction.return_value = ctx

        result = client.link_decision_to_rule("D-1", "RULE-999")
        assert result is False

    def test_error_returns_false(self, client):
        client._driver.transaction.side_effect = Exception("TypeDB error")
        result = client.link_decision_to_rule("D-1", "RULE-001")
        assert result is False
