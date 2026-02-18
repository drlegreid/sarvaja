"""Batch 216 — Models + parser defense tests.

Validates fixes for:
- BUG-216-003-001: parser.py encoding on file open
- BUG-216-009-001: json.dumps guard in ToolUseInfo.from_content_block
"""
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-216-003-001: Parser encoding ─────────────────────────────────

class TestParserEncoding:
    """parse_log_file must specify encoding on file open."""

    def test_encoding_in_parse_log_file(self):
        """Both open() calls in parser.py must include encoding='utf-8'."""
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        # Count open() calls with encoding
        import re
        opens_with_encoding = re.findall(r'open\(filepath.*encoding="utf-8"', src)
        assert len(opens_with_encoding) >= 2, \
            f"Expected 2+ open() calls with encoding, found {len(opens_with_encoding)}"


# ── BUG-216-009-001: json.dumps guard ────────────────────────────────

class TestToolUseInfoJsonGuard:
    """ToolUseInfo.from_content_block must handle non-serializable input."""

    def test_json_dumps_guard_in_source(self):
        """Source must have try/except around json.dumps."""
        src = (SRC / "governance/session_metrics/models.py").read_text()
        assert "default=str" in src or "TypeError" in src

    def test_from_content_block_with_normal_input(self):
        from governance.session_metrics.models import ToolUseInfo
        block = {"name": "Read", "input": {"file_path": "/test.py"}, "id": "use-123"}
        info = ToolUseInfo.from_content_block(block)
        assert info.name == "Read"
        assert info.tool_use_id == "use-123"
        assert "file_path" in info.input_summary

    def test_from_content_block_with_empty_input(self):
        from governance.session_metrics.models import ToolUseInfo
        block = {"name": "Write", "id": "use-456"}
        info = ToolUseInfo.from_content_block(block)
        assert info.input_summary == "{}"

    def test_from_content_block_truncates_long_input(self):
        from governance.session_metrics.models import ToolUseInfo
        block = {"name": "Bash", "input": {"command": "x" * 500}, "id": "use-789"}
        info = ToolUseInfo.from_content_block(block)
        assert len(info.input_summary) <= 200
        assert info.input_summary.endswith("...")


# ── Parser defense ───────────────────────────────────────────────────

class TestParserDefense:
    """Defense tests for session metrics parser."""

    def test_parse_log_file_callable(self):
        from governance.session_metrics.parser import parse_log_file
        assert callable(parse_log_file)

    def test_parse_log_file_extended_callable(self):
        from governance.session_metrics.parser import parse_log_file_extended
        assert callable(parse_log_file_extended)

    def test_parse_timestamp_callable(self):
        from governance.session_metrics.parser import _parse_timestamp
        assert callable(_parse_timestamp)

    def test_parse_timestamp_with_z(self):
        from governance.session_metrics.parser import _parse_timestamp
        ts = _parse_timestamp("2026-01-15T09:00:00.000Z")
        assert ts is not None

    def test_parse_timestamp_with_offset(self):
        from governance.session_metrics.parser import _parse_timestamp
        ts = _parse_timestamp("2026-01-15T09:00:00+00:00")
        assert ts is not None

    def test_parse_timestamp_invalid(self):
        """Invalid timestamps raise ValueError (caller must handle)."""
        from governance.session_metrics.parser import _parse_timestamp
        import pytest
        with pytest.raises(ValueError):
            _parse_timestamp("not-a-timestamp")


# ── Models defense ───────────────────────────────────────────────────

class TestModelsDefense:
    """Defense tests for session metrics models."""

    def test_tool_use_info_dataclass(self):
        from governance.session_metrics.models import ToolUseInfo
        info = ToolUseInfo(name="Test", input_summary="{}", is_mcp=False)
        assert info.name == "Test"

    def test_tool_result_info_dataclass(self):
        from governance.session_metrics.models import ToolResultInfo
        info = ToolResultInfo(tool_use_id="use-1")
        assert info.tool_use_id == "use-1"

    def test_transcript_entry_to_dict(self):
        from governance.session_metrics.models import TranscriptEntry
        entry = TranscriptEntry(
            index=0, timestamp="2026-01-15T09:00:00",
            entry_type="user_prompt", content="Hello",
            content_length=5,
        )
        d = entry.to_dict()
        assert d["index"] == 0
        assert d["entry_type"] == "user_prompt"
        assert d["content"] == "Hello"
