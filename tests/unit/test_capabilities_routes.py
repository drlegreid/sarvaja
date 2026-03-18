"""
Route tests for Capability API endpoints.

Tests for governance/routes/capabilities.py — Rule-to-Agent binding CRUD.
"""

import pytest
from unittest.mock import patch


class TestCapabilitiesRoutes:
    """Tests for capability CRUD API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    # -------------------------------------------------------------------------
    # GET /api/capabilities — list
    # -------------------------------------------------------------------------

    @patch("governance.routes.capabilities.cap_service")
    def test_list_capabilities_empty(self, mock_svc, client):
        mock_svc.list_capabilities.return_value = []
        resp = client.get("/api/capabilities")
        assert resp.status_code == 200
        assert resp.json() == []

    @patch("governance.routes.capabilities.cap_service")
    def test_list_capabilities_with_items(self, mock_svc, client):
        mock_svc.list_capabilities.return_value = [
            {"agent_id": "agent-1", "rule_id": "RULE-A",
             "category": "coding", "status": "active", "created_at": None},
            {"agent_id": "agent-2", "rule_id": "RULE-B",
             "category": "testing", "status": "active", "created_at": None},
        ]
        resp = client.get("/api/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["agent_id"] == "agent-1"
        assert data[1]["rule_id"] == "RULE-B"

    @patch("governance.routes.capabilities.cap_service")
    def test_list_capabilities_with_filters(self, mock_svc, client):
        mock_svc.list_capabilities.return_value = [
            {"agent_id": "agent-1", "rule_id": "RULE-A",
             "category": "coding", "status": "active", "created_at": None},
        ]
        resp = client.get(
            "/api/capabilities?agent_id=agent-1&category=coding&status=active"
        )
        assert resp.status_code == 200
        mock_svc.list_capabilities.assert_called_once_with(
            agent_id="agent-1", rule_id=None,
            category="coding", status="active",
        )

    # -------------------------------------------------------------------------
    # GET /api/capabilities/summary
    # -------------------------------------------------------------------------

    @patch("governance.routes.capabilities.cap_service")
    def test_get_capability_summary(self, mock_svc, client):
        mock_svc.get_capability_summary.return_value = {
            "total_bindings": 10,
            "agents_with_rules": 3,
            "rules_applied": 5,
            "by_category": {"coding": 4, "testing": 6},
            "active": 8,
            "suspended": 2,
        }
        resp = client.get("/api/capabilities/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_bindings"] == 10
        assert data["active"] == 8
        assert data["by_category"]["coding"] == 4

    # -------------------------------------------------------------------------
    # GET /api/agents/{agent_id}/capabilities
    # -------------------------------------------------------------------------

    @patch("governance.routes.capabilities.cap_service")
    def test_get_agent_capabilities(self, mock_svc, client):
        mock_svc.get_capabilities_for_agent.return_value = [
            {"agent_id": "agent-1", "rule_id": "RULE-X",
             "category": "governance", "status": "active", "created_at": None},
        ]
        resp = client.get("/api/agents/agent-1/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["rule_id"] == "RULE-X"
        mock_svc.get_capabilities_for_agent.assert_called_once_with("agent-1")

    @patch("governance.routes.capabilities.cap_service")
    def test_get_agent_capabilities_empty(self, mock_svc, client):
        mock_svc.get_capabilities_for_agent.return_value = []
        resp = client.get("/api/agents/unknown-agent/capabilities")
        assert resp.status_code == 200
        assert resp.json() == []

    # -------------------------------------------------------------------------
    # GET /api/rules/{rule_id}/agents
    # -------------------------------------------------------------------------

    @patch("governance.routes.capabilities.cap_service")
    def test_get_rule_agents(self, mock_svc, client):
        mock_svc.get_agents_for_rule.return_value = [
            {"agent_id": "agent-1", "rule_id": "RULE-A",
             "category": "coding", "status": "active", "created_at": None},
            {"agent_id": "agent-2", "rule_id": "RULE-A",
             "category": "testing", "status": "suspended", "created_at": None},
        ]
        resp = client.get("/api/rules/RULE-A/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[1]["status"] == "suspended"
        mock_svc.get_agents_for_rule.assert_called_once_with("RULE-A")

    @patch("governance.routes.capabilities.cap_service")
    def test_get_rule_agents_empty(self, mock_svc, client):
        mock_svc.get_agents_for_rule.return_value = []
        resp = client.get("/api/rules/RULE-NONE/agents")
        assert resp.status_code == 200
        assert resp.json() == []

    # -------------------------------------------------------------------------
    # POST /api/capabilities — bind
    # -------------------------------------------------------------------------

    @patch("governance.routes.capabilities.cap_service")
    def test_bind_rule_to_agent(self, mock_svc, client):
        mock_svc.bind_rule_to_agent.return_value = {
            "agent_id": "agent-1", "rule_id": "RULE-NEW",
            "category": "coding", "status": "active",
            "created_at": "2026-02-21T10:00:00",
        }
        resp = client.post("/api/capabilities", json={
            "agent_id": "agent-1",
            "rule_id": "RULE-NEW",
            "category": "coding",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["agent_id"] == "agent-1"
        assert data["rule_id"] == "RULE-NEW"
        assert data["status"] == "active"
        mock_svc.bind_rule_to_agent.assert_called_once_with(
            agent_id="agent-1", rule_id="RULE-NEW",
            category="coding", source="rest-api",
        )

    @patch("governance.routes.capabilities.cap_service")
    def test_bind_rule_default_category(self, mock_svc, client):
        mock_svc.bind_rule_to_agent.return_value = {
            "agent_id": "agent-1", "rule_id": "RULE-X",
            "category": "general", "status": "active", "created_at": None,
        }
        resp = client.post("/api/capabilities", json={
            "agent_id": "agent-1",
            "rule_id": "RULE-X",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "general"

    def test_bind_rule_missing_fields(self, client):
        resp = client.post("/api/capabilities", json={})
        assert resp.status_code == 422

    # -------------------------------------------------------------------------
    # DELETE /api/capabilities/{agent_id}/{rule_id} — unbind
    # -------------------------------------------------------------------------

    @patch("governance.routes.capabilities.cap_service")
    def test_unbind_rule_success(self, mock_svc, client):
        mock_svc.unbind_rule_from_agent.return_value = True
        resp = client.delete("/api/capabilities/agent-1/RULE-A")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "deleted"
        assert data["agent_id"] == "agent-1"
        assert data["rule_id"] == "RULE-A"
        mock_svc.unbind_rule_from_agent.assert_called_once_with(
            "agent-1", "RULE-A", source="rest-api",
        )

    @patch("governance.routes.capabilities.cap_service")
    def test_unbind_rule_not_found(self, mock_svc, client):
        mock_svc.unbind_rule_from_agent.return_value = False
        resp = client.delete("/api/capabilities/agent-x/RULE-NOPE")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # PUT /api/capabilities/{agent_id}/{rule_id}/status — update status
    # -------------------------------------------------------------------------

    @patch("governance.routes.capabilities.cap_service")
    def test_update_capability_status_success(self, mock_svc, client):
        mock_svc.update_capability_status.return_value = {
            "agent_id": "agent-1", "rule_id": "RULE-A",
            "category": "coding", "status": "suspended", "created_at": None,
        }
        resp = client.put(
            "/api/capabilities/agent-1/RULE-A/status",
            json={"status": "suspended"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "suspended"
        mock_svc.update_capability_status.assert_called_once_with(
            "agent-1", "RULE-A", "suspended", source="rest-api",
        )

    @patch("governance.routes.capabilities.cap_service")
    def test_update_capability_status_not_found(self, mock_svc, client):
        mock_svc.update_capability_status.return_value = None
        resp = client.put(
            "/api/capabilities/agent-x/RULE-NOPE/status",
            json={"status": "active"},
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_update_capability_status_invalid_value(self, client):
        resp = client.put(
            "/api/capabilities/agent-1/RULE-A/status",
            json={"status": "invalid-state"},
        )
        assert resp.status_code == 422
