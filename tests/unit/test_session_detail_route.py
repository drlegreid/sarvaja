"""
Route tests for Session Detail / Lazy Loading endpoint.

Per DATA-LAZY-01-v1: Tests for GET /api/sessions/{id}/detail?zoom=N.
"""

import pytest
from unittest.mock import patch


class TestSessionDetailRoute:
    """Tests for the session detail lazy loading endpoint."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_zoom_0_summary(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "S-1",
            "zoom": 0,
            "summary": {
                "status": "COMPLETED",
                "description": "Test session",
                "start_time": "2026-02-11T10:00:00Z",
                "end_time": "2026-02-11T11:00:00Z",
                "cc_session_uuid": "uuid-1",
                "cc_project_slug": "test",
                "cc_git_branch": "master",
                "cc_tool_count": 42,
                "cc_thinking_chars": 5000,
                "cc_compaction_count": 2,
            },
        }
        resp = client.get("/api/sessions/S-1/detail?zoom=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["zoom"] == 0
        assert data["summary"]["cc_tool_count"] == 42
        mock_detail.assert_called_once_with("S-1", zoom=0)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_zoom_1_with_breakdown(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "S-2",
            "zoom": 1,
            "summary": {"status": "COMPLETED"},
            "tool_breakdown": {"Read": 15, "Write": 8, "Bash": 5},
            "thinking_summary": {"total_chars": 10000, "estimated_tokens": 2500},
        }
        resp = client.get("/api/sessions/S-2/detail?zoom=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["zoom"] == 1
        assert "tool_breakdown" in data
        assert data["tool_breakdown"]["Read"] == 15

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_default_zoom_is_1(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "S-3", "zoom": 1, "summary": {},
        }
        resp = client.get("/api/sessions/S-3/detail")
        assert resp.status_code == 200
        mock_detail.assert_called_once_with("S-3", zoom=1)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_session_not_found(self, mock_detail, client):
        mock_detail.return_value = None
        resp = client.get("/api/sessions/NOPE/detail")
        assert resp.status_code == 404

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_zoom_out_of_range(self, mock_detail, client):
        resp = client.get("/api/sessions/S-1/detail?zoom=5")
        assert resp.status_code == 422

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_zoom_negative(self, mock_detail, client):
        resp = client.get("/api/sessions/S-1/detail?zoom=-1")
        assert resp.status_code == 422

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_zoom_2(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "S-4", "zoom": 2, "summary": {},
        }
        resp = client.get("/api/sessions/S-4/detail?zoom=2")
        assert resp.status_code == 200
        mock_detail.assert_called_once_with("S-4", zoom=2)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_zoom_3_max(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "S-5", "zoom": 3, "summary": {},
        }
        resp = client.get("/api/sessions/S-5/detail?zoom=3")
        assert resp.status_code == 200
        mock_detail.assert_called_once_with("S-5", zoom=3)
