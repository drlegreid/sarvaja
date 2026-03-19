"""
Unit tests for cc_transcript.py (GAP-SESSION-TRANSCRIPT-001).

Tests the JSONL → TranscriptEntry streaming parser and pagination.
"""

import json
import tempfile
from pathlib import Path

import pytest

from tests.fixtures.cc_jsonl_factory import write_jsonl_temp

from governance.services.cc_transcript import (
    _extract_user_text,
    _extract_tool_result_content,
    _truncate,
    stream_transcript,
    get_transcript_page,
    build_synthetic_transcript,
)
from governance.session_metrics.models import TranscriptEntry


# ---------- _extract_user_text ----------

class TestExtractUserText:
    def test_plain_string(self):
        assert _extract_user_text("hello world") == "hello world"

    def test_text_blocks_list(self):
        blocks = [
            {"type": "text", "text": "first"},
            {"type": "text", "text": "second"},
        ]
        assert _extract_user_text(blocks) == "first\nsecond"

    def test_mixed_blocks_filters_non_text(self):
        blocks = [
            {"type": "text", "text": "prompt"},
            {"type": "tool_result", "content": "ignored"},
        ]
        assert _extract_user_text(blocks) == "prompt"

    def test_empty_list_returns_none(self):
        assert _extract_user_text([]) is None

    def test_non_string_non_list(self):
        assert _extract_user_text(42) is None


# ---------- _extract_tool_result_content ----------

class TestExtractToolResultContent:
    def test_string_content(self):
        assert _extract_tool_result_content({"content": "ok"}) == "ok"

    def test_list_content_text_blocks(self):
        block = {"content": [
            {"type": "text", "text": "line1"},
            {"type": "text", "text": "line2"},
        ]}
        assert _extract_tool_result_content(block) == "line1\nline2"

    def test_empty_content(self):
        assert _extract_tool_result_content({}) == ""

    def test_non_string_non_list(self):
        assert _extract_tool_result_content({"content": 123}) == "123"


# ---------- _truncate ----------

class TestTruncate:
    def test_within_limit(self):
        text, truncated = _truncate("short", 100)
        assert text == "short"
        assert not truncated

    def test_exceeds_limit(self):
        text, truncated = _truncate("a" * 100, 10)
        assert truncated
        assert len(text) < 100
        assert "chars truncated" in text

    def test_zero_limit_means_unlimited(self):
        long_text = "x" * 10000
        text, truncated = _truncate(long_text, 0)
        assert text == long_text
        assert not truncated


# ---------- stream_transcript ----------

