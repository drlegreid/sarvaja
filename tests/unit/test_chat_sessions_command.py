"""
Tests for /sessions chat command.

Per A.1: Add /sessions command to chat.
Verifies:
- /sessions command returns formatted session list via service layer
- Falls back to in-memory store when service layer fails
- Handles empty session store
- Shows session details (agent_id, status, start_time)
- /help includes /sessions in command list

Created: 2026-02-01
Updated: 2026-02-01 - Service layer integration (TypeDB + fallback)
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSessionsCommand:
    """Tests for /sessions chat command."""

    def test_sessions_command_via_service_layer(self):
        """When service layer returns sessions, display them."""
        mock_result = {
            "items": [
                {
                    "session_id": "SESSION-2026-02-01-TEST",
                    "agent_id": "agent-curator",
                    "status": "ACTIVE",
                    "start_time": "2026-02-01T10:00:00",
                },
                {
                    "session_id": "SESSION-2026-01-31-REVIEW",
                    "agent_id": "agent-orchestrator",
                    "status": "COMPLETED",
                    "start_time": "2026-01-31T14:00:00",
                },
            ],
            "pagination": {"total": 2},
        }
        with patch("governance.routes.chat.commands.list_sessions", return_value=mock_result):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "SESSION-2026-02-01-TEST" in result
        assert "SESSION-2026-01-31-REVIEW" in result
        assert "2 total" in result
        assert "1 active" in result

    def test_sessions_command_fallback_to_store(self):
        """When service layer fails, fall back to in-memory store."""
        mock_sessions = {
            "s1": {
                "session_id": "SESSION-FALLBACK-1",
                "agent_id": "agent-curator",
                "status": "ACTIVE",
                "start_time": "2026-02-01T10:00:00",
            },
        }
        with patch(
            "governance.routes.chat.commands.list_sessions",
            side_effect=Exception("TypeDB down"),
        ), patch("governance.routes.chat.commands._sessions_store", mock_sessions):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "SESSION-FALLBACK-1" in result

    def test_sessions_command_empty(self):
        """When no sessions exist, return helpful message."""
        mock_result = {"items": [], "pagination": {"total": 0}}
        with patch("governance.routes.chat.commands.list_sessions", return_value=mock_result):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "no" in result.lower() or "No" in result

    def test_sessions_command_shows_agent_id(self):
        """Session list includes agent_id."""
        mock_result = {
            "items": [
                {
                    "session_id": "SESSION-TEST-1",
                    "agent_id": "agent-curator",
                    "status": "ACTIVE",
                    "start_time": "2026-02-01T10:00:00",
                },
            ],
            "pagination": {"total": 1},
        }
        with patch("governance.routes.chat.commands.list_sessions", return_value=mock_result):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "agent-curator" in result

    def test_sessions_command_shows_evidence_count(self):
        """Session list includes evidence file count when present."""
        mock_result = {
            "items": [
                {
                    "session_id": "SESSION-TEST-1",
                    "agent_id": "agent-curator",
                    "status": "COMPLETED",
                    "start_time": "2026-02-01T10:00:00",
                    "evidence_files": ["ev1.md", "ev2.md"],
                },
            ],
            "pagination": {"total": 1},
        }
        with patch("governance.routes.chat.commands.list_sessions", return_value=mock_result):
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("/sessions", "test-agent")

        assert "evidence" in result.lower()
        assert "2 files" in result

    def test_help_includes_sessions_command(self):
        """Help output includes /sessions command."""
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/help", "test-agent")
        assert "/sessions" in result
