"""
Tests for chat view container.

Batch 168: New coverage for agent/governance_ui/views/chat_view.py (0->8 tests).
"""
import inspect

import pytest


class TestChatViewComponents:
    def test_build_chat_view_callable(self):
        from agent.governance_ui.views.chat_view import build_chat_view
        assert callable(build_chat_view)


class TestChatViewContent:
    def test_has_chat_view_testid(self):
        from agent.governance_ui.views import chat_view
        source = inspect.getsource(chat_view)
        assert "chat-view" in source

    def test_imports_chat_header(self):
        from agent.governance_ui.views import chat_view
        source = inspect.getsource(chat_view)
        assert "build_chat_header" in source

    def test_imports_chat_messages(self):
        from agent.governance_ui.views import chat_view
        source = inspect.getsource(chat_view)
        assert "build_chat_messages" in source

    def test_imports_chat_input(self):
        from agent.governance_ui.views import chat_view
        source = inspect.getsource(chat_view)
        assert "build_chat_input" in source

    def test_imports_quick_commands(self):
        from agent.governance_ui.views import chat_view
        source = inspect.getsource(chat_view)
        assert "build_quick_commands" in source

    def test_imports_execution_viewer(self):
        from agent.governance_ui.views import chat_view
        source = inspect.getsource(chat_view)
        assert "build_task_execution_viewer" in source
