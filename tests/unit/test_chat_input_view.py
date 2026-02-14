"""
Tests for chat input view components.

Per GAP-UI-CHAT-001: Agent command interface.
Batch 165: New coverage for views/chat/input.py (0->10 tests).
"""
import inspect

import pytest


class TestChatInputComponents:
    def test_build_chat_input_callable(self):
        from agent.governance_ui.views.chat.input import build_chat_input
        assert callable(build_chat_input)

    def test_build_quick_commands_callable(self):
        from agent.governance_ui.views.chat.input import build_quick_commands
        assert callable(build_quick_commands)


class TestChatInputContent:
    def test_has_input_testid(self):
        from agent.governance_ui.views.chat import input as chat_input
        source = inspect.getsource(chat_input)
        assert "chat-input" in source

    def test_has_send_btn(self):
        from agent.governance_ui.views.chat import input as chat_input
        source = inspect.getsource(chat_input)
        assert "chat-send-btn" in source

    def test_has_send_icon(self):
        from agent.governance_ui.views.chat import input as chat_input
        source = inspect.getsource(chat_input)
        assert "mdi-send" in source

    def test_has_enter_trigger(self):
        from agent.governance_ui.views.chat import input as chat_input
        source = inspect.getsource(chat_input)
        assert "keyup.enter" in source


class TestQuickCommandsContent:
    def test_has_help_command(self):
        from agent.governance_ui.views.chat import input as chat_input
        source = inspect.getsource(chat_input)
        assert "chat-cmd-help" in source

    def test_has_status_command(self):
        from agent.governance_ui.views.chat import input as chat_input
        source = inspect.getsource(chat_input)
        assert "chat-cmd-status" in source

    def test_has_tasks_command(self):
        from agent.governance_ui.views.chat import input as chat_input
        source = inspect.getsource(chat_input)
        assert "chat-cmd-tasks" in source

    def test_has_agents_command(self):
        from agent.governance_ui.views.chat import input as chat_input
        source = inspect.getsource(chat_input)
        assert "chat-cmd-agents" in source
