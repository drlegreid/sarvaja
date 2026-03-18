"""Tests for session content validator (deep JSONL integrity).

TDD-first: These tests define the contract for SessionContentValidator,
which validates real Claude Code session JSONL data for:
- Tool call / tool result pairing (orphaned calls, missing results)
- MCP tool calls with server metadata
- Thinking blocks with actual content
- Timestamp consistency
- Session completeness metrics

Per TEST-E2E-01-v1: Tier 1 unit tests for content validation logic.
"""

import json
import tempfile
from pathlib import Path

import pytest

from governance.services.session_content_validator import (
    ContentValidationResult,
    ValidationIssue,
    validate_session_content,
)


def _write_jsonl(lines: list[dict], path: Path) -> None:
    """Helper: write list of dicts as JSONL file."""
    with open(path, "w") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")


def _make_assistant_entry(
    content_blocks: list[dict],
    timestamp: str = "2026-02-20T10:00:00.000Z",
    model: str = "claude-opus-4-6",
    mcp_meta: dict | None = None,
) -> dict:
    """Helper: build an assistant JSONL entry."""
    entry = {
        "type": "assistant",
        "timestamp": timestamp,
        "uuid": "ast-001",
        "sessionId": "test-uuid",
        "message": {
            "role": "assistant",
            "model": model,
            "content": content_blocks,
            "usage": {"input_tokens": 10, "output_tokens": 20},
        },
    }
    if mcp_meta:
        entry["mcpMeta"] = mcp_meta
    return entry


def _make_user_entry(
    content, timestamp: str = "2026-02-20T10:00:01.000Z",
    mcp_meta: dict | None = None,
) -> dict:
    """Helper: build a user JSONL entry."""
    entry = {
        "type": "user",
        "timestamp": timestamp,
        "uuid": "usr-001",
        "sessionId": "test-uuid",
        "message": {"role": "user", "content": content},
    }
    if mcp_meta:
        entry["mcpMeta"] = mcp_meta
    return entry


def _make_tool_use(tool_id: str, name: str, input_data: dict | None = None) -> dict:
    return {
        "type": "tool_use",
        "id": tool_id,
        "name": name,
        "input": input_data or {},
    }


def _make_tool_result(tool_id: str, content: str = "result", is_error: bool = False) -> dict:
    return {
        "type": "tool_result",
        "tool_use_id": tool_id,
        "content": content,
        "is_error": is_error,
    }


def _make_thinking(text: str) -> dict:
    return {"type": "thinking", "thinking": text}


class TestValidateSessionContent:
    """Tests for validate_session_content() — the main entry point."""

    def test_returns_result_object(self, tmp_path):
        """Should return a ContentValidationResult dataclass."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([], jsonl)
        result = validate_session_content(str(jsonl))
        assert isinstance(result, ContentValidationResult)

    def test_empty_file_returns_valid_with_warning(self, tmp_path):
        """Empty JSONL should return valid=True with a warning issue."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.valid is True
        assert result.entry_count == 0
        assert any(i.severity == "warning" and "empty" in i.message.lower() for i in result.issues)

    def test_nonexistent_file_returns_error(self):
        """Non-existent file should return valid=False with error."""
        result = validate_session_content("/tmp/does-not-exist.jsonl")
        assert result.valid is False
        assert any(i.severity == "error" and "not found" in i.message.lower() for i in result.issues)


