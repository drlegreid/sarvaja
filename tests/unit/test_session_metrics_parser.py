"""
TDD Test Spec: Session Metrics Parser
======================================
Per SESSION-METRICS-01-v1: Claude Code JSONL log parsing.

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_session_metrics_parser.py -v
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures: synthetic JSONL log data
# ---------------------------------------------------------------------------

def _ts(iso: str) -> str:
    """Shorthand for ISO timestamp."""
    return iso


def _user_entry(ts: str, content: str = "hello", uuid: str = "u1",
                session_id: str = "sess-001") -> dict:
    return {
        "type": "user",
        "timestamp": ts,
        "sessionId": session_id,
        "uuid": uuid,
        "message": {"role": "user", "content": content},
    }


def _assistant_entry(ts: str, text: str = "response", thinking: str = None,
                     tool_uses: list = None, uuid: str = "a1",
                     session_id: str = "sess-001",
                     model: str = "claude-opus-4-5-20251101") -> dict:
    content = []
    if thinking:
        content.append({"type": "thinking", "thinking": thinking})
    if text:
        content.append({"type": "text", "text": text})
    for tu in (tool_uses or []):
        content.append({"type": "tool_use", "id": tu["id"], "name": tu["name"],
                         "input": tu.get("input", {})})
    return {
        "type": "assistant",
        "timestamp": ts,
        "sessionId": session_id,
        "uuid": uuid,
        "message": {"role": "assistant", "content": content, "model": model},
    }


def _tool_result_entry(ts: str, tool_use_id: str = "tu1",
                       session_id: str = "sess-001",
                       mcp_meta: dict = None) -> dict:
    entry = {
        "type": "user",
        "timestamp": ts,
        "sessionId": session_id,
        "uuid": "tr1",
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use_id,
                          "content": "result data"}],
        },
    }
    if mcp_meta:
        entry["mcpMeta"] = mcp_meta
    return entry


def _system_entry(ts: str, subtype: str = "compact_boundary",
                  session_id: str = "sess-001",
                  compact_meta: dict = None) -> dict:
    entry = {
        "type": "system",
        "timestamp": ts,
        "sessionId": session_id,
        "subtype": subtype,
        "content": "Conversation compacted",
    }
    if compact_meta:
        entry["compactMetadata"] = compact_meta
    return entry


def _progress_entry(ts: str, session_id: str = "sess-001") -> dict:
    return {
        "type": "progress",
        "timestamp": ts,
        "sessionId": session_id,
        "data": {"type": "hook_progress"},
    }


@pytest.fixture
def sample_log_dir(tmp_path):
    """Create a temp dir with a sample JSONL log file."""
    entries = [
        # Day 1: 2026-01-28, Session 1 (10 min active)
        _user_entry("2026-01-28T10:00:00Z", uuid="u1"),
        _assistant_entry("2026-01-28T10:01:00Z", thinking="Let me think...",
                         tool_uses=[{"id": "tu1", "name": "Read"}], uuid="a1"),
        _tool_result_entry("2026-01-28T10:01:30Z", tool_use_id="tu1"),
        _assistant_entry("2026-01-28T10:05:00Z", text="Done", uuid="a2"),
        _user_entry("2026-01-28T10:10:00Z", uuid="u2"),
        _assistant_entry("2026-01-28T10:10:30Z", uuid="a3"),

        # Gap > 30 min → new session
        # Day 1: 2026-01-28, Session 2 (5 min active)
        _user_entry("2026-01-28T11:00:00Z", uuid="u3"),
        _assistant_entry("2026-01-28T11:02:00Z",
                         tool_uses=[{"id": "tu2", "name": "Bash"},
                                    {"id": "tu3", "name": "mcp__gov-core__rules_query"}],
                         uuid="a4"),
        _assistant_entry("2026-01-28T11:05:00Z", uuid="a5"),

        # Day 2: 2026-01-29, Session 3 (3 min active)
        _user_entry("2026-01-29T14:00:00Z", uuid="u4"),
        _system_entry("2026-01-29T14:01:00Z", compact_meta={"trigger": "auto", "preTokens": 150000}),
        _assistant_entry("2026-01-29T14:02:00Z",
                         tool_uses=[{"id": "tu4", "name": "Edit"}], uuid="a6"),
        _user_entry("2026-01-29T14:03:00Z", uuid="u5"),
    ]

    log_file = tmp_path / "test-session.jsonl"
    with open(log_file, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    return tmp_path, log_file


@pytest.fixture
def empty_log_dir(tmp_path):
    """Empty directory with no JSONL files."""
    return tmp_path


@pytest.fixture
def multi_file_log_dir(tmp_path):
    """Directory with main log + agent subprocess log."""
    main_entries = [
        _user_entry("2026-01-29T10:00:00Z"),
        _assistant_entry("2026-01-29T10:05:00Z",
                         tool_uses=[{"id": "tu1", "name": "Task"}]),
    ]
    agent_entries = [
        _assistant_entry("2026-01-29T10:05:30Z", uuid="ag1",
                         tool_uses=[{"id": "atu1", "name": "Grep"}]),
        _assistant_entry("2026-01-29T10:06:00Z", uuid="ag2",
                         tool_uses=[{"id": "atu2", "name": "Read"}]),
    ]

    main_file = tmp_path / "main-session.jsonl"
    agent_file = tmp_path / "agent-sub1.jsonl"

    with open(main_file, "w") as f:
        for e in main_entries:
            f.write(json.dumps(e) + "\n")
    with open(agent_file, "w") as f:
        for e in agent_entries:
            f.write(json.dumps(e) + "\n")

    return tmp_path


# ---------------------------------------------------------------------------
# Tests: JSONL Discovery
# ---------------------------------------------------------------------------

class TestLogDiscovery:
    """Test JSONL file discovery in project directories."""

    def test_discover_main_log_files(self, sample_log_dir):
        """Parser finds .jsonl files in project directory."""
        from governance.session_metrics.parser import discover_log_files
        log_dir, _ = sample_log_dir
        files = discover_log_files(log_dir)
        assert len(files) >= 1
        assert all(f.suffix == ".jsonl" for f in files)

    def test_discover_excludes_agent_files_by_default(self, multi_file_log_dir):
        """Main discovery excludes agent-*.jsonl by default."""
        from governance.session_metrics.parser import discover_log_files
        files = discover_log_files(multi_file_log_dir, include_agents=False)
        assert not any("agent-" in f.name for f in files)

    def test_discover_includes_agent_files_when_requested(self, multi_file_log_dir):
        """Agent files included when include_agents=True."""
        from governance.session_metrics.parser import discover_log_files
        files = discover_log_files(multi_file_log_dir, include_agents=True)
        agent_files = [f for f in files if "agent-" in f.name]
        assert len(agent_files) >= 1

    def test_discover_empty_directory(self, empty_log_dir):
        """Empty directory returns empty list, no error."""
        from governance.session_metrics.parser import discover_log_files
        files = discover_log_files(empty_log_dir)
        assert files == []

    def test_discover_nonexistent_directory(self, tmp_path):
        """Nonexistent directory returns empty list, no error."""
        from governance.session_metrics.parser import discover_log_files
        files = discover_log_files(tmp_path / "does-not-exist")
        assert files == []


# ---------------------------------------------------------------------------
# Tests: JSONL Parsing
# ---------------------------------------------------------------------------

class TestLogParsing:
    """Test JSONL entry parsing and classification."""

    def test_parse_entries_returns_all(self, sample_log_dir):
        """Parser yields all entries from JSONL file."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        assert len(entries) == 13  # Total entries in fixture

    def test_parse_entries_streaming(self, sample_log_dir):
        """Parser uses streaming (generator), not loading all into memory."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        result = parse_log_file(log_file)
        # Should be a generator, not a list
        import types
        assert isinstance(result, types.GeneratorType)

    def test_parse_extracts_timestamp(self, sample_log_dir):
        """Each parsed entry has a datetime timestamp."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        for entry in entries:
            assert hasattr(entry, "timestamp")
            assert isinstance(entry.timestamp, datetime)

    def test_parse_extracts_entry_type(self, sample_log_dir):
        """Each parsed entry has a type classification."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        valid_types = {"user", "assistant", "system", "progress",
                       "file-history-snapshot", "queue-operation"}
        for entry in entries:
            assert entry.entry_type in valid_types

    def test_parse_extracts_tool_uses(self, sample_log_dir):
        """Parser extracts tool_use blocks from assistant content."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        assistant_entries = [e for e in entries if e.entry_type == "assistant"]
        tool_entries = [e for e in assistant_entries if e.tool_uses]
        assert len(tool_entries) >= 1
        # Check tool name extraction
        all_tools = []
        for e in tool_entries:
            all_tools.extend(e.tool_uses)
        tool_names = {t.name for t in all_tools}
        assert "Read" in tool_names

    def test_parse_extracts_thinking_length(self, sample_log_dir):
        """Parser extracts thinking block character count (not content)."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        thinking_entries = [e for e in entries if e.thinking_chars > 0]
        assert len(thinking_entries) >= 1
        # Should have char count, not actual content by default
        for e in thinking_entries:
            assert isinstance(e.thinking_chars, int)
            assert e.thinking_chars > 0

    def test_parse_detects_compaction(self, sample_log_dir):
        """Parser identifies compaction boundary entries."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        compactions = [e for e in entries if e.is_compaction]
        assert len(compactions) == 1

    def test_parse_detects_mcp_calls(self, sample_log_dir):
        """Parser identifies MCP tool calls (name starts with mcp__)."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        assistant_entries = [e for e in entries if e.entry_type == "assistant"]
        mcp_tools = []
        for e in assistant_entries:
            for tu in e.tool_uses:
                if tu.is_mcp:
                    mcp_tools.append(tu)
        assert len(mcp_tools) >= 1
        assert mcp_tools[0].name.startswith("mcp__")

    def test_parse_handles_malformed_line(self, tmp_path):
        """Parser skips malformed JSON lines gracefully."""
        from governance.session_metrics.parser import parse_log_file
        log_file = tmp_path / "bad.jsonl"
        with open(log_file, "w") as f:
            f.write('{"type": "user", "timestamp": "2026-01-29T10:00:00Z"}\n')
            f.write("not json at all\n")
            f.write('{"type": "assistant", "timestamp": "2026-01-29T10:01:00Z"}\n')
        entries = list(parse_log_file(log_file))
        assert len(entries) == 2  # Skipped the bad line

    def test_parse_extracts_model(self, sample_log_dir):
        """Parser extracts model name from assistant entries."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        assistant_entries = [e for e in entries if e.entry_type == "assistant"]
        models = {e.model for e in assistant_entries if e.model}
        assert "claude-opus-4-5-20251101" in models


