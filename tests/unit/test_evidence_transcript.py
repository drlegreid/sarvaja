"""
Unit tests for evidence_transcript.py (GAP-SESSION-TRANSCRIPT-001).

Tests evidence .md file parsing into TranscriptEntry format.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from governance.services.evidence_transcript import (
    find_evidence_file,
    parse_evidence_transcript,
    _parse_tool_success_map,
    _parse_event_timeline,
    _parse_table_and_thoughts,
)


# --- Sample evidence markdown ---

EVIDENCE_FULL = """# Session Evidence Log: CHAT-FULL-LIFECYCLE

**Session ID:** SESSION-2026-02-15-CHAT-FULL-LIFECYCLE
**Type:** general
**Started:** 2026-02-15T18:03:43.318292
**Ended:** 2026-02-15T18:03:43.353747
**Duration:** 0:00:00.035455

---

## Key Thoughts

*Per RECOVER-AMNES-01-v1: Captured for context recovery*

### Observation

> System is healthy


### Reasoning

> Need to review tasks


---

## Tool Calls

*Per RECOVER-AMNES-01-v1: Action trail for context recovery*

| Tool | Success | Duration |
|------|---------|----------|
| /status | ✅ | 10ms |
| /tasks | ✅ | 20ms |

---

## Event Timeline

- 🔧 **TOOL_CALL** (2026-02-15T18:03:43.336148): /status()...
- 💭 **THOUGHT** (2026-02-15T18:03:43.336161): System is healthy...
- 🔧 **TOOL_CALL** (2026-02-15T18:03:43.336166): /tasks()...
- 💭 **THOUGHT** (2026-02-15T18:03:43.336171): Need to review tasks...

---

*Generated per SESSION-EVID-01-v1: Session Evidence Logging*
"""

EVIDENCE_HEURISTIC = """# Session Evidence Log: CHAT-HEURISTIC-CHECK

## Tool Calls

| Tool | Success | Duration |
|------|---------|----------|
| heuristic/H-TASK-001 | ✅ | 94ms |
| heuristic/H-TASK-002 | ❌ | 50ms |
| heuristic/H-SESSION-001 | ✅ | 27ms |

---

## Event Timeline

- 🔧 **TOOL_CALL** (2026-02-01T20:52:28.742434): heuristic/H-TASK-001(domain=TASK)...
- 🔧 **TOOL_CALL** (2026-02-01T20:52:28.793157): heuristic/H-TASK-002(domain=TASK)...
- 🔧 **TOOL_CALL** (2026-02-01T20:52:28.934196): heuristic/H-SESSION-001(domain=SESSION)...
"""

EVIDENCE_NO_TIMELINE = """# Session Evidence Log

## Key Thoughts

### Observation

> Everything looks good

## Tool Calls

