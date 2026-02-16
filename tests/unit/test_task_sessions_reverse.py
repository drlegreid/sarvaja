"""Tests for reverse task-session query (get_sessions_for_task).

Per GAP-SESSION-CC-AUTO-DISCOVERY: Unlock task→session reverse lookup.
"""

from unittest.mock import MagicMock, patch

import pytest

from governance.services.tasks import get_sessions_for_task


class TestGetSessionsForTask:
    """Tests for get_sessions_for_task() service function."""

    @patch("governance.services.tasks.get_task")
    @patch("governance.services.sessions.get_session")
    def test_returns_full_session_details(self, mock_get_session, mock_get_task):
        """Should resolve session IDs to full session dicts."""
        mock_get_task.return_value = {
            "task_id": "T-001",
            "linked_sessions": ["SESSION-A", "SESSION-B"],
        }
        mock_get_session.side_effect = [
            {"session_id": "SESSION-A", "status": "COMPLETED", "description": "Work A"},
            {"session_id": "SESSION-B", "status": "ACTIVE", "description": "Work B"},
        ]

        result = get_sessions_for_task("T-001")
        assert len(result) == 2
        assert result[0]["session_id"] == "SESSION-A"
        assert result[1]["session_id"] == "SESSION-B"

    @patch("governance.services.tasks.get_task")
    def test_returns_empty_for_missing_task(self, mock_get_task):
        """Should return empty list when task not found."""
        mock_get_task.return_value = None
        result = get_sessions_for_task("NONEXIST")
        assert result == []

    @patch("governance.services.tasks.get_task")
    def test_returns_empty_for_no_linked_sessions(self, mock_get_task):
        """Should return empty list when task has no linked sessions."""
        mock_get_task.return_value = {
            "task_id": "T-001",
            "linked_sessions": [],
        }
        result = get_sessions_for_task("T-001")
        assert result == []

    @patch("governance.services.tasks.get_task")
    def test_returns_empty_for_null_linked_sessions(self, mock_get_task):
        """Should handle None linked_sessions gracefully."""
        mock_get_task.return_value = {
            "task_id": "T-001",
            "linked_sessions": None,
        }
        result = get_sessions_for_task("T-001")
        assert result == []

    @patch("governance.services.tasks.get_task")
    @patch("governance.services.sessions.get_session")
    def test_returns_stub_for_missing_sessions(self, mock_get_session, mock_get_task):
        """Should return minimal stub when session not found in service."""
        mock_get_task.return_value = {
            "task_id": "T-001",
            "linked_sessions": ["SESSION-GONE"],
        }
        mock_get_session.return_value = None

        result = get_sessions_for_task("T-001")
        assert len(result) == 1
        assert result[0]["session_id"] == "SESSION-GONE"
        assert result[0]["status"] == "UNKNOWN"

    @patch("governance.services.tasks.get_task")
    @patch("governance.services.sessions.get_session")
    def test_mixed_found_and_missing(self, mock_get_session, mock_get_task):
        """Should handle mix of found and missing sessions."""
        mock_get_task.return_value = {
            "task_id": "T-001",
            "linked_sessions": ["SESSION-OK", "SESSION-GONE"],
        }
        mock_get_session.side_effect = [
            {"session_id": "SESSION-OK", "status": "COMPLETED"},
            None,
        ]

        result = get_sessions_for_task("T-001")
        assert len(result) == 2
        assert result[0]["status"] == "COMPLETED"
        assert result[1]["status"] == "UNKNOWN"


class TestTaskSessionsRoute:
    """Tests for GET /tasks/{task_id}/sessions route."""

    @patch("governance.services.tasks.get_sessions_for_task")
    def test_returns_sessions_list(self, mock_func):
        """Should return task_id, sessions, and count."""
        from fastapi.testclient import TestClient
        from governance.routes.tasks.crud import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")

        mock_func.return_value = [
            {"session_id": "S-1", "status": "COMPLETED"},
            {"session_id": "S-2", "status": "ACTIVE"},
        ]

        client = TestClient(app)
        resp = client.get("/api/tasks/T-001/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == "T-001"
        assert data["count"] == 2
        assert len(data["sessions"]) == 2

    @patch("governance.services.tasks.get_sessions_for_task")
    def test_returns_empty_sessions(self, mock_func):
        """Should return empty list when no sessions linked."""
        from fastapi.testclient import TestClient
        from governance.routes.tasks.crud import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")
        mock_func.return_value = []

        client = TestClient(app)
        resp = client.get("/api/tasks/T-001/sessions")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0
