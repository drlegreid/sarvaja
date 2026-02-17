"""
Unit tests for Chat Routes Endpoints.

Per DOC-SIZE-01-v1: Tests for routes/chat/endpoints.py module.
Tests: send_chat_message, get_chat_session, list_chat_sessions,
       delete_chat_session.
"""

from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

import pytest
from fastapi import HTTPException

_P = "governance.routes.chat.endpoints"


@pytest.fixture(autouse=True)
def _reset_stores():
    with patch(f"{_P}._chat_sessions", {}) as sessions, \
         patch(f"{_P}._chat_gov_sessions", {}) as gov:
        yield sessions, gov


# ── send_chat_message ───────────────────────────────────────────


class TestSendChatMessage:
    @pytest.mark.asyncio
    async def test_new_session(self, _reset_stores):
        from governance.routes.chat.endpoints import send_chat_message
        from governance.models import ChatMessageRequest
        sessions, gov = _reset_stores
        req = ChatMessageRequest(content="/help", agent_id="AGENT-001")
        with patch(f"{_P}.generate_chat_session_id", return_value="CHAT-1"), \
             patch(f"{_P}.preload_session_context") as mock_ctx, \
             patch(f"{_P}.process_chat_command", return_value="Help response"), \
             patch(f"{_P}.start_chat_session", return_value=MagicMock()), \
             patch(f"{_P}.record_chat_tool_call"), \
             patch(f"{_P}.record_chat_thought"):
            mock_ctx.return_value = MagicMock(to_dict=lambda: {})
            result = await send_chat_message(req)
        assert result.role == "agent"
        assert result.content == "Help response"

    @pytest.mark.asyncio
    async def test_existing_session(self, _reset_stores):
        from governance.routes.chat.endpoints import send_chat_message
        from governance.models import ChatMessageRequest
        sessions, gov = _reset_stores
        sessions["CHAT-1"] = {
            "session_id": "CHAT-1", "messages": [],
            "active_task_id": None, "selected_agent_id": "AGENT-001",
        }
        req = ChatMessageRequest(
            content="hello", session_id="CHAT-1", agent_id="AGENT-001",
        )
        with patch(f"{_P}.process_chat_command", return_value="Hi there"), \
             patch(f"{_P}.record_chat_tool_call"), \
             patch(f"{_P}.record_chat_thought"):
            result = await send_chat_message(req)
        assert result.content == "Hi there"
        assert len(sessions["CHAT-1"]["messages"]) == 2  # user + agent

    @pytest.mark.asyncio
    async def test_no_agent_id_defaults(self, _reset_stores):
        from governance.routes.chat.endpoints import send_chat_message
        from governance.models import ChatMessageRequest
        sessions, _ = _reset_stores
        req = ChatMessageRequest(content="test")
        with patch(f"{_P}.generate_chat_session_id", return_value="CHAT-2"), \
             patch(f"{_P}.preload_session_context") as mock_ctx, \
             patch(f"{_P}.get_available_agents_for_chat", return_value=[]), \
             patch(f"{_P}.process_chat_command", return_value="response"), \
             patch(f"{_P}.start_chat_session", return_value=MagicMock()), \
             patch(f"{_P}.record_chat_tool_call"), \
             patch(f"{_P}.record_chat_thought"):
            mock_ctx.return_value = MagicMock(to_dict=lambda: {})
            result = await send_chat_message(req)
        assert result.agent_id == "AGENT-001"

    @pytest.mark.asyncio
    async def test_delegation_handling(self, _reset_stores):
        from governance.routes.chat.endpoints import send_chat_message
        from governance.models import ChatMessageRequest
        # BUG-300-DEL-001: Must use explicit /delegate command for sentinel to be honored
        req = ChatMessageRequest(content="/delegate do stuff", agent_id="AGENT-001")
        with patch(f"{_P}.generate_chat_session_id", return_value="CHAT-3"), \
             patch(f"{_P}.preload_session_context") as mock_ctx, \
             patch(f"{_P}.process_chat_command", return_value="__DELEGATE__:do stuff"), \
             patch(f"{_P}.start_chat_session", return_value=MagicMock()), \
             patch(f"{_P}.record_chat_tool_call"), \
             patch(f"{_P}._delegate_task_async", new_callable=AsyncMock, return_value="Delegated!"):
            mock_ctx.return_value = MagicMock(to_dict=lambda: {})
            result = await send_chat_message(req)
        assert result.content == "Delegated!"

    @pytest.mark.asyncio
    async def test_context_preload_failure(self, _reset_stores):
        from governance.routes.chat.endpoints import send_chat_message
        from governance.models import ChatMessageRequest
        req = ChatMessageRequest(content="test", agent_id="AGENT-001")
        with patch(f"{_P}.generate_chat_session_id", return_value="CHAT-4"), \
             patch(f"{_P}.preload_session_context", side_effect=Exception("fail")), \
             patch(f"{_P}.process_chat_command", return_value="ok"), \
             patch(f"{_P}.start_chat_session", return_value=MagicMock()), \
             patch(f"{_P}.record_chat_tool_call"), \
             patch(f"{_P}.record_chat_thought"):
            result = await send_chat_message(req)
        assert result.content == "ok"