class TestToolCallResultPairing:
    """Tool call / result pairing validation."""

    def test_matched_tool_call_and_result(self, tmp_path):
        """A tool_use followed by matching tool_result = no issues."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([_make_tool_use("t1", "Read", {"file_path": "/a.py"})]),
            _make_user_entry([_make_tool_result("t1", "file contents here")]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.tool_calls_total == 1
        assert result.tool_results_total == 1
        assert result.orphaned_tool_calls == 0
        assert result.orphaned_tool_results == 0

    def test_orphaned_tool_call_no_result(self, tmp_path):
        """A tool_use with no matching tool_result = orphaned call."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([_make_tool_use("t1", "Bash", {"command": "ls"})]),
            # No user entry with tool_result for t1
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.orphaned_tool_calls == 1
        assert any(
            i.check == "tool_call_result_pairing" and "t1" in i.message
            for i in result.issues
        )

    def test_orphaned_tool_result_no_call(self, tmp_path):
        """A tool_result with no prior tool_use = orphaned result."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_user_entry([_make_tool_result("t999", "some result")]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.orphaned_tool_results == 1
        assert any(
            i.check == "tool_call_result_pairing" and "t999" in i.message
            for i in result.issues
        )

    def test_multiple_tool_calls_all_matched(self, tmp_path):
        """Multiple tool calls all with matching results."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([
                _make_tool_use("t1", "Read", {"file_path": "/a.py"}),
                _make_tool_use("t2", "Glob", {"pattern": "*.py"}),
            ]),
            _make_user_entry([
                _make_tool_result("t1", "contents of a.py"),
                _make_tool_result("t2", "file1.py\nfile2.py"),
            ]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.tool_calls_total == 2
        assert result.tool_results_total == 2
        assert result.orphaned_tool_calls == 0
        assert result.orphaned_tool_results == 0

    def test_partial_match_one_orphaned(self, tmp_path):
        """Two tool_uses but only one tool_result."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([
                _make_tool_use("t1", "Read"),
                _make_tool_use("t2", "Write"),
            ]),
            _make_user_entry([_make_tool_result("t1", "ok")]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.orphaned_tool_calls == 1

    def test_tool_result_with_empty_content(self, tmp_path):
        """Tool result with empty content string should be flagged."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([_make_tool_use("t1", "Bash")]),
            _make_user_entry([_make_tool_result("t1", "")]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert any(
            i.check == "empty_tool_result" and "t1" in i.message
            for i in result.issues
        )

    def test_tool_result_error_flagged(self, tmp_path):
        """Tool result with is_error=True should be counted."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([_make_tool_use("t1", "Bash")]),
            _make_user_entry([_make_tool_result("t1", "Error: command failed", is_error=True)]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.tool_errors == 1


class TestMCPCallValidation:
    """MCP service call validation."""

    def test_mcp_call_with_server_metadata(self, tmp_path):
        """MCP tool call with mcpMeta.serverName = valid."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry(
                [_make_tool_use("t1", "mcp__gov-core__rules_query", {"tags": ["TEST"]})],
            ),
            _make_user_entry(
                [_make_tool_result("t1", "[{rule}]")],
                mcp_meta={"serverName": "gov-core"},
            ),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.mcp_calls_total == 1
        assert result.mcp_calls_with_server == 1
        assert result.mcp_calls_without_server == 0

    def test_mcp_call_derives_server_from_tool_name(self, tmp_path):
        """MCP tool call without mcpMeta but standard name = server derived."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry(
                [_make_tool_use("t1", "mcp__gov-tasks__task_create")],
            ),
            _make_user_entry([_make_tool_result("t1", "created")]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.mcp_calls_total == 1
        # Server derived from tool name: mcp__gov-tasks__task_create → gov-tasks
        assert result.mcp_calls_with_server == 1
        assert result.mcp_server_distribution == {"gov-tasks": 1}

    def test_mcp_call_without_derivable_name_flagged(self, tmp_path):
        """MCP tool call with non-standard name = flagged."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry(
                [_make_tool_use("t1", "mcp__unknown")],  # Only 2 parts, not 3
            ),
            _make_user_entry([_make_tool_result("t1", "created")]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.mcp_calls_total == 1
        assert result.mcp_calls_without_server == 1
        assert any(
            i.check == "mcp_server_metadata" and "mcp__unknown" in i.message
            for i in result.issues
        )

    def test_non_mcp_tool_not_counted(self, tmp_path):
        """Non-MCP tools (Read, Write, Bash) should not count as MCP calls."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([_make_tool_use("t1", "Read")]),
            _make_user_entry([_make_tool_result("t1", "file content")]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.mcp_calls_total == 0

    def test_mcp_server_distribution(self, tmp_path):
        """Track which MCP servers were called and how often."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([_make_tool_use("t1", "mcp__gov-core__rules_query")]),
            _make_user_entry([_make_tool_result("t1", "ok")]),
            _make_assistant_entry(
                [_make_tool_use("t2", "mcp__gov-tasks__task_create")],
                timestamp="2026-02-20T10:01:00.000Z",
            ),
            _make_user_entry(
                [_make_tool_result("t2", "ok")],
                timestamp="2026-02-20T10:01:01.000Z",
            ),
            _make_assistant_entry(
                [_make_tool_use("t3", "mcp__gov-core__rule_get")],
                timestamp="2026-02-20T10:02:00.000Z",
            ),
            _make_user_entry(
                [_make_tool_result("t3", "ok")],
                timestamp="2026-02-20T10:02:01.000Z",
            ),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        # Server names derived from tool names (mcp__{server}__{method})
        assert result.mcp_server_distribution == {"gov-core": 2, "gov-tasks": 1}


class TestThinkingValidation:
    """Claude thinking block validation."""

    def test_thinking_with_content(self, tmp_path):
        """Thinking block with real content = counted, no issue."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([
                _make_thinking("Let me analyze the requirements here..."),
                {"type": "text", "text": "I'll help with that."},
            ]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.thinking_blocks_total == 1
        assert result.thinking_blocks_empty == 0
        assert result.thinking_chars_total > 0

    def test_thinking_empty_string(self, tmp_path):
        """Thinking block with empty string = flagged."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([
                _make_thinking(""),
                {"type": "text", "text": "Here's the answer."},
            ]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.thinking_blocks_empty == 1
        assert any(i.check == "empty_thinking" for i in result.issues)

    def test_multiple_thinking_blocks_counted(self, tmp_path):
        """Multiple thinking blocks across entries are aggregated."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([_make_thinking("First thought")]),
            _make_assistant_entry([
                _make_thinking("Second thought"),
                _make_thinking("Third thought"),
            ], timestamp="2026-02-20T10:01:00.000Z"),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.thinking_blocks_total == 3


class TestTimestampValidation:
    """Timestamp consistency checks."""

    def test_valid_timestamps(self, tmp_path):
        """All entries with valid ISO timestamps = no issues."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry(
                [{"type": "text", "text": "hello"}],
                timestamp="2026-02-20T10:00:00.000Z",
            ),
            _make_user_entry("thanks", timestamp="2026-02-20T10:00:05.000Z"),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert not any(i.check == "timestamp_order" for i in result.issues)

    def test_missing_timestamp(self, tmp_path):
        """Entry with missing timestamp = flagged."""
        jsonl = tmp_path / "session.jsonl"
        entry = _make_assistant_entry([{"type": "text", "text": "hello"}])
        del entry["timestamp"]
        _write_jsonl([entry], jsonl)
        result = validate_session_content(str(jsonl))
        assert any(i.check == "missing_timestamp" for i in result.issues)

    def test_non_monotonic_timestamps(self, tmp_path):
        """Timestamps going backwards = flagged."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry(
                [{"type": "text", "text": "first"}],
                timestamp="2026-02-20T10:05:00.000Z",
            ),
            _make_user_entry("second", timestamp="2026-02-20T10:00:00.000Z"),  # Earlier!
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert any(i.check == "timestamp_order" for i in result.issues)


class TestSessionCompleteness:
    """Overall session completeness metrics."""

    def test_completeness_summary(self, tmp_path):
        """Full session with all element types produces complete summary."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_user_entry("Please read the file"),
            _make_assistant_entry([
                _make_thinking("I need to read the file first"),
                _make_tool_use("t1", "Read", {"file_path": "/app.py"}),
            ]),
            _make_user_entry(
                [_make_tool_result("t1", "def main(): pass")],
                timestamp="2026-02-20T10:00:02.000Z",
            ),
            _make_assistant_entry(
                [{"type": "text", "text": "The file contains a main function."}],
                timestamp="2026-02-20T10:00:03.000Z",
            ),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        assert result.entry_count == 4
        assert result.user_messages >= 1
        assert result.assistant_messages >= 1
        assert result.tool_calls_total == 1
        assert result.tool_results_total == 1
        assert result.thinking_blocks_total == 1
        assert result.has_user_messages is True
        assert result.has_assistant_messages is True
        assert result.has_tool_calls is True
        assert result.has_thinking is True

    def test_malformed_json_lines_skipped(self, tmp_path):
        """Malformed JSON lines should be skipped with warning, not crash."""
        jsonl = tmp_path / "session.jsonl"
        with open(jsonl, "w") as f:
            f.write('{"type": "assistant", "timestamp": "2026-02-20T10:00:00Z", '
                    '"message": {"content": [{"type": "text", "text": "ok"}]}}\n')
            f.write('THIS IS NOT JSON\n')
            f.write('{"type": "user", "timestamp": "2026-02-20T10:00:01Z", '
                    '"message": {"content": "thanks"}}\n')
        result = validate_session_content(str(jsonl))
        assert result.entry_count == 2  # Skipped the bad line
        assert result.parse_errors == 1
        assert any(i.check == "json_parse" for i in result.issues)

    def test_to_dict_serializable(self, tmp_path):
        """Result.to_dict() should be JSON-serializable."""
        jsonl = tmp_path / "session.jsonl"
        _write_jsonl([
            _make_assistant_entry([{"type": "text", "text": "hello"}]),
        ], jsonl)
        result = validate_session_content(str(jsonl))
        d = result.to_dict()
        assert isinstance(d, dict)
        # Should not raise
        json.dumps(d)
        assert "valid" in d
        assert "issues" in d
        assert "tool_calls_total" in d


class TestValidationIssueModel:
    """Tests for the ValidationIssue dataclass."""

    def test_issue_fields(self):
        issue = ValidationIssue(
            check="tool_call_result_pairing",
            severity="warning",
            message="Tool call t1 (Read) has no matching result",
            line_number=5,
        )
        assert issue.check == "tool_call_result_pairing"
        assert issue.severity == "warning"
        assert issue.line_number == 5

    def test_issue_to_dict(self):
        issue = ValidationIssue(
            check="mcp_server_metadata",
            severity="info",
            message="MCP call missing server info",
        )
        d = issue.to_dict()
        assert d["check"] == "mcp_server_metadata"
        assert d["severity"] == "info"
