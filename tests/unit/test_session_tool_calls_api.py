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


class TestToolCallsFallbackToSessionsStore:
    """Tests for Lim 3 fix: fallback to _sessions_store when TypeDB has session
    but no get_session_tool_calls method."""

    def test_fallback_when_typedb_has_session_but_no_tool_call_method(self, client):
        """When TypeDB client lacks get_session_tool_calls, should fall back to _sessions_store."""
        from governance.stores import _sessions_store
        _sessions_store["S-FALLBACK"] = {
            "session_id": "S-FALLBACK",
            "status": "COMPLETED",
            "tool_calls": [
                {"tool_name": "/status", "result": "ok"},
                {"tool_name": "/tasks", "result": "3 tasks"},
            ],
        }
        try:
            with patch("governance.routes.sessions.relations.get_typedb_client") as mock:
                mock_client = MagicMock()
                mock_client.get_session.return_value = {"session_id": "S-FALLBACK"}
                # Simulate: client has NO get_session_tool_calls method
                del mock_client.get_session_tool_calls
                mock.return_value = mock_client
                response = client.get("/api/sessions/S-FALLBACK/tool_calls")
                assert response.status_code == 200
                data = response.json()
                assert data["tool_call_count"] == 2
                assert data["tool_calls"][0]["tool_name"] == "/status"
        finally:
            _sessions_store.pop("S-FALLBACK", None)

    def test_fallback_when_typedb_tool_calls_empty(self, client):
        """When TypeDB returns empty tool_calls, should fall back to _sessions_store."""
        from governance.stores import _sessions_store
        _sessions_store["S-EMPTY-TC"] = {
            "session_id": "S-EMPTY-TC",
            "status": "ACTIVE",
            "tool_calls": [{"tool_name": "/health", "result": "ok"}],
        }
        try:
            with patch("governance.routes.sessions.relations.get_typedb_client") as mock:
                mock_client = MagicMock()
                mock_client.get_session.return_value = {"session_id": "S-EMPTY-TC"}
                mock_client.get_session_tool_calls.return_value = []
                mock.return_value = mock_client
                response = client.get("/api/sessions/S-EMPTY-TC/tool_calls")
                assert response.status_code == 200
                data = response.json()
                assert data["tool_call_count"] == 1
                assert data["tool_calls"][0]["tool_name"] == "/health"
        finally:
            _sessions_store.pop("S-EMPTY-TC", None)


class TestThoughtsFallbackToSessionsStore:
    """Tests for Lim 3 fix: fallback to _sessions_store when TypeDB has session
    but no get_session_thoughts method."""

    def test_fallback_when_typedb_has_session_but_no_thoughts_method(self, client):
        """When TypeDB client lacks get_session_thoughts, should fall back to _sessions_store."""
        from governance.stores import _sessions_store
        _sessions_store["S-THOUGHTS-FB"] = {
            "session_id": "S-THOUGHTS-FB",
            "status": "COMPLETED",
            "thoughts": [
                {"thought": "Analyzing system health", "thought_type": "observation"},
            ],
        }
        try:
            with patch("governance.routes.sessions.relations.get_typedb_client") as mock:
                mock_client = MagicMock()
                mock_client.get_session.return_value = {"session_id": "S-THOUGHTS-FB"}
                del mock_client.get_session_thoughts
                mock.return_value = mock_client
                response = client.get("/api/sessions/S-THOUGHTS-FB/thoughts")
                assert response.status_code == 200
                data = response.json()
                assert data["thought_count"] == 1
                assert data["thoughts"][0]["thought_type"] == "observation"
        finally:
            _sessions_store.pop("S-THOUGHTS-FB", None)

    def test_fallback_when_typedb_thoughts_empty(self, client):
        """When TypeDB returns empty thoughts, should fall back to _sessions_store."""
        from governance.stores import _sessions_store
        _sessions_store["S-EMPTY-TH"] = {
            "session_id": "S-EMPTY-TH",
            "status": "ACTIVE",
            "thoughts": [{"thought": "Checking rules", "thought_type": "reasoning"}],
        }
        try:
            with patch("governance.routes.sessions.relations.get_typedb_client") as mock:
                mock_client = MagicMock()
                mock_client.get_session.return_value = {"session_id": "S-EMPTY-TH"}
                mock_client.get_session_thoughts.return_value = []
                mock.return_value = mock_client
                response = client.get("/api/sessions/S-EMPTY-TH/thoughts")
                assert response.status_code == 200
                data = response.json()
                assert data["thought_count"] == 1
                assert data["thoughts"][0]["thought"] == "Checking rules"
        finally:
            _sessions_store.pop("S-EMPTY-TH", None)


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