# ---------------------------------------------------------------------------
# Tests: Privacy
# ---------------------------------------------------------------------------

class TestPrivacy:
    """Test privacy constraints on parsed data."""

    def test_thinking_content_excluded_by_default(self, sample_log_dir):
        """Thinking block content is NOT included in parsed entries."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        thinking_entries = [e for e in entries if e.thinking_chars > 0]
        for e in thinking_entries:
            assert e.thinking_content is None

    def test_thinking_content_included_when_requested(self, sample_log_dir):
        """Thinking content available with include_thinking=True."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file, include_thinking=True))
        thinking_entries = [e for e in entries if e.thinking_chars > 0]
        for e in thinking_entries:
            assert e.thinking_content is not None
            assert len(e.thinking_content) == e.thinking_chars

    def test_user_message_content_not_stored(self, sample_log_dir):
        """User message content is not stored in parsed entries."""
        from governance.session_metrics.parser import parse_log_file
        _, log_file = sample_log_dir
        entries = list(parse_log_file(log_file))
        user_entries = [e for e in entries if e.entry_type == "user"]
        for e in user_entries:
            assert e.user_content is None

    def test_tool_input_truncated(self, tmp_path):
        """Tool input is truncated to max 200 chars in output."""
        from governance.session_metrics.parser import parse_log_file
        log_file = tmp_path / "long-tool.jsonl"
        long_input = {"code": "x" * 500}
        entry = _assistant_entry(
            "2026-01-29T10:00:00Z",
            tool_uses=[{"id": "tu1", "name": "Bash", "input": long_input}]
        )
        with open(log_file, "w") as f:
            f.write(json.dumps(entry) + "\n")

        entries = list(parse_log_file(log_file))
        for tu in entries[0].tool_uses:
            serialized = json.dumps(tu.input_summary)
            assert len(serialized) <= 250  # 200 + some JSON overhead
