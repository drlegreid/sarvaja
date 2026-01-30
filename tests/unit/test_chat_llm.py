"""
Tests for Chat LLM integration.

Per PLAN-UI-OVERHAUL-001 Task 3.5: Wire LLM for natural language chat.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestChatLLMIntegration:
    """Verify chat routes use LLM for natural language queries."""

    def test_chat_commands_has_llm_handler(self):
        """Chat commands module should have an LLM query function."""
        from governance.routes.chat import commands
        source = inspect.getsource(commands)
        assert 'query_llm' in source or 'llm_response' in source or 'litellm' in source.lower(), (
            "Chat commands should integrate LLM for natural language"
        )

    def test_natural_language_calls_llm(self):
        """Natural language input should attempt LLM call, not return canned text."""
        from governance.routes.chat import commands
        source = inspect.getsource(commands.process_chat_command)
        # Should NOT have the old canned response
        assert "I'm here to help with governance tasks" not in source, (
            "Chat should not return canned 'I'm here to help' for natural language"
        )

    def test_llm_query_function_exists(self):
        """A query_llm function should exist in chat commands."""
        from governance.routes.chat import commands
        assert hasattr(commands, 'query_llm'), (
            "Chat commands should have a query_llm function"
        )

    def test_llm_query_accepts_message_and_context(self):
        """query_llm should accept message and context parameters."""
        from governance.routes.chat import commands
        sig = inspect.signature(commands.query_llm)
        params = list(sig.parameters.keys())
        assert 'message' in params, "query_llm should accept 'message' parameter"
        assert 'context' in params or 'system_prompt' in params, (
            "query_llm should accept context or system_prompt parameter"
        )
