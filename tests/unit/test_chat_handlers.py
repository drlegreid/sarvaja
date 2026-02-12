"""
Unit tests for Chat & Agent Interaction Handlers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/handlers/common_handlers_chat.py.
Tests: register_chat_handlers, _process_chat_command, _send_to_agent.
"""

from unittest.mock import MagicMock, patch

from agent.governance_ui.handlers.common_handlers_chat import (
    register_chat_handlers,
    _process_chat_command,
    _send_to_agent,
)


class _MockCtrl:
    """Mock Trame controller that captures trigger registrations."""

    def __init__(self):
        self._triggers = {}

    def trigger(self, name):
        def decorator(fn):
            self._triggers[name] = fn
            return fn
        return decorator


class _MockState:
    """Mock Trame state object."""

    def __init__(self):
        self.chat_input = ""
        self.chat_messages = []
        self.rules = []
        self.tasks = []
        self.agents = []
        self.selected_chat_agent = None


# ── register_chat_handlers ─────────────────────────────────


class TestRegisterChatHandlers:
    def test_registers_triggers(self):
        ctrl = _MockCtrl()
        state = _MockState()
        register_chat_handlers(ctrl, state)
        assert "send_chat_message" in ctrl._triggers
        assert "clear_chat" in ctrl._triggers

    def test_clear_chat(self):
        ctrl = _MockCtrl()
        state = _MockState()
        state.chat_messages = [{"role": "user", "content": "hi"}]
        register_chat_handlers(ctrl, state)
        ctrl._triggers["clear_chat"]()
        assert state.chat_messages == []

    def test_send_empty_message_ignored(self):
        ctrl = _MockCtrl()
        state = _MockState()
        state.chat_input = ""
        register_chat_handlers(ctrl, state)
        ctrl._triggers["send_chat_message"]()
        assert state.chat_messages == []

    def test_send_whitespace_only_ignored(self):
        ctrl = _MockCtrl()
        state = _MockState()
        state.chat_input = "   "
        register_chat_handlers(ctrl, state)
        ctrl._triggers["send_chat_message"]()
        assert state.chat_messages == []

    def test_send_message_adds_user_msg(self):
        ctrl = _MockCtrl()
        state = _MockState()
        state.chat_input = "/help"
        register_chat_handlers(ctrl, state)
        ctrl._triggers["send_chat_message"]()
        # Should have user message + bot response
        assert len(state.chat_messages) >= 2
        assert state.chat_messages[0]["role"] == "user"
        assert state.chat_messages[0]["content"] == "/help"

    def test_send_clears_input(self):
        ctrl = _MockCtrl()
        state = _MockState()
        state.chat_input = "/help"
        register_chat_handlers(ctrl, state)
        ctrl._triggers["send_chat_message"]()
        assert state.chat_input == ""


# ── _process_chat_command ──────────────────────────────────


class TestProcessChatCommand:
    def test_help_command(self):
        state = _MockState()
        _process_chat_command(state, "/help")
        assert len(state.chat_messages) == 1
        assert state.chat_messages[0]["role"] == "assistant"
        assert "Available commands" in state.chat_messages[0]["content"]

    def test_status_command(self):
        state = _MockState()
        state.rules = [{"id": "1"}, {"id": "2"}]
        state.tasks = [{"id": "1"}]
        state.agents = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        _process_chat_command(state, "/status")
        content = state.chat_messages[0]["content"]
        assert "2 rules" in content
        assert "1 tasks" in content
        assert "3 agents" in content

    def test_tasks_command(self):
        state = _MockState()
        state.tasks = [
            {"status": "TODO"}, {"status": "TODO"},
            {"status": "DONE"},
        ]
        _process_chat_command(state, "/tasks")
        assert "2 pending" in state.chat_messages[0]["content"]

    def test_rules_command(self):
        state = _MockState()
        state.rules = [
            {"status": "ACTIVE"}, {"status": "ACTIVE"},
            {"status": "DEPRECATED"},
        ]
        _process_chat_command(state, "/rules")
        assert "2 active" in state.chat_messages[0]["content"]

    def test_agents_command(self):
        state = _MockState()
        state.agents = [{"id": "1"}, {"id": "2"}]
        _process_chat_command(state, "/agents")
        assert "2 registered" in state.chat_messages[0]["content"]

    def test_unknown_command(self):
        state = _MockState()
        _process_chat_command(state, "/unknown")
        assert "Unknown command" in state.chat_messages[0]["content"]

    def test_command_case_insensitive(self):
        state = _MockState()
        _process_chat_command(state, "/HELP")
        assert "Available commands" in state.chat_messages[0]["content"]


# ── _send_to_agent ─────────────────────────────────────────


class TestSendToAgent:
    @patch("agent.governance_ui.handlers.common_handlers_chat.httpx")
    def test_successful_response(self, mock_httpx):
        state = _MockState()
        state.selected_chat_agent = "code-agent"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Hello!"}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx.Client.return_value = mock_client

        _send_to_agent(state, "hi there")

        assert len(state.chat_messages) == 1
        assert state.chat_messages[0]["role"] == "assistant"
        assert state.chat_messages[0]["content"] == "Hello!"

    @patch("agent.governance_ui.handlers.common_handlers_chat.httpx")
    def test_error_response(self, mock_httpx):
        state = _MockState()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx.Client.return_value = mock_client

        _send_to_agent(state, "test")

        assert "Error: 500" in state.chat_messages[0]["content"]

    @patch("agent.governance_ui.handlers.common_handlers_chat.httpx")
    def test_connection_error(self, mock_httpx):
        state = _MockState()
        mock_client = MagicMock()
        mock_client.post.side_effect = ConnectionError("refused")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx.Client.return_value = mock_client

        _send_to_agent(state, "test")

        assert "Connection error" in state.chat_messages[0]["content"]

    @patch("agent.governance_ui.handlers.common_handlers_chat.httpx")
    def test_default_agent(self, mock_httpx):
        state = _MockState()
        state.selected_chat_agent = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "ok"}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_httpx.Client.return_value = mock_client

        _send_to_agent(state, "hi")

        call_url = mock_client.post.call_args[0][0]
        assert "claude-code" in call_url
