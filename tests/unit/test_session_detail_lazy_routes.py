"""
Unit tests for Session Detail & Lazy Loading Routes.

Per GAP-TEST-CRUD-001: Orthogonal CRUD test coverage for session
detail, tools, thoughts, and evidence rendering endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSessionDetail:
    """Tests for GET /sessions/{id}/detail."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_detail_zoom_0(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "SESSION-1",
            "summary": {"tool_count": 5, "duration": 120},
        }
        resp = client.get("/api/sessions/SESSION-1/detail?zoom=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "SESSION-1"
        mock_detail.assert_called_once_with("SESSION-1", zoom=0, page=1, per_page=20)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_detail_zoom_3(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "SESSION-1",
            "thinking_blocks": [{"content": "Let me think..."}],
            "thinking_blocks_total": 1,
        }
        resp = client.get("/api/sessions/SESSION-1/detail?zoom=3&page=2&per_page=10")
        assert resp.status_code == 200
        mock_detail.assert_called_once_with("SESSION-1", zoom=3, page=2, per_page=10)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_detail_not_found(self, mock_detail, client):
        mock_detail.return_value = None
        resp = client.get("/api/sessions/SESSION-NOPE/detail")
        assert resp.status_code == 404

    def test_detail_zoom_out_of_range(self, client):
        resp = client.get("/api/sessions/S-1/detail?zoom=5")
        assert resp.status_code == 422

    def test_detail_page_zero(self, client):
        resp = client.get("/api/sessions/S-1/detail?page=0")
        assert resp.status_code == 422

    def test_detail_per_page_too_large(self, client):
        resp = client.get("/api/sessions/S-1/detail?per_page=200")
        assert resp.status_code == 422


class TestSessionTools:
    """Tests for GET /sessions/{id}/tools."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_tools_success(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "SESSION-1",
            "tool_calls": [
                {"tool": "Read", "input": "file.py"},
                {"tool": "Edit", "input": "other.py"},
            ],
            "tool_calls_total": 15,
        }
        resp = client.get("/api/sessions/SESSION-1/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "SESSION-1"
        assert len(data["tool_calls"]) == 2
        assert data["total"] == 15
        assert data["page"] == 1

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_tools_pagination(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "SESSION-1",
            "tool_calls": [{"tool": "Bash"}],
            "tool_calls_total": 50,
        }
        resp = client.get("/api/sessions/SESSION-1/tools?page=3&per_page=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 3
        assert data["per_page"] == 10
        mock_detail.assert_called_once_with("SESSION-1", zoom=2, page=3, per_page=10)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_tools_not_found(self, mock_detail, client):
        mock_detail.return_value = None
        resp = client.get("/api/sessions/SESSION-NOPE/tools")
        assert resp.status_code == 404


class TestSessionThoughts:
    """Tests for GET /sessions/{id}/thoughts."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_thoughts_success(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "SESSION-1",
            "thinking_blocks": [
                {"content": "I should check the schema first"},
            ],
            "thinking_blocks_total": 5,
        }
        resp = client.get("/api/sessions/SESSION-1/thoughts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "SESSION-1"
        assert len(data["thinking_blocks"]) == 1
        assert data["total"] == 5

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_thoughts_not_found(self, mock_detail, client):
        mock_detail.return_value = None
        resp = client.get("/api/sessions/SESSION-NOPE/thoughts")
        assert resp.status_code == 404

    @patch("governance.routes.sessions.detail.get_session_detail")
    def test_thoughts_empty(self, mock_detail, client):
        mock_detail.return_value = {
            "session_id": "SESSION-1",
            "thinking_blocks": [],
            "thinking_blocks_total": 0,
        }
        resp = client.get("/api/sessions/SESSION-1/thoughts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["thinking_blocks"] == []
        assert data["total"] == 0


class TestSessionEvidenceRendered:
    """Tests for GET /sessions/{id}/evidence/rendered."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    @patch("governance.services.sessions.get_session")
    def test_evidence_rendered_success(self, mock_get, client, tmp_path):
        import os
        # BUG-ROUTE-PATH-001: Evidence must be in project evidence/ directory
        # Create test file inside the project's evidence directory
        project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        evidence_dir = os.path.join(project_root, "evidence")
        os.makedirs(evidence_dir, exist_ok=True)
        test_file = os.path.join(evidence_dir, "_test_evidence_rendered.md")
        try:
            with open(test_file, "w") as f:
                f.write("# Session Report\n\nAll tasks completed.")
            mock_get.return_value = {
                "session_id": "SESSION-1",
                "file_path": test_file,
            }
            resp = client.get("/api/sessions/SESSION-1/evidence/rendered")
            assert resp.status_code == 200
            data = resp.json()
            assert data["session_id"] == "SESSION-1"
            assert "<h1>" in data["html"] or "Session Report" in data["html"]
            assert "All tasks completed" in data["raw"]
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    @patch("governance.services.sessions.get_session")
    def test_evidence_rendered_no_session(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/sessions/SESSION-NOPE/evidence/rendered")
        assert resp.status_code == 404

    @patch("governance.services.sessions.get_session")
    def test_evidence_rendered_no_file_path(self, mock_get, client):
        mock_get.return_value = {"session_id": "SESSION-1", "file_path": None}
        resp = client.get("/api/sessions/SESSION-1/evidence/rendered")
        assert resp.status_code == 404
        assert "No evidence file" in resp.json()["detail"]

    @patch("governance.services.sessions.get_session")
    def test_evidence_rendered_file_missing(self, mock_get, client):
        import os
        # BUG-ROUTE-PATH-001: Path must be within evidence dir to reach 404
        project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        evidence_dir = os.path.join(project_root, "evidence")
        missing_file = os.path.join(evidence_dir, "nonexistent_evidence_file_xyz.md")
        mock_get.return_value = {
            "session_id": "SESSION-1",
            "file_path": missing_file,
        }
        resp = client.get("/api/sessions/SESSION-1/evidence/rendered")
        assert resp.status_code == 404
        assert "not found on disk" in resp.json()["detail"]
