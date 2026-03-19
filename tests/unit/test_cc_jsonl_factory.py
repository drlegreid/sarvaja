"""
TDD tests for CC JSONL fixture factory (P2-10d).

Per TEST-FIXTURE-01-v1: Test fixtures MUST match production data format.
Tests written FIRST, factory second.
"""

import json
import uuid
from pathlib import Path

import pytest

from tests.fixtures.cc_jsonl_factory import CCJsonlFactory


# ---------------------------------------------------------------------------
# Factory instantiation
# ---------------------------------------------------------------------------


class TestFactoryDefaults:
    """Factory creates entries with all production fields."""

    def test_factory_has_default_session_id(self):
        f = CCJsonlFactory()
        assert f.session_id  # non-empty UUID string
        # Must be valid UUID format
        uuid.UUID(f.session_id)

    def test_factory_accepts_custom_session_id(self):
        f = CCJsonlFactory(session_id="custom-uuid")
        assert f.session_id == "custom-uuid"

    def test_factory_has_default_cwd(self):
        f = CCJsonlFactory()
        assert f.cwd.startswith("/")

    def test_factory_has_default_version(self):
        f = CCJsonlFactory()
        assert f.version  # non-empty

    def test_factory_has_default_git_branch(self):
        f = CCJsonlFactory()
        assert f.git_branch == "main"


# ---------------------------------------------------------------------------
# User prompt entries
# ---------------------------------------------------------------------------


class TestMakeUserPrompt:
    """make_user_prompt() creates production-format user entries."""

    def setup_method(self):
        self.factory = CCJsonlFactory()

    def test_has_type_user(self):
        entry = self.factory.make_user_prompt("Hello")
        assert entry["type"] == "user"

    def test_has_timestamp(self):
        entry = self.factory.make_user_prompt("Hello")
        assert "timestamp" in entry
        assert "T" in entry["timestamp"]  # ISO-8601

    def test_has_session_id(self):
        entry = self.factory.make_user_prompt("Hello")
        assert entry["sessionId"] == self.factory.session_id

    def test_has_uuid(self):
        entry = self.factory.make_user_prompt("Hello")
        uuid.UUID(entry["uuid"])  # validates format

    def test_has_message_with_content(self):
        entry = self.factory.make_user_prompt("Hello Claude")
        msg = entry["message"]
        assert msg["role"] == "user"
        assert isinstance(msg["content"], list)
        assert msg["content"][0]["type"] == "text"
        assert msg["content"][0]["text"] == "Hello Claude"

    def test_has_cwd(self):
        entry = self.factory.make_user_prompt("Hello")
        assert entry["cwd"] == self.factory.cwd

    def test_has_git_branch(self):
        entry = self.factory.make_user_prompt("Hello")
        assert entry["gitBranch"] == self.factory.git_branch

    def test_has_version(self):
        entry = self.factory.make_user_prompt("Hello")
        assert entry["version"] == self.factory.version

    def test_has_user_type(self):
        entry = self.factory.make_user_prompt("Hello")
        assert entry["userType"] == "external"

    def test_has_parent_uuid(self):
        entry = self.factory.make_user_prompt("Hello")
        assert "parentUuid" in entry

    def test_has_is_sidechain(self):
        entry = self.factory.make_user_prompt("Hello")
        assert entry["isSidechain"] is False

    def test_timestamps_increment(self):
        e1 = self.factory.make_user_prompt("First")
        e2 = self.factory.make_user_prompt("Second")
        assert e1["timestamp"] < e2["timestamp"]


# ---------------------------------------------------------------------------
# Assistant response entries
# ---------------------------------------------------------------------------


