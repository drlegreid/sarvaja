"""Tests for heuristic check fixes from 2026-02-08 session.

Tests cover:
- H-TASK-005: Task-session auto-linking in create_task()
- H-SESSION-002: Backfill filter consistency
- H-SESSION-005/006: Backfill filter for tool calls / thoughts
- _is_backfilled_session() helper logic
- _get_active_session_id() helper logic
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestIsBackfilledSession:
    """Verify _is_backfilled_session() correctly identifies backfilled/test sessions."""

    def _check(self, session: dict) -> bool:
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session
        return _is_backfilled_session(session)

    def test_backfilled_description(self):
        """Sessions with 'backfill' in description are backfilled."""
        assert self._check({"description": "Backfilled from evidence file"})

    def test_stale_description(self):
        """Sessions with 'stale' in description are backfilled."""
        assert self._check({"description": "Stale test session"})

    def test_test_agent(self):
        """Sessions with agent ending in '-test' are test sessions."""
        assert self._check({"agent_id": "claude-code-test", "session_id": "S-123"})

    def test_no_agent_old_session(self):
        """Sessions without agent_id and old session ID are backfilled."""
        assert self._check({
            "agent_id": None,
            "session_id": "SESSION-2024-12-25-001",
        })

    def test_live_session_with_agent(self):
        """Live sessions with agent_id are NOT backfilled."""
        assert not self._check({
            "agent_id": "code-agent",
            "session_id": "SESSION-2026-02-08-TEST",
            "description": "Active work session",
        })

    def test_recent_session_no_agent(self):
        """Recent sessions (2026-02) without agent are NOT backfilled."""
        assert not self._check({
            "agent_id": None,
            "session_id": "SESSION-2026-02-01-WORK",
            "description": "Recent session",
        })

    def test_empty_session(self):
        """Edge: empty session dict — no agent, no session_id starting with 2026-02."""
        result = self._check({})
        # No agent and session_id doesn't start with SESSION-2026-02 → backfilled
        assert result is True


class TestGetActiveSessionId:
    """Verify _get_active_session_id() finds most recent active session."""

    @patch("governance.services.tasks._sessions_store", {
        "S-1": {"status": "ACTIVE", "start_time": "2026-02-08T10:00:00"},
        "S-2": {"status": "ACTIVE", "start_time": "2026-02-08T14:00:00"},
        "S-3": {"status": "COMPLETED", "start_time": "2026-02-08T15:00:00"},
    })
    def test_returns_most_recent_active(self):
        """Should return the most recent ACTIVE session by start_time."""
        from governance.services.tasks import _get_active_session_id
        assert _get_active_session_id() == "S-2"

    @patch("governance.services.tasks._sessions_store", {
        "S-1": {"status": "COMPLETED"},
        "S-2": {"status": "COMPLETED"},
    })
    def test_no_active_sessions(self):
        """Should return None when no active sessions exist."""
        from governance.services.tasks import _get_active_session_id
        assert _get_active_session_id() is None

    @patch("governance.services.tasks._sessions_store", {})
    def test_empty_store(self):
        """Should return None when session store is empty."""
        from governance.services.tasks import _get_active_session_id
        assert _get_active_session_id() is None


class TestTaskSessionAutoLinking:
    """H-TASK-005: create_task() auto-links to active session per DATA-LINK-01-v1."""

    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    @patch("governance.services.tasks._get_active_session_id", return_value="SESSION-ACTIVE-1")
    @patch("governance.services.tasks._tasks_store", {})
    def test_auto_links_when_no_sessions_provided(self, mock_sid, mock_client, mock_audit):
        """Task created without linked_sessions gets auto-linked to active session."""
        from governance.services.tasks import create_task
        result = create_task("TEST-AUTO-1", description="Test auto-link")
        assert result["linked_sessions"] == ["SESSION-ACTIVE-1"]

    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    @patch("governance.services.tasks._get_active_session_id", return_value="SESSION-ACTIVE-1")
    @patch("governance.services.tasks._tasks_store", {})
    def test_preserves_explicit_sessions(self, mock_sid, mock_client, mock_audit):
        """Task created WITH linked_sessions keeps the explicit list."""
        from governance.services.tasks import create_task
        result = create_task(
            "TEST-EXPLICIT-1", description="Has sessions",
            linked_sessions=["SESSION-MANUAL-1"],
        )
        assert result["linked_sessions"] == ["SESSION-MANUAL-1"]

    @patch("governance.services.tasks.record_audit")
    @patch("governance.services.tasks.get_typedb_client", return_value=None)
    @patch("governance.services.tasks._get_active_session_id", return_value=None)
    @patch("governance.services.tasks._tasks_store", {})
    def test_no_active_session_no_link(self, mock_sid, mock_client, mock_audit):
        """When no active session exists, linked_sessions stays None."""
        from governance.services.tasks import create_task
        result = create_task("TEST-NOLINK-1", description="No active session")
        assert result["linked_sessions"] == []


class TestHTaskCheckRefined:
    """H-TASK-005: Check only looks at IN_PROGRESS/DONE tasks, not OPEN/TODO."""

    @patch("governance.routes.tests.heuristic_checks._api_get")
    def test_skip_when_no_worked_tasks(self, mock_api):
        """Should SKIP when all tasks are OPEN/TODO."""
        mock_api.return_value = [
            {"task_id": "T-1", "status": "OPEN", "linked_sessions": None},
            {"task_id": "T-2", "status": "TODO", "linked_sessions": None},
        ]
        from governance.routes.tests.heuristic_checks import check_task_session_linkage
        result = check_task_session_linkage("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks._api_get")
    def test_fail_when_worked_task_unlinked(self, mock_api):
        """Should FAIL when IN_PROGRESS task has no linked_sessions."""
        mock_api.return_value = [
            {"task_id": "T-1", "status": "IN_PROGRESS", "linked_sessions": None},
            {"task_id": "T-2", "status": "OPEN", "linked_sessions": None},
        ]
        from governance.routes.tests.heuristic_checks import check_task_session_linkage
        result = check_task_session_linkage("http://test:8082")
        assert result["status"] == "FAIL"
        assert "T-1" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks._api_get")
    def test_pass_when_worked_tasks_linked(self, mock_api):
        """Should PASS when all IN_PROGRESS/DONE tasks have linked_sessions."""
        mock_api.return_value = [
            {"task_id": "T-1", "status": "IN_PROGRESS", "linked_sessions": ["S-1"]},
            {"task_id": "T-2", "status": "DONE", "linked_sessions": ["S-2"]},
            {"task_id": "T-3", "status": "OPEN", "linked_sessions": None},
        ]
        from governance.routes.tests.heuristic_checks import check_task_session_linkage
        result = check_task_session_linkage("http://test:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks._api_get")
    def test_excludes_test_tasks(self, mock_api):
        """TEST-* tasks are excluded from the check."""
        mock_api.return_value = [
            {"task_id": "TEST-1", "status": "IN_PROGRESS", "linked_sessions": None},
        ]
        from governance.routes.tests.heuristic_checks import check_task_session_linkage
        result = check_task_session_linkage("http://test:8082")
        assert result["status"] == "SKIP"


class TestHSessionCheckBackfillFilter:
    """H-SESSION-002/005/006: Backfill filter consistency across all session checks."""

    @patch("governance.routes.tests.heuristic_checks_session._api_get")
    @patch("governance.routes.tests.heuristic_checks_session._get_completed_sessions")
    def test_h002_skips_all_backfilled(self, mock_completed, mock_api):
        """H-SESSION-002 should SKIP when all sessions are backfilled."""
        mock_completed.return_value = [
            {"session_id": "SESSION-2024-12-25-001", "status": "COMPLETED",
             "description": "Backfilled from evidence file", "agent_id": None},
        ]
        from governance.routes.tests.heuristic_checks_session import check_session_evidence_files
        result = check_session_evidence_files("http://test:8082")
        assert result["status"] == "SKIP"
        assert "backfilled" in result["message"].lower()

    @patch("governance.routes.tests.heuristic_checks_session._api_get")
    @patch("governance.routes.tests.heuristic_checks_session._get_completed_sessions")
    def test_h005_skips_all_backfilled(self, mock_completed, mock_api):
        """H-SESSION-005 should SKIP when all sessions are backfilled."""
        mock_completed.return_value = [
            {"session_id": "SESSION-2024-12-25-001", "status": "COMPLETED",
             "description": "Backfilled from evidence file", "agent_id": None},
        ]
        from governance.routes.tests.heuristic_checks_session import check_session_tool_calls
        result = check_session_tool_calls("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_session._api_get")
    @patch("governance.routes.tests.heuristic_checks_session._get_completed_sessions")
    def test_h006_skips_all_backfilled(self, mock_completed, mock_api):
        """H-SESSION-006 should SKIP when all sessions are backfilled."""
        mock_completed.return_value = [
            {"session_id": "SESSION-2024-12-25-001", "status": "COMPLETED",
             "description": "Backfilled from evidence file", "agent_id": None},
        ]
        from governance.routes.tests.heuristic_checks_session import check_session_thoughts
        result = check_session_thoughts("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_session._api_get")
    @patch("governance.routes.tests.heuristic_checks_session._get_completed_sessions")
    def test_h005_skips_test_agent(self, mock_completed, mock_api):
        """H-SESSION-005 should skip sessions with test agent."""
        mock_completed.return_value = [
            {"session_id": "SESSION-2026-01-30-45A2EB", "status": "COMPLETED",
             "description": "Exploratory API test session",
             "agent_id": "claude-code-test"},
        ]
        from governance.routes.tests.heuristic_checks_session import check_session_tool_calls
        result = check_session_tool_calls("http://test:8082")
        assert result["status"] == "SKIP"
