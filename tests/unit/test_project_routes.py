"""
Route tests for Project CRUD endpoints.

Per GOV-PROJECT-01-v1: Tests for /api/projects REST API.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestProjectRoutes:
    """Tests for project CRUD API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    # --- LIST ---

    @patch("governance.routes.projects.crud.project_service")
    def test_list_projects_empty(self, mock_svc, client):
        mock_svc.list_projects.return_value = {
            "items": [],
            "pagination": {
                "total": 0, "offset": 0, "limit": 50,
                "has_more": False, "returned": 0,
            },
        }
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["pagination"]["total"] == 0

    @patch("governance.routes.projects.crud.project_service")
    def test_list_projects_with_items(self, mock_svc, client):
        mock_svc.list_projects.return_value = {
            "items": [
                {"project_id": "PROJ-1", "name": "Alpha", "path": None,
                 "plan_count": 2, "session_count": 5},
                {"project_id": "PROJ-2", "name": "Beta", "path": "/tmp",
                 "plan_count": 0, "session_count": 3},
            ],
            "pagination": {
                "total": 2, "offset": 0, "limit": 50,
                "has_more": False, "returned": 2,
            },
        }
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["project_id"] == "PROJ-1"

    @patch("governance.routes.projects.crud.project_service")
    def test_list_projects_with_pagination(self, mock_svc, client):
        mock_svc.list_projects.return_value = {
            "items": [{"project_id": "PROJ-1", "name": "A", "path": None,
                        "plan_count": 0, "session_count": 0}],
            "pagination": {
                "total": 10, "offset": 5, "limit": 5,
                "has_more": True, "returned": 1,
            },
        }
        resp = client.get("/api/projects?limit=5&offset=5")
        assert resp.status_code == 200
        mock_svc.list_projects.assert_called_once_with(limit=5, offset=5)

    # --- CREATE ---

    @patch("governance.routes.projects.crud.project_service")
    def test_create_project(self, mock_svc, client):
        mock_svc.create_project.return_value = {
            "project_id": "PROJ-NEW", "name": "New Project",
            "path": "/tmp/new", "plan_count": 0, "session_count": 0,
        }
        resp = client.post("/api/projects", json={
            "project_id": "PROJ-NEW", "name": "New Project", "path": "/tmp/new",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_id"] == "PROJ-NEW"
        assert data["name"] == "New Project"

    @patch("governance.routes.projects.crud.project_service")
    def test_create_project_minimal(self, mock_svc, client):
        mock_svc.create_project.return_value = {
            "project_id": "PROJ-AUTO", "name": "Minimal",
            "path": None, "plan_count": 0, "session_count": 0,
        }
        resp = client.post("/api/projects", json={"name": "Minimal"})
        assert resp.status_code == 201

    @patch("governance.routes.projects.crud.project_service")
    def test_create_project_conflict(self, mock_svc, client):
        mock_svc.create_project.return_value = None
        resp = client.post("/api/projects", json={
            "project_id": "PROJ-DUP", "name": "Duplicate",
        })
        assert resp.status_code == 409

    def test_create_project_missing_name(self, client):
        resp = client.post("/api/projects", json={})
        assert resp.status_code == 422

    # --- GET ---

    @patch("governance.routes.projects.crud.project_service")
    def test_get_project(self, mock_svc, client):
        mock_svc.get_project.return_value = {
            "project_id": "PROJ-1", "name": "Test",
            "path": "/home/test", "plan_count": 1, "session_count": 3,
        }
        resp = client.get("/api/projects/PROJ-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "PROJ-1"
        assert data["plan_count"] == 1

    @patch("governance.routes.projects.crud.project_service")
    def test_get_project_not_found(self, mock_svc, client):
        mock_svc.get_project.return_value = None
        resp = client.get("/api/projects/PROJ-NOPE")
        assert resp.status_code == 404

    # --- DELETE ---

    @patch("governance.routes.projects.crud.project_service")
    def test_delete_project(self, mock_svc, client):
        mock_svc.delete_project.return_value = True
        resp = client.delete("/api/projects/PROJ-DEL")
        assert resp.status_code == 204

    @patch("governance.routes.projects.crud.project_service")
    def test_delete_project_not_found(self, mock_svc, client):
        mock_svc.delete_project.return_value = False
        resp = client.delete("/api/projects/PROJ-NOPE")
        assert resp.status_code == 404

    # --- LINK SESSION ---

    @patch("governance.routes.projects.crud.project_service")
    def test_link_session_to_project(self, mock_svc, client):
        mock_svc.link_session_to_project.return_value = True
        resp = client.post("/api/projects/PROJ-1/sessions/SESSION-123")
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "linked"
        assert data["project_id"] == "PROJ-1"
        assert data["session_id"] == "SESSION-123"

    @patch("governance.routes.projects.crud.project_service")
    def test_link_session_failure(self, mock_svc, client):
        mock_svc.link_session_to_project.return_value = False
        resp = client.post("/api/projects/PROJ-1/sessions/SESSION-BAD")
        assert resp.status_code == 400
