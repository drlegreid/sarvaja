"""
Unit tests for TypeDB Session Linking Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/sessions/linking.py module.
Tests: SessionLinkingOperations — link_evidence_to_session,
       get_session_evidence, link_rule_to_session, link_decision_to_session,
       get_session_rules, get_session_decisions.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

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


from governance.typedb.queries.sessions.linking import SessionLinkingOperations


class _ConcreteLinker(SessionLinkingOperations):
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


class TestLinkEvidenceToSession:
    def test_success(self):
        linker = _ConcreteLinker()
        linker._setup_tx()
        result = linker.link_evidence_to_session("SESSION-2026-01-01-001",
                                                  "evidence/test.md")
        assert result is True

    def test_failure(self):
        linker = _ConcreteLinker()
        linker._driver.transaction.side_effect = Exception("db error")
        result = linker.link_evidence_to_session("S-1", "evidence/test.md")
        assert result is False

    def test_evidence_id_sanitized(self):
        linker = _ConcreteLinker()
        tx = linker._setup_tx()
        linker.link_evidence_to_session("S-1", "evidence/sub/path.test.md")
        assert tx.query.called


class TestGetSessionEvidence:
    def test_with_results(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"src": "evidence/file1.md"},
            {"src": "evidence/file2.md"},
        ]
        result = linker.get_session_evidence("S-1")
        assert len(result) == 2
        assert "evidence/file1.md" in result

    def test_empty_results(self):
        linker = _ConcreteLinker()
        linker._query_results = []
        result = linker.get_session_evidence("S-1")
        assert result == []

    def test_filters_none_values(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"src": "file.md"},
            {"src": None},
            {"other": "val"},
        ]
        result = linker.get_session_evidence("S-1")
        assert result == ["file.md"]


class TestLinkRuleToSession:
    def test_success(self):
        linker = _ConcreteLinker()
        linker._setup_tx()
        result = linker.link_rule_to_session("S-1", "RULE-001")
        assert result is True

    def test_failure(self):
        linker = _ConcreteLinker()
        linker._driver.transaction.side_effect = Exception("no rule")
        result = linker.link_rule_to_session("S-1", "RULE-999")
        assert result is False


class TestLinkDecisionToSession:
    def test_success(self):
        linker = _ConcreteLinker()
        linker._setup_tx()
        result = linker.link_decision_to_session("S-1", "DECISION-001")
        assert result is True

    def test_failure(self):
        linker = _ConcreteLinker()
        linker._driver.transaction.side_effect = Exception("no decision")
        result = linker.link_decision_to_session("S-1", "DECISION-999")
        assert result is False


class TestGetSessionRules:
    def test_with_results(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"rid": "RULE-001"},
            {"rid": "RULE-002"},
        ]
        result = linker.get_session_rules("S-1")
        assert len(result) == 2
        assert "RULE-001" in result

    def test_empty(self):
        linker = _ConcreteLinker()
        linker._query_results = []
        result = linker.get_session_rules("S-1")
        assert result == []


class TestGetSessionDecisions:
    def test_with_results(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"did": "DECISION-001"},
        ]
        result = linker.get_session_decisions("S-1")
        assert result == ["DECISION-001"]

    def test_filters_none(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"did": "D-1"},
            {"did": None},
        ]
        result = linker.get_session_decisions("S-1")
        assert result == ["D-1"]
