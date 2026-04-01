"""
Unit tests for link idempotency guards.

Per SRVJ-BUG-IDEMP-LINK-01: Duplicate link_task_to_workspace and
link_task_to_commit must be idempotent — second call returns True
without creating a new TypeDB relation.

TDD Phase: RED — these tests MUST fail before implementation.
"""

import pytest
from unittest.mock import MagicMock


# ── Helpers ──────────────────────────────────────────────────────

def _make_workspace_linker():
    """Create a concrete WorkspaceLinkingOperations instance with mocks."""
    from governance.typedb.queries.workspaces.linking import (
        WorkspaceLinkingOperations,
    )

    linker = WorkspaceLinkingOperations.__new__(WorkspaceLinkingOperations)
    linker._driver = MagicMock()
    linker.database = "test-db"
    linker._execute_query = MagicMock(return_value=[])
    return linker


def _make_task_linker():
    """Create a concrete TaskLinkingOperations instance with mocks."""
    from governance.typedb.queries.tasks.linking import TaskLinkingOperations

    linker = TaskLinkingOperations.__new__(TaskLinkingOperations)
    linker._driver = MagicMock()
    linker.database = "test-db"
    linker._execute_query = MagicMock(return_value=[])
    return linker


def _setup_tx(linker):
    """Wire up a mock transaction context manager, return the mock tx."""
    tx = MagicMock()
    tx.query.return_value.resolve.return_value = None
    linker._driver.transaction.return_value.__enter__ = MagicMock(
        return_value=tx
    )
    linker._driver.transaction.return_value.__exit__ = MagicMock(
        return_value=False
    )
    return tx


def _tx_returns_existing_on_check(tx):
    """Make the idempotency-check query return a non-empty result (relation exists),
    while the insert query returns None (not reached).

    The check query is the FIRST tx.query() call; the insert is the SECOND.
    """
    check_result = MagicMock()
    check_result.resolve.return_value = [{"exists": True}]

    insert_result = MagicMock()
    insert_result.resolve.return_value = None

    tx.query.return_value = check_result  # default
    # side_effect controls per-call: first = check (has result), second = insert (not called)
    tx.query.side_effect = [check_result, insert_result]


def _tx_returns_empty_on_check(tx):
    """Make the idempotency-check query return empty (no existing relation),
    so the insert branch should execute.
    """
    check_result = MagicMock()
    check_result.resolve.return_value = []

    insert_result = MagicMock()
    insert_result.resolve.return_value = None

    tx.query.side_effect = [check_result, insert_result]


# ── link_task_to_workspace idempotency ───────────────────────────


class TestLinkTaskToWorkspaceIdempotency:
    """Verify link_task_to_workspace has check-before-insert guard."""

    def test_first_call_creates_relation(self):
        """First call with no existing relation should insert and return True."""
        linker = _make_workspace_linker()
        tx = _setup_tx(linker)
        _tx_returns_empty_on_check(tx)

        result = linker.link_task_to_workspace("WS-001", "TASK-001")

        assert result is True
        # Should have TWO queries: check + insert
        assert tx.query.call_count == 2, (
            f"Expected 2 queries (check + insert), got {tx.query.call_count}"
        )
        # The insert query must contain workspace-has-task
        insert_query = tx.query.call_args_list[1][0][0]
        assert "workspace-has-task" in insert_query
        tx.commit.assert_called_once()

    def test_second_call_skips_insert(self):
        """Second call with existing relation should NOT insert — just return True."""
        linker = _make_workspace_linker()
        tx = _setup_tx(linker)
        _tx_returns_existing_on_check(tx)

        result = linker.link_task_to_workspace("WS-001", "TASK-001")

        assert result is True
        # Should have only ONE query (the check) — insert skipped
        assert tx.query.call_count == 1, (
            f"Expected 1 query (check only), got {tx.query.call_count}. "
            "Idempotency guard missing — insert should be skipped when "
            "relation already exists."
        )
        tx.commit.assert_called_once()

    def test_duplicate_link_returns_true_not_false(self):
        """Duplicate link must return True (success), not False (failure)."""
        linker = _make_workspace_linker()
        tx = _setup_tx(linker)
        _tx_returns_existing_on_check(tx)

        result = linker.link_task_to_workspace("WS-001", "TASK-001")
        assert result is True, "Duplicate link should return True (already exists)"


