"""
Unit tests for TypeDB Task Linking Operations.

Batch 125: Tests for governance/typedb/queries/tasks/linking.py
- link_evidence_to_task: evidence entity creation + relation
- link_task_to_session: completed-in relation
- link_task_to_rule: implements-rule relation
- get_task_evidence: evidence file query
- link_task_to_commit: git-commit entity + task-commit relation
- get_task_commits: commit SHA query
"""

import sys
from unittest.mock import patch, MagicMock

import pytest


_MOD = "governance.typedb.queries.tasks.linking"


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


def _make_client(query_results=None):
    """Create a mock client with TaskLinkingOperations mixed in."""
    from governance.typedb.queries.tasks.linking import TaskLinkingOperations

    class MockClient(TaskLinkingOperations):
        pass

    client = MockClient()
    client.database = "test-db"
    client._driver = MagicMock()
    client._execute_query = MagicMock(return_value=query_results or [])
    return client


# ── link_evidence_to_task ────────────────────────────────


class TestLinkEvidenceToTask:
    """Tests for link_evidence_to_task() method."""

    def test_successful_link(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.link_evidence_to_task("T-1", "evidence/SESSION-2026-02-11.md")
            assert result is True
            mock_tx.commit.assert_called_once()

    def test_creates_evidence_entity(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            client.link_evidence_to_task("T-1", "evidence/SESSION-2026-02-11.md")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            # First query creates evidence entity
            assert any("evidence-file" in q and "insert" in q.lower() for q in queries)
            # Second query creates relation
            assert any("evidence-supports" in q for q in queries)

    def test_evidence_id_sanitized(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            client.link_evidence_to_task("T-1", "evidence/SESSION.2026.md")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            # evidence_id replaces / and . with -
            insert_q = [q for q in queries if "evidence-id" in q][0]
            assert "evidence-SESSION-2026-md" in insert_q

    def test_existing_evidence_ignored(self):
        """If evidence entity already exists, insert fails silently."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = MagicMock()
            call_count = [0]

            def query_side_effect(q):
                call_count[0] += 1
                result = MagicMock()
                if call_count[0] == 1:
                    # Evidence insert fails (already exists)
                    result.resolve.side_effect = Exception("Already exists")
                else:
                    result.resolve.return_value = None
                return result

            mock_tx.query = query_side_effect
            mock_tx.__enter__ = MagicMock(return_value=mock_tx)
            mock_tx.__exit__ = MagicMock(return_value=False)
            client._driver.transaction.return_value = mock_tx

            result = client.link_evidence_to_task("T-1", "evidence/test.md")
            assert result is True

    def test_link_failure_returns_false(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            client._driver.transaction.side_effect = Exception("TypeDB down")

            result = client.link_evidence_to_task("T-1", "evidence/fail.md")
            assert result is False


# ── link_task_to_session ─────────────────────────────────


class TestLinkTaskToSession:
    """Tests for link_task_to_session() method."""

    def test_successful_link(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.link_task_to_session("T-1", "SESSION-2026-02-11-TEST")
            assert result is True
            mock_tx.commit.assert_called_once()
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("completed-in" in q for q in queries)
            assert any("SESSION-2026-02-11-TEST" in q for q in queries)

    def test_link_failure_returns_false(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            client._driver.transaction.side_effect = Exception("fail")

            result = client.link_task_to_session("T-1", "S-1")
            assert result is False


# ── link_task_to_rule ────────────────────────────────────


class TestLinkTaskToRule:
    """Tests for link_task_to_rule() method."""

    def test_successful_link(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.link_task_to_rule("T-1", "RULE-001")
            assert result is True
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("implements-rule" in q for q in queries)
            assert any("RULE-001" in q for q in queries)

    def test_link_failure_returns_false(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            client._driver.transaction.side_effect = Exception("fail")

            result = client.link_task_to_rule("T-1", "RULE-001")
            assert result is False


# ── get_task_evidence ────────────────────────────────────


class TestGetTaskEvidence:
    """Tests for get_task_evidence() method."""

    def test_returns_evidence_paths(self):
        client = _make_client(query_results=[
            {"src": "evidence/SESSION-001.md"},
            {"src": "evidence/SESSION-002.md"},
        ])
        result = client.get_task_evidence("T-1")
        assert len(result) == 2
        assert "evidence/SESSION-001.md" in result

    def test_filters_none_values(self):
        client = _make_client(query_results=[
            {"src": "evidence/SESSION-001.md"},
            {"src": None},
            {"other_key": "val"},
        ])
        result = client.get_task_evidence("T-1")
        assert len(result) == 1

    def test_empty_results(self):
        client = _make_client(query_results=[])
        result = client.get_task_evidence("T-1")
        assert result == []

    def test_query_contains_task_id(self):
        client = _make_client()
        client.get_task_evidence("MY-TASK-42")
        query_arg = client._execute_query.call_args[0][0]
        assert "MY-TASK-42" in query_arg
        assert "evidence-supports" in query_arg


# ── link_task_to_commit ──────────────────────────────────


class TestLinkTaskToCommit:
    """Tests for link_task_to_commit() method."""

    def test_successful_link(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.link_task_to_commit("T-1", "abc1234", "Fix bug")
            assert result is True
            mock_tx.commit.assert_called_once()
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("git-commit" in q and "insert" in q.lower() for q in queries)
            assert any("task-commit" in q for q in queries)

    def test_commit_message_escaped(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            client.link_task_to_commit("T-1", "abc1234", 'Fix "quoted" bug')
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            commit_q = [q for q in queries if "commit-message" in q][0]
            assert '\\"quoted\\"' in commit_q

    def test_commit_without_message(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.link_task_to_commit("T-1", "def5678")
            assert result is True
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            # First query is the commit entity insert (no match clause)
            entity_insert = queries[0]
            assert "git-commit" in entity_insert
            assert "commit-message" not in entity_insert

    def test_existing_commit_ignored(self):
        """If commit already exists, insert fails silently."""
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            mock_tx = MagicMock()
            call_count = [0]

            def query_side_effect(q):
                call_count[0] += 1
                result = MagicMock()
                if call_count[0] == 1:
                    result.resolve.side_effect = Exception("Already exists")
                else:
                    result.resolve.return_value = None
                return result

            mock_tx.query = query_side_effect
            mock_tx.__enter__ = MagicMock(return_value=mock_tx)
            mock_tx.__exit__ = MagicMock(return_value=False)
            client._driver.transaction.return_value = mock_tx

            result = client.link_task_to_commit("T-1", "abc1234")
            assert result is True

    def test_link_failure_returns_false(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client()
            client._driver.transaction.side_effect = Exception("fail")

            result = client.link_task_to_commit("T-1", "abc1234")
            assert result is False


# ── get_task_commits ─────────────────────────────────────


class TestGetTaskCommits:
    """Tests for get_task_commits() method."""

    def test_returns_commit_shas(self):
        client = _make_client(query_results=[
            {"sha": "abc1234"},
            {"sha": "def5678"},
        ])
        result = client.get_task_commits("T-1")
        assert len(result) == 2
        assert "abc1234" in result

    def test_filters_none_values(self):
        client = _make_client(query_results=[
            {"sha": "abc1234"},
            {"sha": None},
        ])
        result = client.get_task_commits("T-1")
        assert len(result) == 1

    def test_empty_results(self):
        client = _make_client(query_results=[])
        result = client.get_task_commits("T-1")
        assert result == []

    def test_query_contains_task_id(self):
        client = _make_client()
        client.get_task_commits("MY-TASK-99")
        query_arg = client._execute_query.call_args[0][0]
        assert "MY-TASK-99" in query_arg
        assert "task-commit" in query_arg
