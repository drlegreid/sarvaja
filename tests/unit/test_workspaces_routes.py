"""
Route tests for Workspace CRUD API endpoints.

Tests for governance/routes/workspaces/crud.py — Workspace entity CRUD.
"""

import pytest
from unittest.mock import patch


# Sample workspace dict for reuse across tests.
_SAMPLE_WS = {
    "workspace_id": "WS-1",
    "name": "Dev Workspace",
    "workspace_type": "development",
    "project_id": "PROJ-1",
    "description": "Primary dev workspace",
    "status": "active",
    "created_at": "2026-02-21T10:00:00",
    "agent_ids": ["agent-1", "agent-2"],
    "default_rules": ["RULE-A"],
    "capabilities": ["coding"],
    "icon": "mdi-code-braces",
    "color": "#3b82f6",
}

_SAMPLE_WS_TYPE = {
    "type_id": "development",
    "name": "Development",
    "description": "Software development workspace",
    "icon": "mdi-code-braces",
    "color": "#3b82f6",
    "mcp_servers": ["rest-api"],
    "agent_templates": [],
    "default_rules": ["RULE-A"],
    "capabilities": ["coding"],
    "commands": ["build", "test"],
    "file_patterns": ["*.py", "*.ts"],
    "tags": ["dev"],
}


