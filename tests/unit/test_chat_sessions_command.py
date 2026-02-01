"""
Tests for /sessions chat command.

Per A.1: Add /sessions command to chat.
Verifies:
- /sessions command returns formatted session list
- Handles empty session store
- Shows session details (agent_id, status, start_time)
- /help includes /sessions in command list

Created: 2026-02-01
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSessionsCommand:
    """Tests for /sessions chat command."""

    def test_sessions_command_returns_sessions_list(self):
        """When sessions exist, /sessions returns formatted list."""
        mock_sessions = {
            "sess-1": {
                "session_id": "SESSION-2026-02-01-TEST",
                "agent_id": "agent-curator",
                "status": "ACTIVE",
                "start_time": "2026-02-01T10:00:00",
                "intent": "Testing governance rules",
            },
            "sess-2": {
                "session_id": "SESSION-2026-01-31-REVIEW",
                "agent_id": "agent-orchestrator",
                "status": "ENDED",
                "start_time": "2026-01-31T14:00:00",
                "intent": "Code review session",
            },
        }
        with patch("governance.routes.chat.commands._sessions_store", mock_sessions):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "SESSION-2026-02-01-TEST" in result
        assert "SESSION-2026-01-31-REVIEW" in result
        assert "2 total" in result or "2)" in result

    def test_sessions_command_empty_store(self):
        """When no sessions exist, return helpful message."""
        with patch("governance.routes.chat.commands._sessions_store", {}):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "no" in result.lower() or "No" in result

    def test_sessions_command_shows_agent_id(self):
        """Session list includes agent_id for linking."""
        mock_sessions = {
            "s1": {
                "session_id": "SESSION-TEST-1",
                "agent_id": "agent-curator",
                "status": "ACTIVE",
                "start_time": "2026-02-01T10:00:00",
            },
        }
        with patch("governance.routes.chat.commands._sessions_store", mock_sessions):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "agent-curator" in result

    def test_sessions_command_shows_status(self):
        """Session list includes status."""
        mock_sessions = {
            "s1": {
                "session_id": "SESSION-TEST-1",
                "agent_id": "agent-curator",
                "status": "ACTIVE",
                "start_time": "2026-02-01T10:00:00",
            },
        }
        with patch("governance.routes.chat.commands._sessions_store", mock_sessions):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "ACTIVE" in result

    def test_help_includes_sessions_command(self):
        """Help output includes /sessions command."""
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/help", "test-agent")
        assert "/sessions" in result