class TestMakeAssistantResponse:
    """make_assistant_response() creates production-format assistant entries."""

    def setup_method(self):
        self.factory = CCJsonlFactory()

    def test_has_type_assistant(self):
        entry = self.factory.make_assistant_response("Hello!")
        assert entry["type"] == "assistant"

    def test_has_message_with_model(self):
        entry = self.factory.make_assistant_response("Hello!")
        msg = entry["message"]
        assert msg["model"] == "claude-opus-4-6"
        assert msg["role"] == "assistant"

    def test_has_text_content(self):
        entry = self.factory.make_assistant_response("Hello!")
        content = entry["message"]["content"]
        text_blocks = [b for b in content if b["type"] == "text"]
        assert len(text_blocks) == 1
        assert text_blocks[0]["text"] == "Hello!"

    def test_has_usage(self):
        entry = self.factory.make_assistant_response("Hello!")
        usage = entry["message"]["usage"]
        assert "input_tokens" in usage
        assert "output_tokens" in usage
        assert usage["input_tokens"] > 0
        assert usage["output_tokens"] > 0

    def test_has_stop_reason(self):
        entry = self.factory.make_assistant_response("Hello!")
        assert entry["message"]["stop_reason"] == "end_turn"

    def test_has_request_id(self):
        entry = self.factory.make_assistant_response("Hello!")
        assert entry["requestId"].startswith("req_")

    def test_custom_model(self):
        entry = self.factory.make_assistant_response("Hi", model="claude-sonnet-4-6")
        assert entry["message"]["model"] == "claude-sonnet-4-6"

    def test_has_common_fields(self):
        entry = self.factory.make_assistant_response("Hi")
        assert entry["sessionId"] == self.factory.session_id
        assert entry["cwd"] == self.factory.cwd
        assert entry["gitBranch"] == self.factory.git_branch
        assert "uuid" in entry
        assert "timestamp" in entry


# ---------------------------------------------------------------------------
# Tool use entries (assistant with tool_use content)
# ---------------------------------------------------------------------------


class TestMakeToolUse:
    """make_tool_use() creates assistant entry with tool_use content block."""

    def setup_method(self):
        self.factory = CCJsonlFactory()

    def test_type_is_assistant(self):
        entry = self.factory.make_tool_use("Read", {"file_path": "/tmp/x"})
        assert entry["type"] == "assistant"

    def test_has_tool_use_block(self):
        entry = self.factory.make_tool_use("Read", {"file_path": "/tmp/x"})
        content = entry["message"]["content"]
        tool_blocks = [b for b in content if b["type"] == "tool_use"]
        assert len(tool_blocks) == 1

    def test_tool_use_has_id(self):
        entry = self.factory.make_tool_use("Read", {"file_path": "/tmp/x"})
        tool = [b for b in entry["message"]["content"] if b["type"] == "tool_use"][0]
        assert tool["id"].startswith("toolu_")

    def test_tool_use_has_name_and_input(self):
        entry = self.factory.make_tool_use("Read", {"file_path": "/tmp/x"})
        tool = [b for b in entry["message"]["content"] if b["type"] == "tool_use"][0]
        assert tool["name"] == "Read"
        assert tool["input"] == {"file_path": "/tmp/x"}

    def test_stop_reason_is_tool_use(self):
        entry = self.factory.make_tool_use("Read", {"file_path": "/tmp/x"})
        assert entry["message"]["stop_reason"] == "tool_use"

    def test_mcp_tool_name(self):
        entry = self.factory.make_tool_use(
            "mcp__gov-core__rules_query", {"query": "test"})
        tool = [b for b in entry["message"]["content"] if b["type"] == "tool_use"][0]
        assert tool["name"] == "mcp__gov-core__rules_query"

    def test_returns_tool_use_id(self):
        entry = self.factory.make_tool_use("Read", {"file_path": "/tmp/x"})
        tool = [b for b in entry["message"]["content"] if b["type"] == "tool_use"][0]
        # The id should be retrievable for matching tool_results
        assert len(tool["id"]) > 6


# ---------------------------------------------------------------------------
# Tool result entries (user with tool_result content)
# ---------------------------------------------------------------------------


