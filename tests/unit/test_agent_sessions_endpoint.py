"""Tests for GET /agents/{agent_id}/sessions endpoint.

Per EPIC-A.4: Session-agent linking — verify agent-sessions API.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAgentSessionsEndpoint:
    """Tests for the agent sessions endpoint."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from governance.api import app
        return TestClient(app)

    @patch("governance.routes.agents.crud.agent_service")
    @patch("governance.routes.agents.crud.session_service")
    def test_get_agent_sessions_returns_sessions(self, mock_sess_svc, mock_agent_svc, client):
        """Agent with linked sessions returns them."""
        mock_agent_svc.get_agent.return_value = {"agent_id": "code-agent", "name": "Code Agent"}
        mock_sess_svc.list_sessions.return_value = {
            "items": [
                {"session_id": "S-001", "agent_id": "code-agent", "status": "COMPLETED"},
                {"session_id": "S-002", "agent_id": "code-agent", "status": "ACTIVE"},
            ],
            "total": 2,
            "offset": 0,
            "limit": 20,
            "has_more": False,
        }

        resp = client.get("/api/agents/code-agent/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "code-agent"
        assert len(data["sessions"]) == 2
        assert data["pagination"]["total"] == 2
        mock_sess_svc.list_sessions.assert_called_once_with(
            agent_id="code-agent", offset=0, limit=20,
        )

    @patch("governance.routes.agents.crud.agent_service")
    @patch("governance.routes.agents.crud.session_service")
    def test_get_agent_sessions_empty(self, mock_sess_svc, mock_agent_svc, client):
        """Agent with no sessions returns empty list."""
        mock_agent_svc.get_agent.return_value = {"agent_id": "test-agent"}
        mock_sess_svc.list_sessions.return_value = {
            "items": [],
            "total": 0,
            "offset": 0,
            "limit": 20,
            "has_more": False,
        }

        resp = client.get("/api/agents/test-agent/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sessions"] == []
        assert data["pagination"]["total"] == 0

    @patch("governance.routes.agents.crud.agent_service")
    def test_get_agent_sessions_agent_not_found(self, mock_agent_svc, client):
        """Unknown agent returns 404."""
        mock_agent_svc.get_agent.return_value = None

        resp = client.get("/api/agents/unknown-agent/sessions")
        assert resp.status_code == 404

    @patch("governance.routes.agents.crud.agent_service")
    @patch("governance.routes.agents.crud.session_service")
    def test_get_agent_sessions_pagination(self, mock_sess_svc, mock_agent_svc, client):
        """Pagination params are forwarded to service."""
        mock_agent_svc.get_agent.return_value = {"agent_id": "code-agent"}
        mock_sess_svc.list_sessions.return_value = {
            "items": [{"session_id": "S-003"}],
            "total": 15,
            "offset": 10,
            "limit": 5,
            "has_more": False,
        }

        resp = client.get("/api/agents/code-agent/sessions?offset=10&limit=5")
        assert resp.status_code == 200
        mock_sess_svc.list_sessions.assert_called_once_with(
            agent_id="code-agent", offset=10, limit=5,
        )
        data = resp.json()
        assert data["pagination"]["offset"] == 10
        assert data["pagination"]["limit"] == 5
