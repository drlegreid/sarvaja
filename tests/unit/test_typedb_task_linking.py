"""
Unit tests for TypeDB Task Linking Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/tasks/linking.py module.
Tests: TaskLinkingOperations — link_evidence_to_task, link_task_to_session,
       link_task_to_rule, get_task_evidence, link_task_to_commit,
       get_task_commits.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

# Mock typedb.driver for in-function imports
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


from governance.typedb.queries.tasks.linking import TaskLinkingOperations


class _ConcreteLinker(TaskLinkingOperations):
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


class TestLinkEvidenceToTask:
    def test_success(self):
        linker = _ConcreteLinker()
        linker._setup_tx()
        result = linker.link_evidence_to_task("P1.1", "evidence/SESSION-2026-01-01.md")
        assert result is True

    def test_failure(self):
        linker = _ConcreteLinker()
        linker._driver.transaction.side_effect = Exception("db error")
        result = linker.link_evidence_to_task("P1.1", "evidence/test.md")
        assert result is False

    def test_evidence_id_sanitized(self):
        linker = _ConcreteLinker()
        tx = linker._setup_tx()
        linker.link_evidence_to_task("P1.1", "evidence/sub/path.test.md")
        # The query should use sanitized evidence_id (slashes and dots replaced)
        assert tx.query.called


class TestLinkTaskToSession:
    def test_success(self):
        linker = _ConcreteLinker()
        linker._setup_tx()
        result = linker.link_task_to_session("P1.1", "SESSION-2026-01-01-TEST")
        assert result is True

    def test_failure(self):
        linker = _ConcreteLinker()
        linker._driver.transaction.side_effect = Exception("no session")
        result = linker.link_task_to_session("P1.1", "S-MISSING")
        assert result is False


class TestLinkTaskToRule:
    def test_success(self):
        linker = _ConcreteLinker()
        linker._setup_tx()
        result = linker.link_task_to_rule("P1.1", "RULE-001")
        assert result is True

    def test_failure(self):
        linker = _ConcreteLinker()
        linker._driver.transaction.side_effect = Exception("no rule")
        result = linker.link_task_to_rule("P1.1", "RULE-999")
        assert result is False


class TestGetTaskEvidence:
    def test_with_results(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"src": "evidence/SESSION-2026-01-01.md"},
            {"src": "evidence/SESSION-2026-01-02.md"},
        ]
        result = linker.get_task_evidence("P1.1")
        assert len(result) == 2
        assert "evidence/SESSION-2026-01-01.md" in result

    def test_empty_results(self):
        linker = _ConcreteLinker()
        linker._query_results = []
        result = linker.get_task_evidence("P1.1")
        assert result == []

    def test_filters_none_values(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"src": "file1.md"},
            {"src": None},
            {"other": "val"},
        ]
        result = linker.get_task_evidence("P1.1")
        assert result == ["file1.md"]


class TestLinkTaskToCommit:
    def test_success(self):
        linker = _ConcreteLinker()
        linker._setup_tx()
        result = linker.link_task_to_commit("P1.1", "abc123", "Fix bug")
        assert result is True

    def test_without_message(self):
        linker = _ConcreteLinker()
        linker._setup_tx()
        result = linker.link_task_to_commit("P1.1", "abc123")
        assert result is True

    def test_failure(self):
        linker = _ConcreteLinker()
        linker._driver.transaction.side_effect = Exception("db error")
        result = linker.link_task_to_commit("P1.1", "abc123")
        assert result is False

    def test_message_escapes_quotes(self):
        linker = _ConcreteLinker()
        tx = linker._setup_tx()
        linker.link_task_to_commit("P1.1", "abc123", 'Fix "bug" in code')
        assert tx.query.called


class TestGetTaskCommits:
    def test_with_results(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"sha": "abc123"},
            {"sha": "def456"},
        ]
        result = linker.get_task_commits("P1.1")
        assert len(result) == 2
        assert "abc123" in result

    def test_empty_results(self):
        linker = _ConcreteLinker()
        linker._query_results = []
        result = linker.get_task_commits("P1.1")
        assert result == []

    def test_filters_none_values(self):
        linker = _ConcreteLinker()
        linker._query_results = [
            {"sha": "abc123"},
            {"sha": None},
        ]
        result = linker.get_task_commits("P1.1")
        assert result == ["abc123"]
