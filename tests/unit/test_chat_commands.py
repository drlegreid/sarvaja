"""
Unit tests for Chat Command Processing.

Per DOC-SIZE-01-v1: Tests for routes/chat/commands.py module.
Tests: query_llm, process_chat_command.
"""

from unittest.mock import MagicMock, patch

import pytest

_P = "governance.routes.chat.commands"


@pytest.fixture(autouse=True)
def _patch_stores():
    with patch(f"{_P}._tasks_store", {
        "T-1": {"task_id": "T-1", "name": "Fix bug", "status": "pending",
                "description": "Fix a bug"},
        "T-2": {"task_id": "T-2", "name": "Add feature", "status": "IN_PROGRESS",
                "description": "Add new feature"},
    }), \
        patch(f"{_P}._agents_store", {
            "code-agent": {"agent_id": "code-agent", "name": "Code Agent",
                           "trust_score": 0.85},
        }), \
        patch(f"{_P}._sessions_store", {
            "S-1": {"session_id": "S-1", "status": "ACTIVE",
                    "start_time": "2026-01-01T10:00:00", "agent_id": "code-agent"},
        }):
        yield


@pytest.fixture(autouse=True)
def _patch_client():
    mock_client = MagicMock()
    mock_rule = MagicMock()
    mock_rule.id = "TEST-01-v1"
    mock_rule.name = "Test Rule"
    mock_rule.status = "ACTIVE"
    mock_rule.directive = "Do something"
    mock_client.get_all_rules.return_value = [mock_rule]
    with patch(f"{_P}.get_client", return_value=mock_client):
        yield mock_client


# ── query_llm ────────────────────────────────────────────────────


class TestQueryLlm:
    def test_success(self):
        from governance.routes.chat.commands import query_llm
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
        }
        with patch("httpx.post", return_value=mock_resp):
            result = query_llm("Hi")
        assert result == "Hello!"

    def test_with_system_prompt(self):
        from governance.routes.chat.commands import query_llm
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
        }
        with patch("httpx.post", return_value=mock_resp) as mock_post:
            query_llm("Hi", system_prompt="You are helpful")
        call_args = mock_post.call_args
        messages = call_args[1]["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"

    def test_http_error(self):
        from governance.routes.chat.commands import query_llm
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        with patch("httpx.post", return_value=mock_resp):
            result = query_llm("Hi")
        assert "error" in result.lower()

    def test_connection_error(self):
        from governance.routes.chat.commands import query_llm
        with patch("httpx.post", side_effect=Exception("Connection refused")):
            result = query_llm("Hi")
        assert "Cannot reach" in result


# ── process_chat_command ─────────────────────────────────────────


class TestProcessChatCommand:
    def test_status_command(self):
        from governance.routes.chat.commands import process_chat_command
        with patch(f"{_P}.list_sessions", return_value={"items": [], "pagination": {"total": 5}}):
            result = process_chat_command("/status", "code-agent")
        assert "System Status" in result
        assert "Rules:" in result

    def test_tasks_command(self):
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/tasks", "code-agent")
        assert "Pending Tasks" in result
        assert "T-1" in result

    def test_tasks_empty(self):
        from governance.routes.chat.commands import process_chat_command
        with patch(f"{_P}._tasks_store", {}):
            result = process_chat_command("/tasks", "code-agent")
        assert "No pending tasks" in result

    def test_rules_command(self):
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/rules", "code-agent")
        assert "Active Rules" in result

    def test_help_command(self):
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/help", "code-agent")
        assert "Available Commands" in result
        assert "/status" in result

    def test_agents_command(self):
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/agents", "code-agent")
        assert "Registered Agents" in result

    def test_agents_empty(self):
        from governance.routes.chat.commands import process_chat_command
        with patch(f"{_P}._agents_store", {}):
            result = process_chat_command("/agents", "code-agent")
        assert "No agents" in result

    def test_sessions_command(self):
        from governance.routes.chat.commands import process_chat_command
        with patch(f"{_P}.list_sessions", return_value={
            "items": [{"session_id": "S-1", "status": "ACTIVE",
                       "agent_id": "code-agent", "start_time": "2026-01-01T10:00:00"}],
            "pagination": {"total": 1},
        }):
            result = process_chat_command("/sessions", "code-agent")
        assert "Sessions" in result

    def test_context_command(self):
        from governance.routes.chat.commands import process_chat_command
        mock_ctx = MagicMock()
        mock_ctx.to_agent_prompt.return_value = "Context data"
        with patch(f"{_P}.preload_session_context", return_value=mock_ctx):
            result = process_chat_command("/context", "code-agent")
        assert result == "Context data"

    def test_search_command(self):
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/search bug", "code-agent")
        assert "Search Results" in result or "No results" in result

    def test_search_empty_query(self):
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/search", "code-agent")
        assert "Usage" in result

    def test_delegate_command(self):
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/delegate fix the tests", "code-agent")
        assert "__DELEGATE__:" in result

    def test_delegate_empty(self):
        from governance.routes.chat.commands import process_chat_command
        result = process_chat_command("/delegate", "code-agent")
        assert "Usage" in result

    def test_natural_language(self):
        from governance.routes.chat.commands import process_chat_command
        with patch(f"{_P}.query_llm", return_value="LLM response"), \
             patch(f"{_P}.list_sessions", return_value={"items": []}):
            result = process_chat_command("What rules exist?", "code-agent")
        assert result == "LLM response"
