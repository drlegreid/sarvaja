"""Batch 209 — Chat commands + session scanner defense tests.

Validates fixes for:
- BUG-209-CMD-SLICE-001: None[:16] guard on start_time
- BUG-209-CMD-FORMAT-001: None:.2f guard on trust_score
- BUG-209-CMD-ITER-001: _tasks_store iteration snapshot
- BUG-209-SCANNER-ENCODING-001: encoding on cc_session_scanner open
"""
from pathlib import Path
from unittest.mock import patch


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-209-CMD-SLICE-001: None guard on start_time ──────────────────

class TestCommandStartTimeGuard:
    """process_chat_command must guard against None start_time."""

    def test_sessions_command_handles_none_start_time(self):
        """When start_time is None, /sessions must not crash."""
        from governance.routes.chat.commands import process_chat_command
        with patch("governance.routes.chat.commands._tasks_store", {}), \
             patch("governance.routes.chat.commands._agents_store", {}), \
             patch("governance.routes.chat.commands._sessions_store", {
                 "S1": {"session_id": "S1", "start_time": None, "status": "ACTIVE"},
             }), \
             patch("governance.routes.chat.commands.list_sessions") as mock_ls, \
             patch("governance.routes.chat.commands.get_client", return_value=None):
            # Make list_sessions raise so fallback path is used
            mock_ls.side_effect = Exception("unavailable")
            result = process_chat_command("/sessions", "AGENT-001")
        assert "N/A" in result or "S1" in result

    def test_or_pattern_in_source(self):
        """Source must use (s.get('start_time') or 'N/A') pattern."""
        src = (SRC / "governance/routes/chat/commands.py").read_text()
        assert "s.get('start_time') or 'N/A'" in src


# ── BUG-209-CMD-FORMAT-001: None guard on trust_score ─────────────────

class TestCommandTrustScoreGuard:
    """process_chat_command must guard against None trust_score."""

    def test_agents_command_handles_none_trust_score(self):
        """When trust_score is None, /agents must not crash."""
        from governance.routes.chat.commands import process_chat_command
        with patch("governance.routes.chat.commands._tasks_store", {}), \
             patch("governance.routes.chat.commands._agents_store", {
                 "A1": {"agent_id": "A1", "name": "Test Agent", "trust_score": None},
             }), \
             patch("governance.routes.chat.commands._sessions_store", {}), \
             patch("governance.routes.chat.commands.get_client", return_value=None):
            result = process_chat_command("/agents", "A1")
        assert "A1" in result
        assert "0.00" in result  # None → 0 → "0.00"

    def test_or_pattern_in_source_trust(self):
        """Source must use (a.get('trust_score') or 0) pattern."""
        src = (SRC / "governance/routes/chat/commands.py").read_text()
        assert "a.get('trust_score') or 0" in src


# ── BUG-209-CMD-ITER-001: _tasks_store iteration snapshot ────────────

class TestCommandStoreSnapshot:
    """commands.py must use list() snapshot for _tasks_store iteration."""

    def test_tasks_iteration_uses_snapshot(self):
        """All _tasks_store.values() iterations must use list() snapshot."""
        src = (SRC / "governance/routes/chat/commands.py").read_text()
        # Count bare _tasks_store.values() (without list())
        import re
        bare_iters = re.findall(r'(?<!list\()_tasks_store\.values\(\)', src)
        assert len(bare_iters) == 0, f"Found {len(bare_iters)} bare _tasks_store.values() iterations"


# ── BUG-209-SCANNER-ENCODING-001: cc_session_scanner encoding ────────

class TestScannerEncoding:
    """cc_session_scanner must specify encoding on file open."""

    def test_scanner_has_encoding(self):
        """scan_jsonl_metadata must open files with encoding='utf-8'."""
        src = (SRC / "governance/services/cc_session_scanner.py").read_text()
        assert 'encoding="utf-8"' in src or "encoding='utf-8'" in src


# ── Chat commands defense ─────────────────────────────────────────────

class TestChatCommandsDefense:
    """Defense tests for chat commands module."""

    def test_process_chat_command_callable(self):
        from governance.routes.chat.commands import process_chat_command
        assert callable(process_chat_command)

    def test_query_llm_callable(self):
        from governance.routes.chat.commands import query_llm
        assert callable(query_llm)

    def test_help_command_returns_help(self):
        from governance.routes.chat.commands import process_chat_command
        with patch("governance.routes.chat.commands._tasks_store", {}), \
             patch("governance.routes.chat.commands._agents_store", {}), \
             patch("governance.routes.chat.commands._sessions_store", {}), \
             patch("governance.routes.chat.commands.get_client", return_value=None):
            result = process_chat_command("/help", "AGENT-001")
        assert "Available Commands" in result

    def test_status_command_returns_status(self):
        from governance.routes.chat.commands import process_chat_command
        with patch("governance.routes.chat.commands._tasks_store", {}), \
             patch("governance.routes.chat.commands._agents_store", {}), \
             patch("governance.routes.chat.commands._sessions_store", {}), \
             patch("governance.routes.chat.commands.get_client", return_value=None), \
             patch("governance.routes.chat.commands.list_sessions", return_value={"pagination": {"total": 5}, "items": []}):
            result = process_chat_command("/status", "AGENT-001")
        assert "System Status" in result

    def test_search_empty_query_returns_usage(self):
        from governance.routes.chat.commands import process_chat_command
        with patch("governance.routes.chat.commands._tasks_store", {}), \
             patch("governance.routes.chat.commands._agents_store", {}), \
             patch("governance.routes.chat.commands._sessions_store", {}), \
             patch("governance.routes.chat.commands.get_client", return_value=None):
            result = process_chat_command("/search", "AGENT-001")
        assert "Usage" in result

    def test_delegate_empty_returns_usage(self):
        from governance.routes.chat.commands import process_chat_command
        with patch("governance.routes.chat.commands._tasks_store", {}), \
             patch("governance.routes.chat.commands._agents_store", {}), \
             patch("governance.routes.chat.commands._sessions_store", {}), \
             patch("governance.routes.chat.commands.get_client", return_value=None):
            result = process_chat_command("/delegate", "AGENT-001")
        assert "Usage" in result

    def test_delegate_with_desc_returns_marker(self):
        from governance.routes.chat.commands import process_chat_command
        with patch("governance.routes.chat.commands._tasks_store", {}), \
             patch("governance.routes.chat.commands._agents_store", {}), \
             patch("governance.routes.chat.commands._sessions_store", {}), \
             patch("governance.routes.chat.commands.get_client", return_value=None):
            result = process_chat_command("/delegate fix the login bug", "AGENT-001")
        assert result.startswith("__DELEGATE__:")
