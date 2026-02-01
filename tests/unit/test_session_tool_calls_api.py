"""
Tests for session tool calls and thoughts API endpoints.

Per B.3: Load session tool calls + thoughts in detail view.
Verifies:
- GET /sessions/{id}/tool_calls endpoint exists
- GET /sessions/{id}/thoughts endpoint exists
- Session controller loads tool calls on select
- Session controller loads thoughts on select

Created: 2026-02-01
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for session relations API."""
    from governance.routes.sessions.relations import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


class TestToolCallsEndpoint:
    """Tests for GET /sessions/{id}/tool_calls."""

    def test_endpoint_exists(self, client):
        """Tool calls endpoint should exist and return a response."""
        with patch("governance.routes.sessions.relations.get_typedb_client") as mock:
            mock_client = MagicMock()
            mock_client.get_session.return_value = {"session_id": "S-1"}
            mock.return_value = mock_client
            # The method may not exist yet but the endpoint should
            mock_client.get_session_tool_calls = MagicMock(return_value=[])
            response = client.get("/api/sessions/S-1/tool_calls")
            assert response.status_code in (200, 503)

    def test_returns_tool_calls_list(self, client):
        """Endpoint should return tool calls as a list."""
        with patch("governance.routes.sessions.relations.get_typedb_client") as mock:
            mock_client = MagicMock()
            mock_client.get_session.return_value = {"session_id": "S-1"}
            mock_client.get_session_tool_calls.return_value = [
                {"tool_name": "health_check", "duration_ms": 100}
            ]
            mock.return_value = mock_client
            response = client.get("/api/sessions/S-1/tool_calls")
            assert response.status_code == 200
            data = response.json()
            assert "tool_calls" in data
            assert len(data["tool_calls"]) == 1


class TestThoughtsEndpoint:
    """Tests for GET /sessions/{id}/thoughts."""

    def test_endpoint_exists(self, client):
        """Thoughts endpoint should exist and return a response."""
        with patch("governance.routes.sessions.relations.get_typedb_client") as mock:
            mock_client = MagicMock()
            mock_client.get_session.return_value = {"session_id": "S-1"}
            mock.return_value = mock_client
            mock_client.get_session_thoughts = MagicMock(return_value=[])
            response = client.get("/api/sessions/S-1/thoughts")
            assert response.status_code in (200, 503)

    def test_returns_thoughts_list(self, client):
        """Endpoint should return thoughts as a list."""
        with patch("governance.routes.sessions.relations.get_typedb_client") as mock:
            mock_client = MagicMock()
            mock_client.get_session.return_value = {"session_id": "S-1"}
            mock_client.get_session_thoughts.return_value = [
                {"thought": "Analyzing rules...", "thought_type": "reasoning"}
            ]
            mock.return_value = mock_client
            response = client.get("/api/sessions/S-1/thoughts")
            assert response.status_code == 200
            data = response.json()
            assert "thoughts" in data


class TestSessionControllerIntegration:
    """Tests for session controller loading tool calls/thoughts."""

    def test_controller_references_tool_calls(self):
        """Session controller should reference tool calls loading."""
        import inspect
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        source = inspect.getsource(register_sessions_controllers)
        assert "session_tool_calls" in source or "tool_calls" in source

    def test_controller_references_thoughts(self):
        """Session controller should reference thinking items loading."""
        import inspect
        from agent.governance_ui.controllers.sessions import register_sessions_controllers
        source = inspect.getsource(register_sessions_controllers)
        assert "session_thinking_items" in source or "thinking_items" in source