class TestStreamTranscript:
    def test_user_prompt_extraction(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": "Hello Claude"}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 1
        assert entries[0].entry_type == "user_prompt"
        assert entries[0].content == "Hello Claude"

    def test_user_prompt_with_text_blocks(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": [
                 {"type": "text", "text": "Tell me about Python"},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 1
        assert entries[0].entry_type == "user_prompt"
        assert entries[0].content == "Tell me about Python"

    def test_user_prompt_excluded_when_disabled(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": "secret"}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path, include_user_content=False))
        # Only tool_results would survive, no user_prompt
        assert all(e.entry_type != "user_prompt" for e in entries)

    def test_tool_result_in_user_message(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": [
                 {"type": "tool_result", "tool_use_id": "tu_1",
                  "content": "file contents here"},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 1
        assert entries[0].entry_type == "tool_result"
        assert entries[0].content == "file contents here"
        assert entries[0].tool_use_id == "tu_1"

    def test_tool_result_error_flag(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": [
                 {"type": "tool_result", "tool_use_id": "tu_1",
                  "content": "Command failed", "is_error": True},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert entries[0].is_error is True

    def test_assistant_text_extraction(self):
        lines = [
            {"type": "assistant", "timestamp": "2026-02-15T10:01:00Z",
             "message": {"content": [
                 {"type": "text", "text": "Here is my response."},
             ], "model": "claude-opus-4-6"}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 1
        assert entries[0].entry_type == "assistant_text"
        assert entries[0].content == "Here is my response."
        assert entries[0].model == "claude-opus-4-6"

    def test_tool_use_full_input(self):
        lines = [
            {"type": "assistant", "timestamp": "2026-02-15T10:01:00Z",
             "message": {"content": [
                 {"type": "tool_use", "id": "tu_2", "name": "Bash",
                  "input": {"command": "ls -la"}},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 1
        assert entries[0].entry_type == "tool_use"
        assert entries[0].tool_name == "Bash"
        assert "ls -la" in entries[0].content
        assert not entries[0].is_mcp

    def test_mcp_tool_use(self):
        lines = [
            {"type": "assistant", "timestamp": "2026-02-15T10:01:00Z",
             "message": {"content": [
                 {"type": "tool_use", "id": "tu_3", "name": "mcp__gov-tasks__task_create",
                  "input": {"description": "New task"}},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert entries[0].is_mcp is True
        assert entries[0].tool_name == "mcp__gov-tasks__task_create"

    def test_thinking_block(self):
        lines = [
            {"type": "assistant", "timestamp": "2026-02-15T10:01:00Z",
             "message": {"content": [
                 {"type": "thinking", "thinking": "Let me analyze this..."},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 1
        assert entries[0].entry_type == "thinking"
        assert "analyze" in entries[0].content

    def test_thinking_excluded_when_disabled(self):
        lines = [
            {"type": "assistant", "timestamp": "2026-02-15T10:01:00Z",
             "message": {"content": [
                 {"type": "thinking", "thinking": "secret thoughts"},
                 {"type": "text", "text": "visible response"},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path, include_thinking=False))
        assert len(entries) == 1
        assert entries[0].entry_type == "assistant_text"

    def test_compaction_marker(self):
        lines = [
            {"type": "system", "timestamp": "2026-02-15T10:30:00Z",
             "compactMetadata": {"tokens": 5000},
             "message": {"content": "compaction"}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 1
        assert entries[0].entry_type == "compaction"
        assert "compacted" in entries[0].content

    def test_skips_non_conversation_types(self):
        lines = [
            {"type": "progress", "timestamp": "2026-02-15T10:00:00Z"},
            {"type": "file-history-snapshot", "timestamp": "2026-02-15T10:00:00Z"},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 0

    def test_empty_file(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        f.close()
        entries = list(stream_transcript(Path(f.name)))
        assert len(entries) == 0

    def test_truncation_applied(self):
        long_content = "x" * 5000
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": long_content}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path, content_limit=100))
        assert entries[0].is_truncated is True
        assert entries[0].content_length == 5000
        assert len(entries[0].content) < 5000

    def test_max_entries_limit(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": f"msg {i}"},
            }
            for i in range(10)
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path, max_entries=3))
        assert len(entries) == 3

    def test_start_index_skip(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": f"msg {i}"},
            }
            for i in range(5)
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path, start_index=3))
        assert len(entries) == 2
        assert entries[0].index == 3


# ---------- get_transcript_page ----------

class TestGetTranscriptPage:
    def test_basic_pagination(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": f"msg {i}"},
            }
            for i in range(10)
        ]
        path = write_jsonl_temp(lines)
        result = get_transcript_page(path, page=1, per_page=3)
        assert len(result["entries"]) == 3
        assert result["total"] == 10
        assert result["has_more"] is True
        assert result["page"] == 1

    def test_last_page(self):
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": f"msg {i}"},
            }
            for i in range(5)
        ]
        path = write_jsonl_temp(lines)
        result = get_transcript_page(path, page=2, per_page=3)
        assert len(result["entries"]) == 2
        assert result["has_more"] is False

    def test_empty_file_returns_zero_total(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        f.close()
        result = get_transcript_page(Path(f.name))
        assert result["total"] == 0
        assert result["entries"] == []


# ---------- TranscriptEntry.to_dict ----------

class TestTranscriptEntryToDict:
    def test_minimal_fields(self):
        entry = TranscriptEntry(
            index=0, timestamp="2026-02-15T10:00:00Z",
            entry_type="user_prompt", content="hi",
            content_length=2,
        )
        d = entry.to_dict()
        assert d["index"] == 0
        assert d["entry_type"] == "user_prompt"
        assert d["content"] == "hi"
        assert "model" not in d
        assert "tool_name" not in d

    def test_optional_fields_included(self):
        entry = TranscriptEntry(
            index=1, timestamp="2026-02-15T10:00:00Z",
            entry_type="tool_use", content="{}",
            content_length=2, tool_name="Bash",
            tool_use_id="tu_1", is_mcp=True,
            is_error=True, server_name="gov-core",
        )
        d = entry.to_dict()
        assert d["tool_name"] == "Bash"
        assert d["tool_use_id"] == "tu_1"
        assert d["is_mcp"] is True
        assert d["is_error"] is True
        assert d["server_name"] == "gov-core"

    def test_full_conversation_flow(self):
        """Test a realistic multi-message conversation."""
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": "Run the tests"}},
            {"type": "assistant", "timestamp": "2026-02-15T10:00:05Z",
             "message": {"content": [
                 {"type": "thinking", "thinking": "I need to run pytest"},
                 {"type": "text", "text": "Running the tests now."},
                 {"type": "tool_use", "id": "tu_1", "name": "Bash",
                  "input": {"command": "pytest tests/ -q"}},
             ], "model": "claude-opus-4-6"}},
            {"type": "user", "timestamp": "2026-02-15T10:00:10Z",
             "message": {"content": [
                 {"type": "tool_result", "tool_use_id": "tu_1",
                  "content": "5 passed"},
             ]}},
            {"type": "assistant", "timestamp": "2026-02-15T10:00:12Z",
             "message": {"content": [
                 {"type": "text", "text": "All 5 tests passed!"},
             ], "model": "claude-opus-4-6"}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))

        types = [e.entry_type for e in entries]
        assert types == [
            "user_prompt", "thinking", "assistant_text",
            "tool_use", "tool_result", "assistant_text",
        ]
        # Verify tool_use has full input
        tool_entry = [e for e in entries if e.entry_type == "tool_use"][0]
        assert "pytest tests/ -q" in tool_entry.content
        # Verify tool_result has output
        result_entry = [e for e in entries if e.entry_type == "tool_result"][0]
        assert "5 passed" in result_entry.content


# ---------- mixed content user messages ----------

class TestMixedUserContent:
    def test_user_text_and_tool_result(self):
        """User message with both text prompt and tool_result blocks."""
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": [
                 {"type": "text", "text": "Here is context"},
                 {"type": "tool_result", "tool_use_id": "tu_1",
                  "content": "output data"},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 2
        assert entries[0].entry_type == "user_prompt"
        assert entries[1].entry_type == "tool_result"

    def test_tool_result_with_mcp_meta(self):
        """Tool result with mcpMeta.serverName attached."""
        lines = [
            {"type": "user", "timestamp": "2026-02-15T10:00:00Z",
             "mcpMeta": {"serverName": "gov-core"},
             "message": {"content": [
                 {"type": "tool_result", "tool_use_id": "tu_1",
                  "content": "rule data"},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert entries[0].server_name == "gov-core"

    def test_skips_empty_assistant_text(self):
        """Assistant text blocks with only whitespace are skipped."""
        lines = [
            {"type": "assistant", "timestamp": "2026-02-15T10:00:00Z",
             "message": {"content": [
                 {"type": "text", "text": "   \n  "},
                 {"type": "text", "text": "Real content"},
             ]}},
        ]
        path = write_jsonl_temp(lines)
        entries = list(stream_transcript(path))
        assert len(entries) == 1
        assert entries[0].content == "Real content"


# ---------- build_synthetic_transcript ----------

class TestBuildSyntheticTranscript:
    """Tests for synthetic transcript from _sessions_store data."""

    def test_empty_session_data(self):
        result = build_synthetic_transcript({})
        assert result["entries"] == []
        assert result["total"] == 0
        assert result["source"] == "synthetic"

    def test_tool_calls_produce_use_and_result_pairs(self):
        data = {"tool_calls": [
            {"tool_name": "Bash", "arguments": {"command": "ls"},
             "result": "file1.py\nfile2.py", "success": True,
             "timestamp": "2026-02-15T10:00:00"},
        ]}
        result = build_synthetic_transcript(data)
        assert result["total"] == 2
        assert result["entries"][0]["entry_type"] == "tool_use"
        assert result["entries"][0]["tool_name"] == "Bash"
        assert "ls" in result["entries"][0]["content"]
        assert result["entries"][1]["entry_type"] == "tool_result"
        assert "file1.py" in result["entries"][1]["content"]

    def test_mcp_tool_detected(self):
        data = {"tool_calls": [
            {"tool_name": "mcp__gov-core__rules_query", "arguments": {},
             "result": "ok", "success": True, "timestamp": "2026-02-15T10:00:00"},
        ]}
        result = build_synthetic_transcript(data)
        assert result["entries"][0]["is_mcp"] is True

    def test_failed_tool_marked_as_error(self):
        data = {"tool_calls": [
            {"tool_name": "Bash", "arguments": {"command": "fail"},
             "result": "error", "success": False, "timestamp": "2026-02-15T10:00:00"},
        ]}
        result = build_synthetic_transcript(data)
        assert result["entries"][1]["is_error"] is True

    def test_thoughts_included(self):
        data = {"thoughts": [
            {"thought": "Analyzing the bug...", "thought_type": "reasoning",
             "timestamp": "2026-02-15T10:00:00"},
        ]}
        result = build_synthetic_transcript(data)
        assert result["total"] == 1
        assert result["entries"][0]["entry_type"] == "thinking"
        assert "Analyzing" in result["entries"][0]["content"]

    def test_thoughts_excluded_when_disabled(self):
        data = {"thoughts": [
            {"thought": "secret", "timestamp": "2026-02-15T10:00:00"},
        ]}
        result = build_synthetic_transcript(data, include_thinking=False)
        assert result["total"] == 0

    def test_sorted_chronologically(self):
        data = {
            "tool_calls": [
                {"tool_name": "B", "arguments": {}, "result": "ok",
                 "success": True, "timestamp": "2026-02-15T10:02:00"},
            ],
            "thoughts": [
                {"thought": "first", "timestamp": "2026-02-15T10:01:00"},
            ],
        }
        result = build_synthetic_transcript(data)
        assert result["entries"][0]["entry_type"] == "thinking"
        assert result["entries"][1]["entry_type"] == "tool_use"

    def test_pagination(self):
        data = {"tool_calls": [
            {"tool_name": f"T{i}", "arguments": {}, "result": "ok",
             "success": True, "timestamp": f"2026-02-15T10:{i:02d}:00"}
            for i in range(5)
        ]}
        # 5 calls × 2 entries each = 10 total
        result = build_synthetic_transcript(data, page=1, per_page=4)
        assert len(result["entries"]) == 4
        assert result["total"] == 10
        assert result["has_more"] is True

        result2 = build_synthetic_transcript(data, page=3, per_page=4)
        assert len(result2["entries"]) == 2
        assert result2["has_more"] is False

    def test_content_truncation(self):
        data = {"tool_calls": [
            {"tool_name": "Bash", "arguments": {"command": "x" * 5000},
             "result": "ok", "success": True, "timestamp": "2026-02-15T10:00:00"},
        ]}
        result = build_synthetic_transcript(data, content_limit=100)
        assert result["entries"][0]["is_truncated"] is True
        assert result["entries"][0]["content_length"] > 100

    def test_indexes_sequential(self):
        data = {"tool_calls": [
            {"tool_name": "A", "arguments": {}, "result": "ok",
             "success": True, "timestamp": "2026-02-15T10:00:00"},
            {"tool_name": "B", "arguments": {}, "result": "ok",
             "success": True, "timestamp": "2026-02-15T10:01:00"},
        ]}
        result = build_synthetic_transcript(data)
        indexes = [e["index"] for e in result["entries"]]
        assert indexes == [0, 1, 2, 3]

    def test_null_result_handled(self):
        data = {"tool_calls": [
            {"tool_name": "Bash", "arguments": {}, "result": None,
             "success": True, "timestamp": "2026-02-15T10:00:00"},
        ]}
        result = build_synthetic_transcript(data)
        assert result["entries"][1]["content"] == ""
        assert result["entries"][1]["content_length"] == 0
