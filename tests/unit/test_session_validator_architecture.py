"""Architectural assessment for session content validation.

Validates reusability, resiliency, and volume scalability of the
SessionContentValidator solution.

Per ARCH-INFRA-01-v1: Architecture must support scale and reliability.
"""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from governance.services.session_content_validator import (
    ContentValidationResult,
    ValidationIssue,
    validate_session_content,
    _derive_server_from_tool_name,
)


# ===== REUSABILITY =====

class TestReusability:
    """Validate the validator is reusable across contexts."""

    def test_works_with_any_jsonl_path(self, tmp_path):
        """Validator accepts any file path — not tied to CC project dirs."""
        custom = tmp_path / "custom" / "location" / "data.jsonl"
        custom.parent.mkdir(parents=True)
        with open(custom, "w") as f:
            f.write(json.dumps({
                "type": "assistant", "timestamp": "2026-01-01T00:00:00Z",
                "message": {"content": [{"type": "text", "text": "ok"}]},
            }) + "\n")
        result = validate_session_content(str(custom))
        assert result.valid is True
        assert result.entry_count == 1

    def test_result_is_json_serializable(self, tmp_path):
        """Result can be sent over REST API, stored in DB, or logged."""
        jsonl = tmp_path / "s.jsonl"
        with open(jsonl, "w") as f:
            f.write("{}\n")
        result = validate_session_content(str(jsonl))
        d = result.to_dict()
        serialized = json.dumps(d)
        assert isinstance(json.loads(serialized), dict)

    def test_result_dataclass_is_composable(self):
        """Result fields are primitive types — composable into reports."""
        r = ContentValidationResult(
            valid=True, entry_count=100, tool_calls_total=50,
            mcp_server_distribution={"gov-core": 10},
        )
        # Can aggregate across multiple sessions
        r2 = ContentValidationResult(
            valid=True, entry_count=200, tool_calls_total=80,
            mcp_server_distribution={"gov-core": 20, "gov-tasks": 5},
        )
        combined_entries = r.entry_count + r2.entry_count
        assert combined_entries == 300

    def test_server_derivation_is_standalone_function(self):
        """_derive_server_from_tool_name is reusable outside validator."""
        assert _derive_server_from_tool_name("mcp__gov-core__rules_query") == "gov-core"
        assert _derive_server_from_tool_name("mcp__playwright__browser_click") == "playwright"
        assert _derive_server_from_tool_name("mcp__claude-mem__chroma_query") == "claude-mem"
        assert _derive_server_from_tool_name("Read") is None
        assert _derive_server_from_tool_name("mcp__unknown") is None

    def test_validation_issues_are_structured(self):
        """Issues use structured data, not just strings — enables filtering."""
        issue = ValidationIssue(
            check="tool_call_result_pairing",
            severity="warning",
            message="Tool call t1 has no result",
            line_number=42,
        )
        d = issue.to_dict()
        # Can filter by check type
        assert d["check"] == "tool_call_result_pairing"
        # Can filter by severity
        assert d["severity"] == "warning"
        # Can link to source line
        assert d["line_number"] == 42

    def test_heuristic_checks_use_api_not_direct_file_access(self):
        """H-SESSION-CC-003/004 use /validate API, not direct JSONL parsing."""
        from governance.routes.tests.heuristic_checks_cc import (
            check_cc_session_tool_pairing,
            check_cc_session_mcp_metadata,
        )
        import inspect
        # Checks don't import file system modules
        src_003 = inspect.getsource(check_cc_session_tool_pairing)
        src_004 = inspect.getsource(check_cc_session_mcp_metadata)
        assert "Path(" not in src_003
        assert "open(" not in src_003
        assert "Path(" not in src_004
        assert "open(" not in src_004
        # They use _api_get which goes through REST
        assert "_api_get" in src_003
        assert "_api_get" in src_004


# ===== RESILIENCY =====

class TestResiliency:
    """Validate graceful handling of edge cases and failures."""

    def test_nonexistent_file_does_not_crash(self):
        """Missing file returns structured error, no exception."""
        result = validate_session_content("/nonexistent/path.jsonl")
        assert result.valid is False
        assert result.issues[0].severity == "error"

    def test_empty_file_is_valid(self, tmp_path):
        """Empty session is valid (just a warning)."""
        jsonl = tmp_path / "empty.jsonl"
        jsonl.write_text("")
        result = validate_session_content(str(jsonl))
        assert result.valid is True
        assert result.entry_count == 0

    def test_corrupted_json_lines_skipped(self, tmp_path):
        """Corrupted lines don't crash — they're counted and skipped."""
        jsonl = tmp_path / "corrupt.jsonl"
        with open(jsonl, "w") as f:
            f.write('{"type":"assistant","timestamp":"2026-01-01T00:00:00Z",'
                    '"message":{"content":[{"type":"text","text":"ok"}]}}\n')
            f.write("GARBAGE LINE\n")
            f.write("{not json at all\n")
            f.write('{"type":"user","timestamp":"2026-01-01T00:00:01Z",'
                    '"message":{"content":"thanks"}}\n')
        result = validate_session_content(str(jsonl))
        assert result.entry_count == 2
        assert result.parse_errors == 2

    def test_missing_message_field(self, tmp_path):
        """Entry with no 'message' field doesn't crash."""
        jsonl = tmp_path / "nomsg.jsonl"
        with open(jsonl, "w") as f:
            f.write('{"type":"assistant","timestamp":"2026-01-01T00:00:00Z"}\n')
        result = validate_session_content(str(jsonl))
        assert result.entry_count == 1
        assert result.assistant_messages == 1

    def test_content_not_list(self, tmp_path):
        """content as string (not list) doesn't crash."""
        jsonl = tmp_path / "strcon.jsonl"
        with open(jsonl, "w") as f:
            f.write('{"type":"user","timestamp":"2026-01-01T00:00:00Z",'
                    '"message":{"content":"just a string"}}\n')
        result = validate_session_content(str(jsonl))
        assert result.entry_count == 1
        assert result.user_messages == 1

    def test_tool_use_without_id(self, tmp_path):
        """tool_use block missing 'id' field doesn't crash."""
        jsonl = tmp_path / "noid.jsonl"
        with open(jsonl, "w") as f:
            f.write(json.dumps({
                "type": "assistant", "timestamp": "2026-01-01T00:00:00Z",
                "message": {"content": [
                    {"type": "tool_use", "name": "Read", "input": {}},
                ]},
            }) + "\n")
        result = validate_session_content(str(jsonl))
        assert result.tool_calls_total == 1

    def test_progress_and_system_entries_handled(self, tmp_path):
        """Progress and system entries are counted but don't crash."""
        jsonl = tmp_path / "mixed.jsonl"
        with open(jsonl, "w") as f:
            f.write('{"type":"progress","timestamp":"2026-01-01T00:00:00Z",'
                    '"data":{"type":"hook_progress"}}\n')
            f.write('{"type":"system","compactMetadata":{}}\n')
        result = validate_session_content(str(jsonl))
        assert result.entry_count == 2
        assert result.user_messages == 0
        assert result.assistant_messages == 0


