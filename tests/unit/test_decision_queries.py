"""
Unit tests for TypeDB Decision Queries and CRUD Operations.

Per DOC-SIZE-01-v1: Tests for governance/typedb/queries/rules/decisions.py module.
Tests: DecisionQueries — get_all_decisions, get_superseded_decisions,
       create_decision, update_decision, delete_decision, link_decision_to_rule.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from governance.typedb.queries.rules.decisions import DecisionQueries


class _TestClient(DecisionQueries):
    """Concrete class for testing the mixin."""

    def __init__(self, query_results=None, write_fn=None):
        self._query_results = query_results or []
        self._query_call_count = 0
        self._multi_results = None
        self._write_fn = write_fn
        self._driver = MagicMock()
        self.database = "test-db"

    def set_multi_results(self, results_list):
        """Set different results for sequential _execute_query calls."""
        self._multi_results = list(results_list)

    def _execute_query(self, query, infer=False):
        if self._multi_results:
            return self._multi_results.pop(0)
        return self._query_results

    def _execute_write(self, query):
        if self._write_fn:
            self._write_fn(query)


# ── get_all_decisions ────────────────────────────────────


class TestGetAllDecisions:
    def test_returns_decisions(self):
        client = _TestClient([
            {"id": "DEC-001", "name": "Use TypeDB", "ctx": "Context", "rat": "Reason", "stat": "APPROVED"},
        ])
        # Second query for decision-date returns empty
        client.set_multi_results([
            [{"id": "DEC-001", "name": "Use TypeDB", "ctx": "Context", "rat": "Reason", "stat": "APPROVED"}],
            [],  # date query
        ])
        result = client.get_all_decisions()
        assert len(result) == 1
        assert result[0].id == "DEC-001"
        assert result[0].name == "Use TypeDB"

    def test_empty_results(self):
        client = _TestClient([])
        result = client.get_all_decisions()
        assert result == []

    def test_decision_with_date(self):
        now = datetime.now()
        client = _TestClient()
        client.set_multi_results([
            [{"id": "DEC-002", "name": "Name", "ctx": "Ctx", "rat": "Rat", "stat": "PENDING"}],
            [{"date": now}],  # date query
        ])
        result = client.get_all_decisions()
        assert len(result) == 1
        assert result[0].decision_date == now

    def test_decision_with_string_date(self):
        client = _TestClient()
        client.set_multi_results([
            [{"id": "DEC-003", "name": "N", "ctx": "C", "rat": "R", "stat": "IMPLEMENTED"}],
            [{"date": "2026-01-15T10:30:00"}],
        ])
        result = client.get_all_decisions()
        assert result[0].decision_date == datetime(2026, 1, 15, 10, 30, 0)


# ── get_superseded_decisions ─────────────────────────────


class TestGetSupersededDecisions:
    def test_returns_chain(self):
        client = _TestClient([
            {"aid": "DEC-002", "bid": "DEC-001"},
        ])
        result = client.get_superseded_decisions()
        assert result == [{"superseding": "DEC-002", "superseded": "DEC-001"}]

    def test_no_supersessions(self):
        client = _TestClient([])
        result = client.get_superseded_decisions()
        assert result == []


# ── create_decision ──────────────────────────────────────


class TestCreateDecision:
    def test_invalid_status_raises(self):
        client = _TestClient()
        with pytest.raises(ValueError, match="Invalid status"):
            client.create_decision("DEC-X", "Name", "Context", "Rationale", status="INVALID")

    def test_valid_statuses(self):
        for status in ["PENDING", "APPROVED", "REJECTED", "IMPLEMENTED"]:
            writes = []
            client = _TestClient(write_fn=lambda q: writes.append(q))
            client.set_multi_results([
                [{"id": "DEC-X", "name": "N", "ctx": "C", "rat": "R", "stat": status}],
                [],
            ])
            result = client.create_decision("DEC-X", "N", "C", "R", status=status)
            assert result is not None
            assert result.id == "DEC-X"

    def test_calls_execute_write(self):
        writes = []
        client = _TestClient(write_fn=lambda q: writes.append(q))
        client.set_multi_results([
            [{"id": "DEC-NEW", "name": "New", "ctx": "C", "rat": "R", "stat": "PENDING"}],
            [],
        ])
        client.create_decision("DEC-NEW", "New", "C", "R")
        assert len(writes) == 1
        assert "DEC-NEW" in writes[0]

    def test_returns_none_when_not_found(self):
        writes = []
        client = _TestClient(write_fn=lambda q: writes.append(q))
        client.set_multi_results([
            [],  # get_all_decisions returns empty after create
        ])
        result = client.create_decision("DEC-MISS", "N", "C", "R")
        assert result is None

    def test_escapes_quotes(self):
        writes = []
        client = _TestClient(write_fn=lambda q: writes.append(q))
        client.set_multi_results([[]])
        client.create_decision("DEC-Q", 'Name "quoted"', "Ctx", "Rat")
        assert '\\"' in writes[0]


# ── update_decision ──────────────────────────────────────


class TestUpdateDecision:
    def test_not_found_returns_none(self):
        client = _TestClient([])
        result = client.update_decision("DEC-MISSING", name="New Name")
        assert result is None

    def test_no_changes_returns_existing(self):
        client = _TestClient()
        client.set_multi_results([
            [{"id": "DEC-001", "name": "N", "ctx": "C", "rat": "R", "stat": "PENDING"}],
            [],
        ])
        result = client.update_decision("DEC-001")
        assert result is not None
        assert result.id == "DEC-001"


# ── delete_decision ──────────────────────────────────────


class TestDeleteDecision:
    def test_not_found_returns_false(self):
        client = _TestClient([])
        result = client.delete_decision("DEC-MISSING")
        assert result is False

    def test_found_returns_true(self):
        writes = []
        client = _TestClient(write_fn=lambda q: writes.append(q))
        client.set_multi_results([
            [{"id": "DEC-DEL", "name": "N", "ctx": "C", "rat": "R", "stat": "PENDING"}],
            [],
        ])
        result = client.delete_decision("DEC-DEL")
        assert result is True
        assert len(writes) == 1


# ── link_decision_to_rule ────────────────────────────────


class TestLinkDecisionToRule:
    def test_success(self):
        client = _TestClient()
        mock_tx_read = MagicMock()
        mock_tx_read.query.return_value.resolve.return_value = [{"d": "x"}]

        mock_tx_write = MagicMock()
        mock_tx_write.query.return_value.resolve.return_value = None

        call_count = [0]

        def make_ctx(db, tx_type):
            ctx = MagicMock()
            if call_count[0] == 0:
                ctx.__enter__ = MagicMock(return_value=mock_tx_read)
            else:
                ctx.__enter__ = MagicMock(return_value=mock_tx_write)
            ctx.__exit__ = MagicMock(return_value=False)
            call_count[0] += 1
            return ctx

        client._driver.transaction.side_effect = make_ctx
        result = client.link_decision_to_rule("DEC-001", "RULE-001")
        assert result is True

    def test_entities_not_found(self):
        client = _TestClient()
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = []
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        result = client.link_decision_to_rule("DEC-X", "RULE-X")
        assert result is False

    def test_exception_returns_false(self):
        client = _TestClient()
        client._driver.transaction.side_effect = Exception("TypeDB error")
        result = client.link_decision_to_rule("DEC-A", "RULE-B")
        assert result is False
