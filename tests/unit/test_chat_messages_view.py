"""
Tests for chat messages view components.

Per GAP-UI-CHAT-001: Agent command interface.
Batch 165: New coverage for views/chat/messages.py (0->10 tests).
"""
import inspect

import pytest


class TestChatMessagesComponents:
    def test_build_user_message_callable(self):
        from agent.governance_ui.views.chat.messages import build_user_message
        assert callable(build_user_message)

    def test_build_agent_message_callable(self):
        from agent.governance_ui.views.chat.messages import build_agent_message
        assert callable(build_agent_message)

    def test_build_system_message_callable(self):
        from agent.governance_ui.views.chat.messages import build_system_message
        assert callable(build_system_message)

    def test_build_chat_messages_callable(self):
        from agent.governance_ui.views.chat.messages import build_chat_messages
        assert callable(build_chat_messages)


class TestChatMessagesContent:
    def test_has_user_message_testid(self):
        from agent.governance_ui.views.chat import messages
        source = inspect.getsource(messages)
        assert "chat-user-message" in source

    def test_has_agent_message_testid(self):
        from agent.governance_ui.views.chat import messages
        source = inspect.getsource(messages)
        assert "chat-agent-message" in source

    def test_has_robot_icon(self):
        from agent.governance_ui.views.chat import messages
        source = inspect.getsource(messages)
        assert "mdi-robot" in source

    def test_has_loading_indicator(self):
        from agent.governance_ui.views.chat import messages
        source = inspect.getsource(messages)
        assert "chat_loading" in source

    def test_has_welcome_import(self):
        from agent.governance_ui.views.chat import messages
        source = inspect.getsource(messages)
        assert "build_chat_welcome" in source

    def test_has_thinking_text(self):
        from agent.governance_ui.views.chat import messages
        source = inspect.getsource(messages)
        assert "thinking" in source.lower()