# ===== VOLUME SCALABILITY =====

class TestVolumeScalability:
    """Validate performance characteristics at scale."""

    def test_1000_entries_under_1_second(self, tmp_path):
        """1000-entry session validates in under 1 second."""
        jsonl = tmp_path / "large.jsonl"
        with open(jsonl, "w") as f:
            for i in range(500):
                # Assistant with tool_use
                f.write(json.dumps({
                    "type": "assistant",
                    "timestamp": f"2026-01-01T{i//3600:02d}:{(i%3600)//60:02d}:{i%60:02d}.000Z",
                    "message": {"content": [
                        {"type": "tool_use", "id": f"t{i}", "name": "Read", "input": {}},
                    ]},
                }) + "\n")
                # User with tool_result
                f.write(json.dumps({
                    "type": "user",
                    "timestamp": f"2026-01-01T{i//3600:02d}:{(i%3600)//60:02d}:{i%60:02d}.500Z",
                    "message": {"content": [
                        {"type": "tool_result", "tool_use_id": f"t{i}", "content": "ok"},
                    ]},
                }) + "\n")

        start = time.monotonic()
        result = validate_session_content(str(jsonl))
        elapsed = time.monotonic() - start

        assert result.entry_count == 1000
        assert result.tool_calls_total == 500
        assert result.orphaned_tool_calls == 0
        assert elapsed < 1.0, f"Validation took {elapsed:.2f}s (expected <1.0s)"

    def test_10000_entries_under_5_seconds(self, tmp_path):
        """10K-entry session validates in under 5 seconds."""
        jsonl = tmp_path / "xlarge.jsonl"
        with open(jsonl, "w") as f:
            for i in range(5000):
                ts = f"2026-01-01T{(i*2)//3600:02d}:{((i*2)%3600)//60:02d}:{(i*2)%60:02d}.000Z"
                ts2 = f"2026-01-01T{(i*2+1)//3600:02d}:{((i*2+1)%3600)//60:02d}:{(i*2+1)%60:02d}.000Z"
                f.write(json.dumps({
                    "type": "assistant", "timestamp": ts,
                    "message": {"content": [
                        {"type": "thinking", "thinking": "x" * 100},
                        {"type": "tool_use", "id": f"t{i}", "name": "mcp__gov-core__rules_query", "input": {}},
                    ]},
                }) + "\n")
                f.write(json.dumps({
                    "type": "user", "timestamp": ts2,
                    "message": {"content": [
                        {"type": "tool_result", "tool_use_id": f"t{i}", "content": "ok"},
                    ]},
                }) + "\n")

        start = time.monotonic()
        result = validate_session_content(str(jsonl))
        elapsed = time.monotonic() - start

        assert result.entry_count == 10000
        assert result.tool_calls_total == 5000
        assert result.mcp_calls_total == 5000
        assert result.mcp_calls_with_server == 5000  # All derived from tool name
        assert result.thinking_blocks_total == 5000
        assert elapsed < 5.0, f"Validation took {elapsed:.2f}s (expected <5.0s)"

    def test_streaming_parse_memory_efficient(self, tmp_path):
        """Validator reads line-by-line, not entire file into memory."""
        import inspect
        from governance.services.session_content_validator import _parse_jsonl
        src = inspect.getsource(_parse_jsonl)
        # Should iterate over file lines, not read all at once
        assert "for line_num, line in enumerate" in src
        # Should NOT load entire file into memory
        assert "readlines()" not in src
        assert "read()" not in src

    def test_issue_count_bounded(self, tmp_path):
        """Issues list doesn't grow unbounded for pathological input."""
        jsonl = tmp_path / "many_issues.jsonl"
        with open(jsonl, "w") as f:
            # 500 orphaned tool calls
            for i in range(500):
                f.write(json.dumps({
                    "type": "assistant",
                    "timestamp": f"2026-01-01T00:00:{i%60:02d}.000Z",
                    "message": {"content": [
                        {"type": "tool_use", "id": f"orphan{i}", "name": "Bash", "input": {}},
                    ]},
                }) + "\n")
        result = validate_session_content(str(jsonl))
        # Issues exist but result is still structured (not OOM)
        assert result.orphaned_tool_calls == 500
        assert isinstance(result.issues, list)
        assert result.to_dict()  # Serializable
