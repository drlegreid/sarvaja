"""
Tests for session tool calls and thoughts API endpoints.

Per B.3: Load session tool calls + thoughts in detail view.
Verifies:
- GET /sessions/{id}/tools endpoint exists (detail.py)
- GET /sessions/{id}/thoughts endpoint exists (detail.py)
- Session controller loads tool calls on select
- Session controller loads thoughts on select

Updated: 2026-02-12 — endpoints moved from relations.py to detail.py
"""
import pytest
from unittest.mock import patch, MagicMock


_DETAIL = "governance.routes.sessions.detail"


class TestToolCallsEndpoint:
    """Tests for GET /sessions/{id}/tools (now in detail.py)."""

    def test_endpoint_exists(self):
        """Tools endpoint should exist in detail.py router."""
        from governance.routes.sessions.detail import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/tools" in paths

    def test_returns_tool_calls_list(self):
        """Endpoint should return tool calls as a list."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from governance.routes.sessions.detail import router
        app = FastAPI()
        app.include_router(router, prefix="/api")
        client = TestClient(app)

        mock_result = {
            "session_id": "S-1",
            "zoom": 2,
            "tool_calls": [
                {"name": "health_check", "is_mcp": True, "input_summary": "{}"}
            ],
            "tool_calls_total": 1,
        }
        with patch(f"{_DETAIL}.get_session_detail", return_value=mock_result):
            response = client.get("/api/sessions/S-1/tools")
            assert response.status_code == 200
            data = response.json()
            assert "tool_calls" in data
            assert data["total"] == 1


class TestThoughtsEndpoint:
    """Tests for GET /sessions/{id}/thoughts (now in detail.py)."""

    def test_endpoint_exists(self):
        """Thoughts endpoint should exist in detail.py router."""
        from governance.routes.sessions.detail import router
        paths = [route.path for route in router.routes]
        assert "/sessions/{session_id}/thoughts" in paths

    def test_returns_thinking_blocks_list(self):
        """Endpoint should return thinking blocks as a list."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from governance.routes.sessions.detail import router
        app = FastAPI()
        app.include_router(router, prefix="/api")
        client = TestClient(app)

        mock_result = {
            "session_id": "S-1",
            "zoom": 3,
            "thinking_blocks": [
                {"content": "Analyzing...", "chars": 120}
            ],
            "thinking_blocks_total": 1,
        }
        with patch(f"{_DETAIL}.get_session_detail", return_value=mock_result):
            response = client.get("/api/sessions/S-1/thoughts")
            assert response.status_code == 200
            data = response.json()
            assert "thinking_blocks" in data
            assert data["total"] == 1


class TestToolCallsFallbackToSessionsStore:
    """Tests for fallback: detail.py's get_session_detail uses _sessions_store
    when JSONL not available for chat-bridge sessions."""

    def test_fallback_uses_sessions_store(self):
        """When no JSONL exists, get_session_detail falls back to _sessions_store."""
        from governance.services.cc_session_ingestion import get_session_detail

        session = {"session_id": "S-CHAT", "status": "COMPLETED"}
        store_data = {
            "S-CHAT": {
                "tool_calls": [
                    {"tool_name": "/status", "arguments": {}, "timestamp": "2026-02-12T10:00:00"},
                ],
                "thoughts": [],
            }
        }
        with patch("governance.services.cc_session_ingestion.session_service") as mock_svc, \
             patch("governance.services.cc_session_ingestion._sessions_store", store_data), \
             patch("governance.services.cc_session_ingestion._find_jsonl_for_session", return_value=None):
            mock_svc.get_session.return_value = session
            result = get_session_detail("S-CHAT", zoom=2)

        assert result is not None
        assert result["tool_calls_total"] == 1

    def test_fallback_when_no_store_data(self):
        """When no JSONL and no _sessions_store data, returns empty tool calls."""
        from governance.services.cc_session_ingestion import get_session_detail

        session = {"session_id": "S-EMPTY", "status": "COMPLETED"}
        with patch("governance.services.cc_session_ingestion.session_service") as mock_svc, \
             patch("governance.services.cc_session_ingestion._sessions_store", {}), \
             patch("governance.services.cc_session_ingestion._find_jsonl_for_session", return_value=None):
            mock_svc.get_session.return_value = session
            result = get_session_detail("S-EMPTY", zoom=2)

        assert result is not None
        assert result["tool_calls_total"] == 0


class TestThoughtsFallbackToSessionsStore:
    """Tests for fallback: thinking blocks from _sessions_store."""

    def test_fallback_uses_sessions_store_thoughts(self):
        """When no JSONL, get_session_detail returns thoughts from _sessions_store."""
        from governance.services.cc_session_ingestion import get_session_detail

        session = {"session_id": "S-TH", "status": "COMPLETED"}
        store_data = {
            "S-TH": {
                "tool_calls": [],
                "thoughts": [
                    {"thought": "Analyzing rules", "timestamp": "2026-02-12T10:00:00"},
                ],
            }
        }
        with patch("governance.services.cc_session_ingestion.session_service") as mock_svc, \
             patch("governance.services.cc_session_ingestion._sessions_store", store_data), \
             patch("governance.services.cc_session_ingestion._find_jsonl_for_session", return_value=None):
            mock_svc.get_session.return_value = session
            result = get_session_detail("S-TH", zoom=3)

        assert result is not None
        assert result["thinking_blocks_total"] == 1

    def test_fallback_empty_thoughts(self):
        """When no JSONL and no thoughts in store, returns empty."""
        from governance.services.cc_session_ingestion import get_session_detail

        session = {"session_id": "S-NO-TH", "status": "COMPLETED"}
        with patch("governance.services.cc_session_ingestion.session_service") as mock_svc, \
             patch("governance.services.cc_session_ingestion._sessions_store", {}), \
             patch("governance.services.cc_session_ingestion._find_jsonl_for_session", return_value=None):
            mock_svc.get_session.return_value = session
            result = get_session_detail("S-NO-TH", zoom=3)

        assert result is not None
        assert result.get("thinking_blocks_total", 0) == 0


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