| Tool | Success | Duration |
|------|---------|----------|
| /status | ✅ | 5ms |
| /deploy | ❌ | 1200ms |
"""


class TestToolSuccessMap:
    def test_parses_success_checkmarks(self):
        result = _parse_tool_success_map(EVIDENCE_FULL)
        assert result["/status"] is True
        assert result["/tasks"] is True

    def test_parses_failure_marks(self):
        result = _parse_tool_success_map(EVIDENCE_HEURISTIC)
        assert result["heuristic/H-TASK-001"] is True
        assert result["heuristic/H-TASK-002"] is False
        assert result["heuristic/H-SESSION-001"] is True

    def test_skips_table_header(self):
        result = _parse_tool_success_map(EVIDENCE_FULL)
        assert "Tool" not in result

    def test_empty_text(self):
        assert _parse_tool_success_map("") == {}


class TestEventTimelineParsing:
    def test_extracts_tool_calls(self):
        success_map = _parse_tool_success_map(EVIDENCE_FULL)
        entries = _parse_event_timeline(EVIDENCE_FULL, success_map, True)
        tool_entries = [e for e in entries if e.entry_type == "tool_use"]
        assert len(tool_entries) == 2
        assert tool_entries[0].tool_name == "/status"
        assert tool_entries[1].tool_name == "/tasks"

    def test_extracts_thoughts(self):
        success_map = _parse_tool_success_map(EVIDENCE_FULL)
        entries = _parse_event_timeline(EVIDENCE_FULL, success_map, True)
        thought_entries = [e for e in entries if e.entry_type == "thinking"]
        assert len(thought_entries) == 2
        assert "System is healthy" in thought_entries[0].content

    def test_excludes_thoughts_when_disabled(self):
        success_map = _parse_tool_success_map(EVIDENCE_FULL)
        entries = _parse_event_timeline(EVIDENCE_FULL, success_map, False)
        thought_entries = [e for e in entries if e.entry_type == "thinking"]
        assert len(thought_entries) == 0

    def test_timestamps_extracted(self):
        success_map = _parse_tool_success_map(EVIDENCE_FULL)
        entries = _parse_event_timeline(EVIDENCE_FULL, success_map, True)
        assert entries[0].timestamp == "2026-02-15T18:03:43.336148"

    def test_sorted_chronologically(self):
        success_map = _parse_tool_success_map(EVIDENCE_FULL)
        entries = _parse_event_timeline(EVIDENCE_FULL, success_map, True)
        timestamps = [e.timestamp for e in entries]
        assert timestamps == sorted(timestamps)

    def test_error_status_from_success_map(self):
        success_map = _parse_tool_success_map(EVIDENCE_HEURISTIC)
        entries = _parse_event_timeline(EVIDENCE_HEURISTIC, success_map, True)
        tool_entries = [e for e in entries if e.entry_type == "tool_use"]
        assert tool_entries[0].is_error is False  # H-TASK-001 = ✅
        assert tool_entries[1].is_error is True   # H-TASK-002 = ❌

    def test_no_timeline_returns_empty(self):
        entries = _parse_event_timeline(EVIDENCE_NO_TIMELINE, {}, True)
        assert entries == []


class TestTableAndThoughtsParsing:
    def test_parses_tool_table(self):
        success_map = _parse_tool_success_map(EVIDENCE_NO_TIMELINE)
        entries = _parse_table_and_thoughts(
            EVIDENCE_NO_TIMELINE, success_map, True,
        )
        tool_entries = [e for e in entries if e.entry_type == "tool_use"]
        assert len(tool_entries) == 2
        names = {e.tool_name for e in tool_entries}
        assert "/status" in names
        assert "/deploy" in names

    def test_parses_key_thoughts(self):
        success_map = _parse_tool_success_map(EVIDENCE_NO_TIMELINE)
        entries = _parse_table_and_thoughts(
            EVIDENCE_NO_TIMELINE, success_map, True,
        )
        thought_entries = [e for e in entries if e.entry_type == "thinking"]
        assert len(thought_entries) == 1
        assert "Everything looks good" in thought_entries[0].content

    def test_deploy_failure_marked(self):
        success_map = _parse_tool_success_map(EVIDENCE_NO_TIMELINE)
        entries = _parse_table_and_thoughts(
            EVIDENCE_NO_TIMELINE, success_map, True,
        )
        deploy = [e for e in entries if e.tool_name == "/deploy"]
        assert deploy[0].is_error is True


class TestParseEvidenceTranscript:
    def test_full_evidence_returns_entries(self, tmp_path):
        f = tmp_path / "SESSION-TEST.md"
        f.write_text(EVIDENCE_FULL)
        result = parse_evidence_transcript(f)
        assert result["source"] == "evidence"
        assert result["total"] == 4  # 2 tool_calls + 2 thoughts
        assert len(result["entries"]) == 4

    def test_pagination(self, tmp_path):
        f = tmp_path / "SESSION-TEST.md"
        f.write_text(EVIDENCE_FULL)
        result = parse_evidence_transcript(f, page=1, per_page=2)
        assert len(result["entries"]) == 2
        assert result["has_more"] is True
        result2 = parse_evidence_transcript(f, page=2, per_page=2)
        assert len(result2["entries"]) == 2
        assert result2["has_more"] is False

    def test_indexes_sequential(self, tmp_path):
        f = tmp_path / "SESSION-TEST.md"
        f.write_text(EVIDENCE_FULL)
        result = parse_evidence_transcript(f)
        indexes = [e["index"] for e in result["entries"]]
        assert indexes == list(range(len(indexes)))

    def test_falls_back_to_table_when_no_timeline(self, tmp_path):
        f = tmp_path / "SESSION-TEST.md"
        f.write_text(EVIDENCE_NO_TIMELINE)
        result = parse_evidence_transcript(f)
        assert result["total"] == 3  # 2 tools + 1 thought
        assert result["source"] == "evidence"

    def test_content_truncation(self, tmp_path):
        long_content = EVIDENCE_FULL.replace(
            "System is healthy", "X" * 5000,
        )
        f = tmp_path / "SESSION-TEST.md"
        f.write_text(long_content)
        result = parse_evidence_transcript(f, content_limit=100)
        thinking = [e for e in result["entries"] if e["entry_type"] == "thinking"]
        if thinking:
            assert thinking[0].get("is_truncated") is True

    def test_heuristic_evidence(self, tmp_path):
        f = tmp_path / "SESSION-TEST.md"
        f.write_text(EVIDENCE_HEURISTIC)
        result = parse_evidence_transcript(f)
        assert result["total"] == 3  # 3 tool calls
        tools = [e for e in result["entries"] if e["entry_type"] == "tool_use"]
        assert len(tools) == 3

    def test_empty_file(self, tmp_path):
        f = tmp_path / "SESSION-TEST.md"
        f.write_text("")
        result = parse_evidence_transcript(f)
        assert result["total"] == 0
        assert result["entries"] == []


class TestFindEvidenceFile:
    def test_exact_match(self, tmp_path):
        f = tmp_path / "SESSION-2026-02-15-CHAT-TEST.md"
        f.write_text("test")
        with patch(
            "governance.services.evidence_transcript._EVIDENCE_DIR", tmp_path,
        ):
            result = find_evidence_file("SESSION-2026-02-15-CHAT-TEST")
            assert result == f

    def test_fuzzy_match(self, tmp_path):
        f = tmp_path / "SESSION-2026-02-15-CHAT-FULL-LIFECYCLE.md"
        f.write_text("test")
        with patch(
            "governance.services.evidence_transcript._EVIDENCE_DIR", tmp_path,
        ):
            result = find_evidence_file(
                "SESSION-2026-02-15-CHAT-FULL-LIFECYCLE",
            )
            assert result == f

    def test_no_match_returns_none(self, tmp_path):
        with patch(
            "governance.services.evidence_transcript._EVIDENCE_DIR", tmp_path,
        ):
            result = find_evidence_file("SESSION-NONEXISTENT")
            assert result is None

    def test_missing_dir_returns_none(self):
        with patch(
            "governance.services.evidence_transcript._EVIDENCE_DIR",
            Path("/nonexistent"),
        ):
            result = find_evidence_file("SESSION-TEST")
            assert result is None
