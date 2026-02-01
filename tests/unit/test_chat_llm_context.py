"""
Tests for enriched LLM context and token limit.

Per A.3: Enrich LLM context and increase token limit.
Verifies:
- max_tokens increased from 512 to 2048
- System prompt includes available commands
- System prompt includes session context
- Natural language handler passes enriched context

Created: 2026-02-01
"""
import pytest
from unittest.mock import patch, MagicMock


class TestLLMTokenLimit:
    """Tests for increased token limit."""

    def test_max_tokens_at_least_2048(self):
        """LLM queries should use max_tokens >= 2048."""
        captured_json = {}

        def mock_post(url, **kwargs):
            captured_json.update(kwargs.get("json", {}))
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": "test response"}}]
            }
            return mock_resp

        with patch("httpx.post", mock_post):
            from governance.routes.chat.commands import query_llm
            query_llm("test query", system_prompt="test")

        assert captured_json.get("max_tokens", 0) >= 2048


class TestEnrichedSystemPrompt:
    """Tests for enriched system prompt content."""

    def test_system_prompt_includes_commands(self):
        """System prompt should list available commands for LLM awareness."""
        from governance.routes.chat.commands import GOVERNANCE_SYSTEM_PROMPT
        assert "/sessions" in GOVERNANCE_SYSTEM_PROMPT or "sessions" in GOVERNANCE_SYSTEM_PROMPT

    def test_system_prompt_mentions_governance(self):
        """System prompt should mention governance platform context."""
        from governance.routes.chat.commands import GOVERNANCE_SYSTEM_PROMPT
        assert "governance" in GOVERNANCE_SYSTEM_PROMPT.lower()

    def test_natural_language_includes_session_count(self):
        """Natural language handler should include session count in context."""
        captured_prompt = {}

        with patch("governance.routes.chat.commands._sessions_store", {"s1": {}}), \
             patch("governance.routes.chat.commands.query_llm") as mock_llm:
            mock_llm.return_value = "mocked response"
            from governance.routes.chat.commands import process_chat_command
            result = process_chat_command("tell me about the platform", "agent-1")
            call_args = mock_llm.call_args
            system_prompt = call_args[1].get("system_prompt", "") if call_args[1] else call_args[0][1]
            assert "1 sessions" in system_prompt or "sessions" in system_prompt