# ── get_chat_session ────────────────────────────────────────────


class TestGetChatSession:
    @pytest.mark.asyncio
    async def test_found(self, _reset_stores):
        from governance.routes.chat.endpoints import get_chat_session
        sessions, _ = _reset_stores
        sessions["CHAT-1"] = {
            "session_id": "CHAT-1",
            "messages": [{"id": "M-1", "role": "user", "content": "hi",
                          "timestamp": "2026-01-01", "status": "complete"}],
            "active_task_id": None, "selected_agent_id": "A-1",
        }
        result = await get_chat_session("CHAT-1")
        assert result.session_id == "CHAT-1"
        assert len(result.messages) == 1

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.chat.endpoints import get_chat_session
        with pytest.raises(HTTPException) as exc:
            await get_chat_session("CHAT-MISSING")
        assert exc.value.status_code == 404


# ── list_chat_sessions ──────────────────────────────────────────


class TestListChatSessions:
    @pytest.mark.asyncio
    async def test_empty(self):
        from governance.routes.chat.endpoints import list_chat_sessions
        result = await list_chat_sessions()
        assert result == []

    @pytest.mark.asyncio
    async def test_with_sessions(self, _reset_stores):
        from governance.routes.chat.endpoints import list_chat_sessions
        sessions, _ = _reset_stores
        sessions["C-1"] = {
            "session_id": "C-1", "messages": [{"a": 1}],
            "created_at": "2026-01-01", "selected_agent_id": "A-1",
        }
        sessions["C-2"] = {
            "session_id": "C-2", "messages": [],
            "created_at": "2026-01-02", "selected_agent_id": "A-2",
        }
        result = await list_chat_sessions()
        assert len(result) == 2
        ids = {s["session_id"] for s in result}
        assert ids == {"C-1", "C-2"}


# ── delete_chat_session ────────────────────────────────────────


class TestDeleteChatSession:
    @pytest.mark.asyncio
    async def test_success(self, _reset_stores):
        from governance.routes.chat.endpoints import delete_chat_session
        sessions, gov = _reset_stores
        sessions["C-1"] = {"session_id": "C-1", "messages": []}
        with patch(f"{_P}.end_chat_session"):
            result = await delete_chat_session("C-1")
        assert result["status"] == "deleted"
        assert "C-1" not in sessions

    @pytest.mark.asyncio
    async def test_with_gov_session(self, _reset_stores):
        from governance.routes.chat.endpoints import delete_chat_session
        sessions, gov = _reset_stores
        sessions["C-1"] = {"session_id": "C-1", "messages": [{"a": 1}]}
        gov["C-1"] = MagicMock()
        with patch(f"{_P}.end_chat_session") as mock_end:
            await delete_chat_session("C-1")
        mock_end.assert_called_once()

    @pytest.mark.asyncio
    async def test_not_found(self):
        from governance.routes.chat.endpoints import delete_chat_session
        with pytest.raises(HTTPException) as exc:
            await delete_chat_session("C-MISSING")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_gov_session_end_failure(self, _reset_stores):
        from governance.routes.chat.endpoints import delete_chat_session
        sessions, gov = _reset_stores
        sessions["C-1"] = {"session_id": "C-1", "messages": []}
        gov["C-1"] = MagicMock()
        with patch(f"{_P}.end_chat_session", side_effect=Exception("fail")):
            result = await delete_chat_session("C-1")
        assert result["status"] == "deleted"
