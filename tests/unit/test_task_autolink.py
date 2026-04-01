"""
Unit tests for Task Session Linking — Deterministic Identity (P9).

P9 (BUG-SESSION-POISON-01): Auto-linking removed. Session must be explicit.
Previously tested auto-link behavior; now tests verify explicit-only linking.

BDD Scenarios:
  - Status transition WITHOUT session_id → no linked session
  - Explicit linked_sessions preserved on update
  - No auto-link even with active sessions in store
  - Session existence pre-check in linking layer
"""

import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

_MUT_MOD = "governance.services.tasks_mutations"


# ── Helpers ─────────────────────────────────────────────


def _make_task_obj(task_id="T-1", status="OPEN", agent_id=None,
                   name="Test", phase="P10", linked_sessions=None,
                   priority=None, task_type=None):
    """Create a mock task object with needed attributes."""
    obj = MagicMock()
    obj.task_id = task_id
    obj.name = name
    obj.status = status
    obj.phase = phase
    obj.agent_id = agent_id
    obj.priority = priority
    obj.task_type = task_type
    obj.created_at = datetime(2026, 1, 1)
    obj.body = None
    obj.gap_id = None
    obj.evidence = None
    obj.resolution = None
    obj.claimed_at = None
    obj.completed_at = None
    obj.document_path = None
    obj.linked_rules = []
    obj.linked_sessions = linked_sessions or []
    obj.linked_commits = []
    obj.linked_documents = []
    return obj


# ── Scenario: Status transition without session → no link ──


class TestNoAutoLinkOnStatusTransition:
    """P9: update_task() does NOT auto-link on status change."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_in_progress_no_autolink(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """IN_PROGRESS without session_id → linked_sessions=[]."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-1"] = {
            "task_id": "T-1", "description": "Test", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }
        _sessions_store["SESSION-ACTIVE"] = {
            "status": "ACTIVE", "start_time": "2026-03-28T09:00:00",
        }

        try:
            result = update_task("T-1", status="IN_PROGRESS", agent_id="code-agent")
            assert result["linked_sessions"] == []
        finally:
            _sessions_store.pop("SESSION-ACTIVE", None)

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_done_status_no_autolink(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """DONE transition without session_id → no auto-link."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-2"] = {
            "task_id": "T-2", "description": "Done task", "status": "IN_PROGRESS",
            "phase": "P10", "agent_id": "code-agent", "linked_sessions": [],
            "summary": "Test > Autolink > Done > Session",
            "linked_documents": [".claude/plans/test-plan.md"],
        }
        _sessions_store["SESSION-BETA"] = {
            "status": "ACTIVE", "start_time": "2026-03-28T10:00:00",
        }

        try:
            result = update_task("T-2", status="DONE")
            assert result["linked_sessions"] == []
        finally:
            _sessions_store.pop("SESSION-BETA", None)


# ── Scenario: Explicit sessions preserved ─────────────────


class TestExplicitSessionLinking:
    """Explicit linked_sessions parameter is the ONLY way to link."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_explicit_sessions_preserved(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """Caller-provided linked_sessions are stored."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        mock_client_fn.return_value = None

        _tasks_store["T-4"] = {
            "task_id": "T-4", "description": "Explicit", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
            "linked_rules": [], "linked_documents": [],
        }

        result = update_task(
            "T-4", status="IN_PROGRESS", agent_id="code-agent",
            linked_sessions=["SESSION-MANUAL"],
        )
        assert result["linked_sessions"] == ["SESSION-MANUAL"]

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_existing_stored_sessions_preserved(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """Task with existing linked_sessions keeps them on update."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        mock_client_fn.return_value = None

        _tasks_store["T-5"] = {
            "task_id": "T-5", "description": "Already linked", "status": "OPEN",
            "phase": "P10", "agent_id": None,
            "linked_sessions": ["SESSION-EXISTING"],
        }

        result = update_task("T-5", status="IN_PROGRESS", agent_id="code-agent")
        assert "SESSION-EXISTING" in result["linked_sessions"]


# ── Scenario: Description-only updates never link ─────────


class TestNoLinkWithoutStatusChange:
    """Non-status updates never trigger session linking."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_description_only_no_link(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        mock_client_fn.return_value = None

        _tasks_store["T-8"] = {
            "task_id": "T-8", "description": "Old desc", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }

        result = update_task("T-8", description="New desc")
        assert result["linked_sessions"] == []
        assert result["description"] == "New desc"


# ── Scenario: Explicit link persists to TypeDB ────────────


class TestExplicitLinkTypeDBPersistence:
    """Explicit linked_sessions written to TypeDB via link_task_to_session."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_explicit_session_persisted_to_typedb(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        mock_client = MagicMock()
        mock_client.get_task.return_value = _make_task_obj(
            "T-9", status="OPEN", linked_sessions=[]
        )
        mock_client.update_task_status.return_value = _make_task_obj(
            "T-9", status="IN_PROGRESS"
        )
        mock_client.link_task_to_session.return_value = True
        mock_client_fn.return_value = mock_client

        _tasks_store.pop("T-9", None)

        update_task(
            "T-9", status="IN_PROGRESS", agent_id="code-agent",
            linked_sessions=["SESSION-EXPLICIT"],
        )

        mock_client.link_task_to_session.assert_any_call("T-9", "SESSION-EXPLICIT")


# ── Scenario: Session existence pre-check ────────────────


class TestSessionExistencePreCheck:
    """link_task_to_session returns False with clear log for nonexistent session."""

    def test_nonexistent_session_returns_false_with_log(self, caplog):
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations

        ops = TaskLinkingOperations()
        mock_driver = MagicMock()
        ops._driver = mock_driver
        ops.database = "test_db"
        ops._execute_query = MagicMock(return_value=[])

        with caplog.at_level(logging.WARNING):
            result = ops.session_exists("SESSION-GHOST")

        assert result is False

    def test_existing_session_returns_true(self):
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations

        ops = TaskLinkingOperations()
        ops._execute_query = MagicMock(return_value=[{"sid": "SESSION-REAL"}])

        result = ops.session_exists("SESSION-REAL")
        assert result is True


# ── Scenario: No DATA-LINK-01 logging (auto-link removed) ──


class TestNoAutoLinkLogging:
    """P9: No DATA-LINK-01 auto-link log message on status transition."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_no_autolink_log_on_update(
        self, mock_client_fn, mock_mon, mock_audit, mock_log, caplog
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store

        mock_client_fn.return_value = None

        _tasks_store["T-10"] = {
            "task_id": "T-10", "description": "Log test", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }

        with caplog.at_level(logging.INFO):
            update_task("T-10", status="IN_PROGRESS", agent_id="code-agent")

        # DATA-LINK-01 auto-link messages must NOT appear
        assert not any("DATA-LINK-01" in msg for msg in caplog.messages), (
            "Auto-link DATA-LINK-01 log found — should be removed by P9"
        )
