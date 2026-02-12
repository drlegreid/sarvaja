"""
Unit tests for Session Metrics JSONL Parser.

Per DOC-SIZE-01-v1: Tests for session_metrics/parser.py module.
Tests: discover_log_files(), _parse_timestamp(), _extract_* helpers,
       parse_log_file(), parse_log_file_extended().
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from governance.session_metrics.parser import (
    discover_log_files,
    _parse_timestamp,
    _extract_text_content,
    _extract_tool_uses,
    _extract_tool_results,
    _extract_thinking,
    parse_log_file,
    parse_log_file_extended,
)


class TestDiscoverLogFiles:
    def test_finds_jsonl(self, tmp_path):
        (tmp_path / "session1.jsonl").write_text("")
        (tmp_path / "session2.jsonl").write_text("")
        (tmp_path / "other.txt").write_text("")
        files = discover_log_files(tmp_path)
        assert len(files) == 2

    def test_excludes_agents(self, tmp_path):
        (tmp_path / "session.jsonl").write_text("")
        (tmp_path / "agent-sub.jsonl").write_text("")
        files = discover_log_files(tmp_path, include_agents=False)
        assert len(files) == 1
        assert files[0].name == "session.jsonl"

    def test_includes_agents(self, tmp_path):
        (tmp_path / "session.jsonl").write_text("")
        (tmp_path / "agent-sub.jsonl").write_text("")
        files = discover_log_files(tmp_path, include_agents=True)
        assert len(files) == 2

    def test_nonexistent_dir(self, tmp_path):
        assert discover_log_files(tmp_path / "nope") == []

    def test_empty_dir(self, tmp_path):
        assert discover_log_files(tmp_path) == []


class TestParseTimestamp:
    def test_z_suffix(self):
        dt = _parse_timestamp("2026-02-11T10:00:00Z")
        assert dt.year == 2026
        assert dt.tzinfo is not None

    def test_offset(self):
        dt = _parse_timestamp("2026-02-11T10:00:00+02:00")
        assert dt.year == 2026

    def test_no_tz(self):
        dt = _parse_timestamp("2026-02-11T10:00:00")
        assert dt.year == 2026


class TestExtractTextContent:
    def test_text_blocks(self):
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
        result = _extract_text_content(content)
        assert "Hello" in result
        assert "World" in result

    def test_no_text(self):
        content = [{"type": "tool_use", "name": "Read"}]
        result = _extract_text_content(content)
        assert result is None

    def test_not_list(self):
        assert _extract_text_content("string") is None

    def test_empty(self):
        assert _extract_text_content([]) is None


class TestExtractToolUses:
    def test_basic(self):
        content = [{"type": "tool_use", "name": "Read", "input": {"path": "/x"}}]
        tools = _extract_tool_uses(content)
        assert len(tools) == 1
        assert tools[0].name == "Read"

    def test_not_list(self):
        assert _extract_tool_uses("str") == []


class TestExtractToolResults:
    def test_basic(self):
        content = [{"type": "tool_result", "tool_use_id": "tu-1"}]
        results = _extract_tool_results(content, None)
        assert len(results) == 1
        assert results[0].tool_use_id == "tu-1"

    def test_with_mcp_meta(self):
        content = [{"type": "tool_result", "tool_use_id": "tu-1"}]
        meta = {"serverName": "gov-core"}
        results = _extract_tool_results(content, meta)
        assert results[0].server_name == "gov-core"


class TestExtractThinking:
    def test_thinking_blocks(self):
        content = [{"type": "thinking", "thinking": "analyze this"}]
        chars, text = _extract_thinking(content, include=True)
        assert chars == len("analyze this")
        assert text == "analyze this"

    def test_exclude_content(self):
        content = [{"type": "thinking", "thinking": "secret"}]
        chars, text = _extract_thinking(content, include=False)
        assert chars > 0
        assert text is None


class TestParseLogFile:
    def test_basic(self, tmp_path):
        entry = {
            "timestamp": "2026-02-11T10:00:00Z",
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "Hello"}]},
        }
        f = tmp_path / "test.jsonl"
        f.write_text(json.dumps(entry) + "\n")
        entries = list(parse_log_file(f))
        assert len(entries) == 1
        assert entries[0].entry_type == "assistant"

    def test_skips_invalid_json(self, tmp_path):
        f = tmp_path / "test.jsonl"
        f.write_text("not json\n" + json.dumps({
            "timestamp": "2026-02-11T10:00:00Z",
            "type": "user", "message": {},
        }) + "\n")
        entries = list(parse_log_file(f))
        assert len(entries) == 1

    def test_skips_no_timestamp(self, tmp_path):
        f = tmp_path / "test.jsonl"
        f.write_text(json.dumps({"type": "user"}) + "\n")
        entries = list(parse_log_file(f))
        assert len(entries) == 0

    def test_compaction_detection(self, tmp_path):
        entry = {
            "timestamp": "2026-02-11T10:00:00Z",
            "type": "system",
            "compactMetadata": {"reason": "context_limit"},
            "message": {},
        }
        f = tmp_path / "test.jsonl"
        f.write_text(json.dumps(entry) + "\n")
        entries = list(parse_log_file(f))
        assert entries[0].is_compaction is True

    def test_api_error_detection(self, tmp_path):
        entry = {
            "timestamp": "2026-02-11T10:00:00Z",
            "type": "assistant",
            "isApiErrorMessage": True,
            "message": {},
        }
        f = tmp_path / "test.jsonl"
        f.write_text(json.dumps(entry) + "\n")
        entries = list(parse_log_file(f))
        assert entries[0].is_api_error is True


class TestParseLogFileExtended:
    def test_extended_fields(self, tmp_path):
        entry = {
            "timestamp": "2026-02-11T10:00:00Z",
            "type": "assistant",
            "sessionId": "uuid-123",
            "gitBranch": "master",
            "message": {"content": [{"type": "text", "text": "Done"}]},
        }
        f = tmp_path / "test.jsonl"
        f.write_text(json.dumps(entry) + "\n")
        entries = list(parse_log_file_extended(f))
        assert entries[0].session_id == "uuid-123"
        assert entries[0].git_branch == "master"
        assert entries[0].text_content == "Done"
