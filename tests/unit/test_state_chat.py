"""
Unit tests for Agent Chat State.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/chat.py.
Tests: with_chat_messages, with_chat_message, with_chat_loading, with_chat_input,
       with_chat_agent, with_chat_session, with_chat_task,
       get_chat_role_color, get_chat_status_icon, format_chat_message,
       create_user_message, create_agent_message, create_system_message.
"""

from agent.governance_ui.state.chat import (
    with_chat_messages, with_chat_message, with_chat_loading,
    with_chat_input, with_chat_agent, with_chat_session, with_chat_task,
    get_chat_role_color, get_chat_status_icon, format_chat_message,
    create_user_message, create_agent_message, create_system_message,
)


# ── State Transforms ─────────────────────────────────────


class TestWithChatMessages:
    def test_sets_messages(self):
        msgs = [{"id": "M-1"}]
        assert with_chat_messages({}, msgs)["chat_messages"] == msgs

    def test_preserves_state(self):
        result = with_chat_messages({"x": 1}, [])
        assert result["x"] == 1


class TestWithChatMessage:
    def test_appends_message(self):
        state = {"chat_messages": [{"id": "M-1"}]}
        result = with_chat_message(state, {"id": "M-2"})
        assert len(result["chat_messages"]) == 2
        assert result["chat_messages"][1]["id"] == "M-2"

    def test_empty_messages(self):
        result = with_chat_message({}, {"id": "M-1"})
        assert len(result["chat_messages"]) == 1

    def test_does_not_mutate_original(self):
        original = [{"id": "M-1"}]
        state = {"chat_messages": original}
        with_chat_message(state, {"id": "M-2"})
        assert len(original) == 1


class TestWithChatLoading:
    def test_default_true(self):
        assert with_chat_loading({})["chat_loading"] is True

    def test_false(self):
        assert with_chat_loading({}, False)["chat_loading"] is False


class TestWithChatInput:
    def test_sets_input(self):
        assert with_chat_input({}, "Hello")["chat_input"] == "Hello"


class TestWithChatAgent:
    def test_sets_agent(self):
        assert with_chat_agent({}, "code-agent")["chat_selected_agent"] == "code-agent"

    def test_none(self):
        assert with_chat_agent({}, None)["chat_selected_agent"] is None


class TestWithChatSession:
    def test_sets_session(self):
        assert with_chat_session({}, "S-1")["chat_session_id"] == "S-1"


class TestWithChatTask:
    def test_sets_task(self):
        assert with_chat_task({}, "T-1")["chat_task_id"] == "T-1"


# ── UI Helpers ────────────────────────────────────────────


class TestGetChatRoleColor:
    def test_known_roles(self):
        assert get_chat_role_color("user") == "primary"
        assert get_chat_role_color("agent") == "success"
        assert get_chat_role_color("system") == "grey"
        assert get_chat_role_color("error") == "error"

    def test_case_insensitive(self):
        assert get_chat_role_color("USER") == "primary"

    def test_unknown(self):
        assert get_chat_role_color("xyz") == "grey"


class TestGetChatStatusIcon:
    def test_known_statuses(self):
        assert get_chat_status_icon("pending") == "mdi-clock-outline"
        assert get_chat_status_icon("complete") == "mdi-check"
        assert get_chat_status_icon("error") == "mdi-alert-circle"

    def test_unknown(self):
        assert get_chat_status_icon("xyz") == "mdi-help-circle"


# ── Format Functions ──────────────────────────────────────


class TestFormatChatMessage:
    def test_user_message(self):
        msg = {"id": "M-1", "role": "user", "content": "Hello",
               "timestamp": "2026-01-01T10:00:00", "status": "complete"}
        result = format_chat_message(msg)
        assert result["id"] == "M-1"
        assert result["is_user"] is True
        assert result["is_agent"] is False
        assert result["role_color"] == "primary"
        assert result["status_icon"] == "mdi-check"

    def test_agent_message(self):
        msg = {"role": "agent", "agent_id": "A-1", "agent_name": "Bot",
               "task_id": "T-1", "status": "processing"}
        result = format_chat_message(msg)
        assert result["is_agent"] is True
        assert result["agent_id"] == "A-1"
        assert result["task_id"] == "T-1"
        assert result["role_color"] == "success"

    def test_defaults(self):
        result = format_chat_message({})
        assert result["role"] == "user"
        assert result["agent_name"] == "Agent"
        assert result["content"] == ""


# ── Message Factories ────────────────────────────────────


class TestCreateUserMessage:
    def test_creates_message(self):
        msg = create_user_message("Hello")
        assert msg["role"] == "user"
        assert msg["content"] == "Hello"
        assert msg["status"] == "complete"
        assert msg["id"].startswith("MSG-")

    def test_custom_timestamp(self):
        msg = create_user_message("Hi", timestamp="2026-01-01T00:00:00")
        assert msg["timestamp"] == "2026-01-01T00:00:00"


class TestCreateAgentMessage:
    def test_creates_message(self):
        msg = create_agent_message("Response", "A-1", "Code Agent")
        assert msg["role"] == "agent"
        assert msg["content"] == "Response"
        assert msg["agent_id"] == "A-1"
        assert msg["agent_name"] == "Code Agent"

    def test_with_task(self):
        msg = create_agent_message("R", "A-1", task_id="T-1")
        assert msg["task_id"] == "T-1"

    def test_pending_status(self):
        msg = create_agent_message("R", "A-1", status="pending")
        assert msg["status"] == "pending"


class TestCreateSystemMessage:
    def test_creates_message(self):
        msg = create_system_message("System info")
        assert msg["role"] == "system"
        assert msg["content"] == "System info"
        assert msg["id"].startswith("MSG-")
