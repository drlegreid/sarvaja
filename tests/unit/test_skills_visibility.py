"""
Unit tests for Skills Visibility (Phase 3).

Per feedback #3: Slash commands should NOT be recorded as tool calls.
Tool calls should be classified by category (cc_builtin, mcp, chat_command).
"""

from unittest.mock import patch, MagicMock


# ── Chat command filtering in endpoints ──────────────────


class TestChatCommandFiltering:
    """Verify slash commands are NOT recorded as tool calls."""

    def test_slash_command_skipped(self):
        """Commands starting with / should not be recorded as tool_name."""
        from governance.routes.chat.session_bridge import is_chat_command
        assert is_chat_command("/status") is True
        assert is_chat_command("/tasks") is True
        assert is_chat_command("/help") is True
        assert is_chat_command("/entropy") is True

    def test_regular_text_not_command(self):
        """Regular text should NOT be flagged as command."""
        from governance.routes.chat.session_bridge import is_chat_command
        assert is_chat_command("What is the weather?") is False
        assert is_chat_command("Fix the bug in auth.py") is False
        assert is_chat_command("") is False

    def test_mcp_tool_not_command(self):
        """MCP tool names should not be flagged as commands."""
        from governance.routes.chat.session_bridge import is_chat_command
        assert is_chat_command("mcp__gov-core__rules_query") is False


# ── Tool category classification ─────────────────────────


class TestToolCategoryClassification:
    """Verify tools are classified by category."""

    def test_mcp_tools(self):
        from governance.routes.chat.session_bridge import classify_tool
        assert classify_tool("mcp__gov-core__rules_query") == "mcp_governance"
        assert classify_tool("mcp__gov-sessions__session_start") == "mcp_governance"
        assert classify_tool("mcp__gov-tasks__task_create") == "mcp_governance"
        assert classify_tool("mcp__gov-agents__agent_get") == "mcp_governance"

    def test_mcp_non_governance(self):
        from governance.routes.chat.session_bridge import classify_tool
        assert classify_tool("mcp__claude-mem__chroma_query") == "mcp_other"
        assert classify_tool("mcp__playwright__browser_click") == "mcp_other"
        assert classify_tool("mcp__rest-api__test_request") == "mcp_other"

    def test_cc_builtin_tools(self):
        from governance.routes.chat.session_bridge import classify_tool
        assert classify_tool("Read") == "cc_builtin"
        assert classify_tool("Write") == "cc_builtin"
        assert classify_tool("Edit") == "cc_builtin"
        assert classify_tool("Bash") == "cc_builtin"
        assert classify_tool("Glob") == "cc_builtin"
        assert classify_tool("Grep") == "cc_builtin"
        assert classify_tool("TodoWrite") == "cc_builtin"
        assert classify_tool("Task") == "cc_builtin"
        assert classify_tool("WebSearch") == "cc_builtin"
        assert classify_tool("WebFetch") == "cc_builtin"

    def test_chat_commands(self):
        from governance.routes.chat.session_bridge import classify_tool
        assert classify_tool("/status") == "chat_command"
        assert classify_tool("/tasks") == "chat_command"
        assert classify_tool("/help") == "chat_command"

    def test_unknown_tool(self):
        from governance.routes.chat.session_bridge import classify_tool
        assert classify_tool("some_custom_tool") == "unknown"


# ── Session tool logger skip list ────────────────────────


class TestToolLoggerSkipList:
    """Verify session_tool_logger skips non-governance tools."""

    def test_skip_tools_expanded(self):
        from hooks_utils.session_tool_logger import SKIP_TOOLS
        assert "session_tool_call" in SKIP_TOOLS
        assert "session_thought" in SKIP_TOOLS
        assert "TodoWrite" in SKIP_TOOLS

    def test_main_skips_listed_tools(self):
        """main() should return 0 and not log for skip_tools."""
        from hooks_utils.session_tool_logger import main
        with patch.dict("os.environ", {"CLAUDE_TOOL_NAME": "TodoWrite"}):
            assert main() == 0


# ── record_chat_tool_call respects category ──────────────


class TestRecordToolCallCategory:
    """Verify tool calls stored with category metadata."""

    @patch("governance.routes.chat.session_bridge._sessions_store", {})
    def test_tool_call_has_category(self):
        from governance.routes.chat.session_bridge import record_chat_tool_call

        collector = MagicMock()
        collector.session_id = "S-1"
        collector.capture_tool_call = MagicMock()

        # Pre-populate sessions store
        import governance.routes.chat.session_bridge as mod
        mod._sessions_store["S-1"] = {"session_id": "S-1"}

        record_chat_tool_call(
            collector,
            tool_name="mcp__gov-core__rules_query",
            arguments={"limit": 10},
        )

        store = mod._sessions_store["S-1"]
        assert len(store["tool_calls"]) == 1
        assert store["tool_calls"][0]["tool_category"] == "mcp_governance"

    @patch("governance.routes.chat.session_bridge._sessions_store", {})
    def test_chat_command_has_category(self):
        from governance.routes.chat.session_bridge import record_chat_tool_call

        collector = MagicMock()
        collector.session_id = "S-2"
        collector.capture_tool_call = MagicMock()

        import governance.routes.chat.session_bridge as mod
        mod._sessions_store["S-2"] = {"session_id": "S-2"}

        record_chat_tool_call(
            collector,
            tool_name="/status",
        )

        store = mod._sessions_store["S-2"]
        assert store["tool_calls"][0]["tool_category"] == "chat_command"
