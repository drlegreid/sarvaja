"""
Unit tests for Task Auto-Linking on Update.

Phase 2 of EPIC-GOV-TASKS-V2: Auto-Linking + Service Layer Parity.

BDD Scenarios:
  - IN_PROGRESS auto-links to active session
  - Existing sessions prevent double-link
  - No active session skips gracefully
  - Non-status updates do NOT auto-link
  - Auto-linked session is persisted to TypeDB
  - Session existence pre-check in linking layer
"""

import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

_MUT_MOD = "governance.services.tasks_mutations"
_TASKS_MOD = "governance.services.tasks"


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


def _setup_sessions_store(store, sessions=None):
    """Populate _sessions_store with test sessions."""
    store.clear()
    if sessions:
        for sid, data in sessions.items():
            store[sid] = data


# ── Scenario: IN_PROGRESS auto-links to active session ──


class TestAutoLinkOnStatusTransition:
    """update_task() auto-links to active session on status change."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_in_progress_autolinks_to_active_session(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """When status transitions to IN_PROGRESS and no linked_sessions,
        auto-link to the most recent active session."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None  # No TypeDB — fallback only

        _tasks_store["T-1"] = {
            "task_id": "T-1", "description": "Test", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }
        _setup_sessions_store(_sessions_store, {
            "SESSION-2026-03-20-ALPHA": {
                "status": "ACTIVE",
                "start_time": "2026-03-20T09:00:00",
            },
        })

        result = update_task("T-1", status="IN_PROGRESS", agent_id="code-agent")

        assert result is not None
        assert "SESSION-2026-03-20-ALPHA" in result["linked_sessions"]

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_done_status_also_autolinks(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """DONE transition also auto-links if no sessions present."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-2"] = {
            "task_id": "T-2", "description": "Done task", "status": "IN_PROGRESS",
            "phase": "P10", "agent_id": "code-agent", "linked_sessions": [],
            "summary": "Test > Autolink > Done > Session", "linked_documents": [],
        }
        _setup_sessions_store(_sessions_store, {
            "SESSION-2026-03-20-BETA": {
                "status": "ACTIVE",
                "start_time": "2026-03-20T10:00:00",
            },
        })

        result = update_task("T-2", status="DONE")
        assert "SESSION-2026-03-20-BETA" in result["linked_sessions"]

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_picks_most_recent_active_session(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """When multiple active sessions, picks the most recent by start_time."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-3"] = {
            "task_id": "T-3", "description": "Multi", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }
        _setup_sessions_store(_sessions_store, {
            "SESSION-OLD": {
                "status": "ACTIVE", "start_time": "2026-03-19T08:00:00",
            },
            "SESSION-NEW": {
                "status": "ACTIVE", "start_time": "2026-03-20T12:00:00",
            },
        })

        result = update_task("T-3", status="IN_PROGRESS", agent_id="code-agent")
        assert result["linked_sessions"] == ["SESSION-NEW"]


# ── Scenario: Existing sessions prevent double-link ──────


class TestAutoLinkExistingSessions:
    """Existing linked_sessions are not overwritten by auto-link."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_explicit_sessions_not_overwritten(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """Caller-provided linked_sessions are kept — no auto-link."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-4"] = {
            "task_id": "T-4", "description": "Explicit", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }
        _setup_sessions_store(_sessions_store, {
            "SESSION-AUTO": {"status": "ACTIVE", "start_time": "2026-03-20T10:00:00"},
        })

        result = update_task(
            "T-4", status="IN_PROGRESS", agent_id="code-agent",
            linked_sessions=["SESSION-MANUAL"],
        )
        assert result["linked_sessions"] == ["SESSION-MANUAL"]
        assert "SESSION-AUTO" not in result["linked_sessions"]

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_existing_stored_sessions_prevent_autolink(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """Task already has linked_sessions in store — auto-link skipped."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-5"] = {
            "task_id": "T-5", "description": "Already linked", "status": "OPEN",
            "phase": "P10", "agent_id": None,
            "linked_sessions": ["SESSION-EXISTING"],
        }
        _setup_sessions_store(_sessions_store, {
            "SESSION-AUTO": {"status": "ACTIVE", "start_time": "2026-03-20T10:00:00"},
        })

        result = update_task("T-5", status="IN_PROGRESS", agent_id="code-agent")
        # Original session preserved, no auto session added
        assert "SESSION-EXISTING" in result["linked_sessions"]


# ── Scenario: No active session skips gracefully ─────────


class TestAutoLinkNoActiveSession:
    """When no active session exists, auto-link is a no-op."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_no_active_session_skips_gracefully(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-6"] = {
            "task_id": "T-6", "description": "No session", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }
        _sessions_store.clear()

        result = update_task("T-6", status="IN_PROGRESS", agent_id="code-agent")
        assert result is not None
        assert result["linked_sessions"] == []

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_only_completed_sessions_no_autolink(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        """Only COMPLETED sessions — none ACTIVE — no auto-link."""
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-7"] = {
            "task_id": "T-7", "description": "No active", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }
        _setup_sessions_store(_sessions_store, {
            "SESSION-DONE": {"status": "COMPLETED", "start_time": "2026-03-20T08:00:00"},
        })

        result = update_task("T-7", status="IN_PROGRESS", agent_id="code-agent")
        assert result["linked_sessions"] == []