class TestMakeToolResult:
    """make_tool_result() creates user entry with tool_result content block."""

    def setup_method(self):
        self.factory = CCJsonlFactory()

    def test_type_is_user(self):
        entry = self.factory.make_tool_result("toolu_abc", "file contents")
        assert entry["type"] == "user"

    def test_has_tool_result_block(self):
        entry = self.factory.make_tool_result("toolu_abc", "file contents")
        content = entry["message"]["content"]
        result_blocks = [b for b in content if b["type"] == "tool_result"]
        assert len(result_blocks) == 1

    def test_tool_result_has_matching_id(self):
        entry = self.factory.make_tool_result("toolu_abc", "file contents")
        result = [b for b in entry["message"]["content"]
                  if b["type"] == "tool_result"][0]
        assert result["tool_use_id"] == "toolu_abc"

    def test_tool_result_content(self):
        entry = self.factory.make_tool_result("toolu_abc", "file contents")
        result = [b for b in entry["message"]["content"]
                  if b["type"] == "tool_result"][0]
        assert result["content"] == "file contents"

    def test_tool_result_not_error_by_default(self):
        entry = self.factory.make_tool_result("toolu_abc", "ok")
        result = [b for b in entry["message"]["content"]
                  if b["type"] == "tool_result"][0]
        assert result["is_error"] is False

    def test_tool_result_error_flag(self):
        entry = self.factory.make_tool_result("toolu_abc", "boom", is_error=True)
        result = [b for b in entry["message"]["content"]
                  if b["type"] == "tool_result"][0]
        assert result["is_error"] is True


# ---------------------------------------------------------------------------
# Thinking entries (assistant with thinking content)
# ---------------------------------------------------------------------------


class TestMakeThinking:
    """make_thinking() creates assistant entry with thinking content block."""

    def setup_method(self):
        self.factory = CCJsonlFactory()

    def test_type_is_assistant(self):
        entry = self.factory.make_thinking("Let me analyze this...")
        assert entry["type"] == "assistant"

    def test_has_thinking_block(self):
        entry = self.factory.make_thinking("Let me analyze this...")
        content = entry["message"]["content"]
        think_blocks = [b for b in content if b["type"] == "thinking"]
        assert len(think_blocks) == 1

    def test_thinking_has_text(self):
        entry = self.factory.make_thinking("Let me analyze this...")
        think = [b for b in entry["message"]["content"]
                 if b["type"] == "thinking"][0]
        assert think["thinking"] == "Let me analyze this..."

    def test_thinking_has_signature(self):
        entry = self.factory.make_thinking("Let me analyze this...")
        think = [b for b in entry["message"]["content"]
                 if b["type"] == "thinking"][0]
        assert "signature" in think
        assert len(think["signature"]) > 10


# ---------------------------------------------------------------------------
# Compaction entries
# ---------------------------------------------------------------------------


class TestMakeCompaction:
    """make_compaction() creates system compaction marker."""

    def setup_method(self):
        self.factory = CCJsonlFactory()

    def test_type_is_system(self):
        entry = self.factory.make_compaction()
        assert entry["type"] == "system"

    def test_has_compact_metadata(self):
        entry = self.factory.make_compaction()
        assert "compactMetadata" in entry

    def test_has_timestamp(self):
        entry = self.factory.make_compaction()
        assert "timestamp" in entry


# ---------------------------------------------------------------------------
# Full session generation
# ---------------------------------------------------------------------------


