"""
Chat Integration Library for Robot Framework
Tests for chat session management and integration.
Migrated from tests/test_chat.py
Per: RF-005 Robot Framework Migration
"""
from robot.api.deco import keyword


class ChatIntegrationLibrary:
    """Robot Framework keywords for chat integration tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Chat Session Management Tests
    # =========================================================================

    @keyword("Generate Session Id")
    def generate_session_id(self):
        """Test generating chat session ID."""
        try:
            from governance.api import _generate_chat_session_id

            session_id = _generate_chat_session_id()

            return {
                "starts_with_chat": session_id.startswith('CHAT-'),
                "length_valid": len(session_id) > 5
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Unique Session Ids")
    def generate_unique_session_ids(self):
        """Test that session IDs are unique."""
        try:
            from governance.api import _generate_chat_session_id

            ids = [_generate_chat_session_id() for _ in range(10)]

            return {"all_unique": len(set(ids)) == 10}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Chat Integration Tests
    # =========================================================================

    @keyword("Send Message Creates Session")
    def send_message_creates_session(self):
        """Test that sending message creates new session."""
        try:
            from fastapi.testclient import TestClient
            from governance.api import app

            client = TestClient(app)
            response = client.post("/api/chat/send", json={
                "content": "/help",
            })

            data = response.json()
            return {
                "status_200": response.status_code == 200,
                "role_agent": data.get('role') == 'agent',
                "has_commands": 'Available Commands' in data.get('content', '')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Send Message With Agent")
    def send_message_with_agent(self):
        """Test sending message to specific agent."""
        try:
            from fastapi.testclient import TestClient
            from governance.api import app

            client = TestClient(app)
            response = client.post("/api/chat/send", json={
                "content": "/status",
                "agent_id": "AGENT-001",
            })

            data = response.json()
            return {
                "status_200": response.status_code == 200,
                "has_agent_id": data.get('agent_id') is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Chat Sessions")
    def list_chat_sessions(self):
        """Test listing chat sessions."""
        try:
            from fastapi.testclient import TestClient
            from governance.api import app

            client = TestClient(app)
            # Create a session first
            client.post("/api/chat/send", json={"content": "test"})

            response = client.get("/api/chat/sessions")
            sessions = response.json()

            return {
                "status_200": response.status_code == 200,
                "is_list": isinstance(sessions, list)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Nonexistent Session")
    def get_nonexistent_session(self):
        """Test getting nonexistent session returns 404."""
        try:
            from fastapi.testclient import TestClient
            from governance.api import app

            client = TestClient(app)
            response = client.get("/api/chat/sessions/NONEXISTENT")

            return {"status_404": response.status_code == 404}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