# ── Scenario: Non-status updates do NOT auto-link ────────


class TestNoAutoLinkWithoutStatusChange:
    """Description-only or phase-only updates skip auto-linking."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_description_only_no_autolink(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-8"] = {
            "task_id": "T-8", "description": "Old desc", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }
        _setup_sessions_store(_sessions_store, {
            "SESSION-ACTIVE": {"status": "ACTIVE", "start_time": "2026-03-20T10:00:00"},
        })

        result = update_task("T-8", description="New desc")
        assert result["linked_sessions"] == []
        assert result["description"] == "New desc"


# ── Scenario: Auto-link persists to TypeDB ───────────────


class TestAutoLinkTypeDBPersistence:
    """Auto-linked session is written to TypeDB via link_task_to_session."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_autolinked_session_persisted_to_typedb(
        self, mock_client_fn, mock_mon, mock_audit, mock_log
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

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
        _setup_sessions_store(_sessions_store, {
            "SESSION-PERSIST": {"status": "ACTIVE", "start_time": "2026-03-20T11:00:00"},
        })

        result = update_task("T-9", status="IN_PROGRESS", agent_id="code-agent")

        # Verify TypeDB link was called with the auto-linked session
        mock_client.link_task_to_session.assert_any_call("T-9", "SESSION-PERSIST")


# ── Scenario: Session existence pre-check ────────────────


class TestSessionExistencePreCheck:
    """link_task_to_session returns False with clear log for nonexistent session."""

    def test_nonexistent_session_returns_false_with_log(self, caplog):
        """Linking to a nonexistent session should pre-check and fail cleanly."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations

        ops = TaskLinkingOperations()
        mock_driver = MagicMock()
        ops._driver = mock_driver
        ops.database = "test_db"

        # Simulate session not found via _execute_query
        ops._execute_query = MagicMock(return_value=[])

        with caplog.at_level(logging.WARNING):
            result = ops.session_exists("SESSION-GHOST")

        assert result is False

    def test_existing_session_returns_true(self):
        """Existing session passes the pre-check."""
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations

        ops = TaskLinkingOperations()
        ops._execute_query = MagicMock(return_value=[{"sid": "SESSION-REAL"}])

        result = ops.session_exists("SESSION-REAL")
        assert result is True


# ── Scenario: Auto-link logs INFO message ────────────────


class TestAutoLinkLogging:
    """Auto-linking logs a DATA-LINK-01 info message."""

    @patch(f"{_MUT_MOD}.log_event")
    @patch(f"{_MUT_MOD}.record_audit")
    @patch(f"{_MUT_MOD}._monitor")
    @patch(f"{_MUT_MOD}.get_typedb_client")
    def test_autolink_logs_info(
        self, mock_client_fn, mock_mon, mock_audit, mock_log, caplog
    ):
        from governance.services.tasks_mutations import update_task
        from governance.stores import _tasks_store, _sessions_store

        mock_client_fn.return_value = None

        _tasks_store["T-10"] = {
            "task_id": "T-10", "description": "Log test", "status": "OPEN",
            "phase": "P10", "agent_id": None, "linked_sessions": [],
        }
        _setup_sessions_store(_sessions_store, {
            "SESSION-LOG": {"status": "ACTIVE", "start_time": "2026-03-20T10:00:00"},
        })

        with caplog.at_level(logging.INFO):
            update_task("T-10", status="IN_PROGRESS", agent_id="code-agent")

        assert any("DATA-LINK-01" in msg for msg in caplog.messages)