# ── link_task_to_commit idempotency ──────────────────────────────


class TestLinkTaskToCommitIdempotency:
    """Verify link_task_to_commit has check-before-insert guard."""

    def test_first_call_creates_relation(self):
        """First call with no existing relation should insert and return True."""
        linker = _make_task_linker()
        tx = _setup_tx(linker)

        # For commit: entity insert may or may not fail (commit exists),
        # then check query, then insert query.
        entity_result = MagicMock()
        entity_result.resolve.return_value = None  # entity insert OK

        check_result = MagicMock()
        check_result.resolve.return_value = []  # no existing relation

        insert_result = MagicMock()
        insert_result.resolve.return_value = None  # insert OK

        tx.query.side_effect = [entity_result, check_result, insert_result]

        result = linker.link_task_to_commit("TASK-001", "abc1234", "Fix bug")

        assert result is True
        # Should have 3 queries: entity insert + check + relation insert
        assert tx.query.call_count == 3, (
            f"Expected 3 queries (entity + check + insert), got {tx.query.call_count}"
        )
        # The relation insert query must contain task-commit
        insert_query = tx.query.call_args_list[2][0][0]
        assert "task-commit" in insert_query
        tx.commit.assert_called_once()

    def test_second_call_skips_insert(self):
        """Second call with existing relation should NOT insert — just return True."""
        linker = _make_task_linker()
        tx = _setup_tx(linker)

        # Entity insert fails (already exists) — caught internally
        entity_result = MagicMock()
        entity_result.resolve.side_effect = Exception("already exists")

        # Check query returns existing relation
        check_result = MagicMock()
        check_result.resolve.return_value = [{"exists": True}]

        tx.query.side_effect = [entity_result, check_result]

        result = linker.link_task_to_commit("TASK-001", "abc1234", "Fix bug")

        assert result is True
        # Should have only 2 queries: entity insert (fails) + check (exists)
        # The relation insert should be SKIPPED
        assert tx.query.call_count == 2, (
            f"Expected 2 queries (entity + check), got {tx.query.call_count}. "
            "Idempotency guard missing — insert should be skipped when "
            "relation already exists."
        )
        tx.commit.assert_called_once()

    def test_duplicate_link_returns_true_not_false(self):
        """Duplicate link must return True (success), not False (failure)."""
        linker = _make_task_linker()
        tx = _setup_tx(linker)

        entity_result = MagicMock()
        entity_result.resolve.side_effect = Exception("already exists")

        check_result = MagicMock()
        check_result.resolve.return_value = [{"exists": True}]

        tx.query.side_effect = [entity_result, check_result]

        result = linker.link_task_to_commit("TASK-001", "abc1234")
        assert result is True, "Duplicate link should return True (already exists)"


# ── Shared helper tests ──────────────────────────────────────────


class TestRelationExistsHelper:
    """Verify the shared _relation_exists helper is used by all link methods."""

    def test_helper_importable(self):
        """The _relation_exists helper should be importable from the linking module."""
        from governance.typedb.queries.tasks.linking import _relation_exists
        assert callable(_relation_exists)

    def test_helper_returns_true_when_results_exist(self):
        """_relation_exists returns True when query yields results."""
        from governance.typedb.queries.tasks.linking import _relation_exists

        tx = MagicMock()
        result = MagicMock()
        result.resolve.return_value = [{"x": 1}]
        tx.query.return_value = result

        assert _relation_exists(tx, "match $x; select $x;") is True

    def test_helper_returns_false_when_no_results(self):
        """_relation_exists returns False when query yields empty."""
        from governance.typedb.queries.tasks.linking import _relation_exists

        tx = MagicMock()
        result = MagicMock()
        result.resolve.return_value = []
        tx.query.return_value = result

        assert _relation_exists(tx, "match $x; select $x;") is False

    def test_helper_returns_false_for_none(self):
        """_relation_exists returns False when resolve returns None."""
        from governance.typedb.queries.tasks.linking import _relation_exists

        tx = MagicMock()
        result = MagicMock()
        result.resolve.return_value = None
        tx.query.return_value = result

        assert _relation_exists(tx, "match $x; select $x;") is False