class TestWorkspacesRoutes:
    """Tests for workspace CRUD API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    # -------------------------------------------------------------------------
    # GET /api/workspaces — list
    # -------------------------------------------------------------------------

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_list_workspaces_empty(self, mock_svc, client):
        mock_svc.list_workspaces.return_value = {"items": []}
        resp = client.get("/api/workspaces")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_list_workspaces_with_items(self, mock_svc, client):
        mock_svc.list_workspaces.return_value = {"items": [_SAMPLE_WS]}
        resp = client.get("/api/workspaces")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["workspace_id"] == "WS-1"
        assert data[0]["name"] == "Dev Workspace"

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_list_workspaces_with_filters(self, mock_svc, client):
        mock_svc.list_workspaces.return_value = {"items": [_SAMPLE_WS]}
        resp = client.get(
            "/api/workspaces?project_id=PROJ-1&workspace_type=development"
            "&status=active&offset=0&limit=10"
        )
        assert resp.status_code == 200
        mock_svc.list_workspaces.assert_called_once_with(
            project_id="PROJ-1", workspace_type="development",
            status="active", offset=0, limit=10,
        )

    # -------------------------------------------------------------------------
    # GET /api/workspaces/types
    # -------------------------------------------------------------------------

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_list_workspace_types(self, mock_svc, client):
        mock_svc.get_workspace_types_list.return_value = [_SAMPLE_WS_TYPE]
        resp = client.get("/api/workspaces/types")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["type_id"] == "development"
        assert data[0]["name"] == "Development"
        assert "mdi-code-braces" in data[0]["icon"]

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_list_workspace_types_empty(self, mock_svc, client):
        mock_svc.get_workspace_types_list.return_value = []
        resp = client.get("/api/workspaces/types")
        assert resp.status_code == 200
        assert resp.json() == []

    # -------------------------------------------------------------------------
    # GET /api/workspaces/{workspace_id} — get single
    # -------------------------------------------------------------------------

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_get_workspace(self, mock_svc, client):
        mock_svc.get_workspace.return_value = _SAMPLE_WS
        resp = client.get("/api/workspaces/WS-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workspace_id"] == "WS-1"
        assert data["project_id"] == "PROJ-1"
        assert "agent-1" in data["agent_ids"]
        mock_svc.get_workspace.assert_called_once_with("WS-1")

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_get_workspace_not_found(self, mock_svc, client):
        mock_svc.get_workspace.return_value = None
        resp = client.get("/api/workspaces/WS-NOPE")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # POST /api/workspaces — create
    # -------------------------------------------------------------------------

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_create_workspace(self, mock_svc, client):
        mock_svc.create_workspace.return_value = _SAMPLE_WS
        resp = client.post("/api/workspaces", json={
            "name": "Dev Workspace",
            "workspace_type": "development",
            "project_id": "PROJ-1",
            "description": "Primary dev workspace",
            "agent_ids": ["agent-1", "agent-2"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["workspace_id"] == "WS-1"
        assert data["name"] == "Dev Workspace"
        mock_svc.create_workspace.assert_called_once_with(
            name="Dev Workspace",
            workspace_type="development",
            project_id="PROJ-1",
            description="Primary dev workspace",
            agent_ids=["agent-1", "agent-2"],
            source="rest-api",
        )

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_create_workspace_minimal(self, mock_svc, client):
        minimal_ws = {
            "workspace_id": "WS-MIN", "name": "Minimal",
            "workspace_type": "generic", "project_id": None,
            "description": None, "status": "active", "created_at": None,
            "agent_ids": [], "default_rules": [], "capabilities": [],
            "icon": "mdi-folder", "color": "#64748b",
        }
        mock_svc.create_workspace.return_value = minimal_ws
        resp = client.post("/api/workspaces", json={"name": "Minimal"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["workspace_type"] == "generic"
        assert data["agent_ids"] == []

    def test_create_workspace_missing_name(self, client):
        resp = client.post("/api/workspaces", json={})
        assert resp.status_code == 422

    # -------------------------------------------------------------------------
    # PUT /api/workspaces/{workspace_id} — update
    # -------------------------------------------------------------------------

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_update_workspace(self, mock_svc, client):
        updated = {**_SAMPLE_WS, "name": "Renamed Workspace"}
        mock_svc.update_workspace.return_value = updated
        resp = client.put("/api/workspaces/WS-1", json={
            "name": "Renamed Workspace",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Renamed Workspace"
        mock_svc.update_workspace.assert_called_once_with(
            workspace_id="WS-1",
            name="Renamed Workspace",
            description=None,
            status=None,
            agent_ids=None,
            source="rest-api",
        )

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_update_workspace_not_found(self, mock_svc, client):
        mock_svc.update_workspace.return_value = None
        resp = client.put("/api/workspaces/WS-NOPE", json={
            "name": "Ghost",
        })
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # DELETE /api/workspaces/{workspace_id}
    # -------------------------------------------------------------------------

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_delete_workspace(self, mock_svc, client):
        mock_svc.delete_workspace.return_value = True
        resp = client.delete("/api/workspaces/WS-1")
        # P3-14: HTTP 204 No Content (empty body per spec)
        assert resp.status_code == 204
        assert resp.content == b""
        mock_svc.delete_workspace.assert_called_once_with(
            "WS-1", source="rest-api",
        )

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_delete_workspace_not_found(self, mock_svc, client):
        mock_svc.delete_workspace.return_value = False
        resp = client.delete("/api/workspaces/WS-NOPE")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # POST /api/workspaces/{workspace_id}/agents — assign agent
    # -------------------------------------------------------------------------

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_assign_agent(self, mock_svc, client):
        ws_with_new_agent = {
            **_SAMPLE_WS,
            "agent_ids": ["agent-1", "agent-2", "agent-3"],
        }
        mock_svc.assign_agent_to_workspace.return_value = ws_with_new_agent
        resp = client.post("/api/workspaces/WS-1/agents", json={
            "agent_id": "agent-3",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "agent-3" in data["agent_ids"]
        mock_svc.assign_agent_to_workspace.assert_called_once_with(
            "WS-1", "agent-3", source="rest-api",
        )

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_assign_agent_workspace_not_found(self, mock_svc, client):
        mock_svc.assign_agent_to_workspace.return_value = None
        resp = client.post("/api/workspaces/WS-NOPE/agents", json={
            "agent_id": "agent-1",
        })
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_assign_agent_missing_body(self, client):
        resp = client.post("/api/workspaces/WS-1/agents", json={})
        assert resp.status_code == 422

    # -------------------------------------------------------------------------
    # DELETE /api/workspaces/{workspace_id}/agents/{agent_id} — remove agent
    # -------------------------------------------------------------------------

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_remove_agent(self, mock_svc, client):
        ws_without_agent = {
            **_SAMPLE_WS,
            "agent_ids": ["agent-2"],
        }
        mock_svc.remove_agent_from_workspace.return_value = ws_without_agent
        resp = client.delete("/api/workspaces/WS-1/agents/agent-1")
        assert resp.status_code == 200
        data = resp.json()
        assert "agent-1" not in data["agent_ids"]
        assert "agent-2" in data["agent_ids"]
        mock_svc.remove_agent_from_workspace.assert_called_once_with(
            "WS-1", "agent-1", source="rest-api",
        )

    @patch("governance.routes.workspaces.crud.ws_service")
    def test_remove_agent_workspace_not_found(self, mock_svc, client):
        mock_svc.remove_agent_from_workspace.return_value = None
        resp = client.delete("/api/workspaces/WS-NOPE/agents/agent-1")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()