class TestMakeFullSession:
    """make_full_session() creates a complete multi-turn session."""

    def setup_method(self):
        self.factory = CCJsonlFactory()

    def test_returns_list_of_entries(self):
        entries = self.factory.make_full_session(turns=2)
        assert isinstance(entries, list)
        assert len(entries) > 0

    def test_all_entries_have_type(self):
        entries = self.factory.make_full_session(turns=2)
        for entry in entries:
            assert "type" in entry

    def test_all_entries_have_timestamp(self):
        entries = self.factory.make_full_session(turns=2)
        for entry in entries:
            assert "timestamp" in entry

    def test_timestamps_are_monotonic(self):
        entries = self.factory.make_full_session(turns=3)
        timestamps = [e["timestamp"] for e in entries]
        assert timestamps == sorted(timestamps)

    def test_includes_user_and_assistant(self):
        entries = self.factory.make_full_session(turns=2)
        types = {e["type"] for e in entries}
        assert "user" in types
        assert "assistant" in types

    def test_default_turns_creates_reasonable_session(self):
        entries = self.factory.make_full_session()
        assert len(entries) >= 6  # at least 3 turns × 2 entries

    def test_includes_tool_use_and_result(self):
        entries = self.factory.make_full_session(turns=3)
        content_types = set()
        for e in entries:
            msg = e.get("message", {})
            for block in msg.get("content", []):
                content_types.add(block.get("type"))
        assert "tool_use" in content_types

    def test_session_id_consistent(self):
        entries = self.factory.make_full_session(turns=2)
        session_ids = {e.get("sessionId") for e in entries
                       if e.get("sessionId")}
        # All non-system entries share the same session ID
        assert len(session_ids) <= 1


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------


class TestWriteJsonl:
    """write_jsonl() writes entries to a JSONL file."""

    def setup_method(self):
        self.factory = CCJsonlFactory()

    def test_creates_valid_jsonl(self, tmp_path):
        entries = self.factory.make_full_session(turns=2)
        path = tmp_path / "test.jsonl"
        self.factory.write_jsonl(entries, path)
        assert path.exists()
        # Each line is valid JSON
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == len(entries)
        for line in lines:
            json.loads(line)  # must not raise

    def test_write_session_file(self, tmp_path):
        path = self.factory.write_session_file(tmp_path, turns=2)
        assert path.exists()
        assert path.suffix == ".jsonl"


# ---------------------------------------------------------------------------
# Scanner compatibility: entries work with scan_jsonl_metadata()
# ---------------------------------------------------------------------------


class TestScannerCompatibility:
    """Factory output must be parseable by the real scanner."""

    def test_scan_extracts_metadata(self, tmp_path):
        from governance.services.cc_session_scanner import scan_jsonl_metadata

        factory = CCJsonlFactory()
        path = factory.write_session_file(tmp_path, turns=3)
        meta = scan_jsonl_metadata(path)

        assert meta is not None
        assert meta["session_uuid"] == factory.session_id
        assert meta["git_branch"] == factory.git_branch
        assert meta["user_count"] >= 1
        assert meta["assistant_count"] >= 1
        assert meta["first_ts"] is not None
        assert meta["last_ts"] is not None

    def test_scan_counts_tool_uses(self, tmp_path):
        from governance.services.cc_session_scanner import scan_jsonl_metadata

        factory = CCJsonlFactory()
        path = factory.write_session_file(tmp_path, turns=3)
        meta = scan_jsonl_metadata(path)

        assert meta["tool_use_count"] >= 1


# ---------------------------------------------------------------------------
# Transcript compatibility: entries work with stream_transcript()
# ---------------------------------------------------------------------------


class TestTranscriptCompatibility:
    """Factory output must be parseable by the real transcript parser."""

    def test_stream_produces_entries(self, tmp_path):
        from governance.services.cc_transcript import stream_transcript

        factory = CCJsonlFactory()
        path = factory.write_session_file(tmp_path, turns=3)
        entries = list(stream_transcript(path))

        assert len(entries) > 0
        entry_types = {e.entry_type for e in entries}
        assert "user_prompt" in entry_types

    def test_stream_finds_tool_use(self, tmp_path):
        from governance.services.cc_transcript import stream_transcript

        factory = CCJsonlFactory()
        path = factory.write_session_file(tmp_path, turns=3)
        entries = list(stream_transcript(path))

        entry_types = {e.entry_type for e in entries}
        assert "tool_use" in entry_types
