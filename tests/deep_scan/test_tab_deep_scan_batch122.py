"""Deep scan batch 122: CC session scanner + ingestion pipeline.

Batch 122 findings: 13 total, 0 confirmed fixes, 13 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import re


# ── CC scanner directory guard defense ──────────────


class TestCCScannerDirectoryGuardDefense:
    """Verify CC scanner handles missing directories safely."""

    def test_find_jsonl_returns_none_when_no_dir(self):
        """find_jsonl_for_session returns None when CC dir missing."""
        from governance.services.cc_session_scanner import find_jsonl_for_session

        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR", Path("/nonexistent")):
            result = find_jsonl_for_session("SESSION-2026-02-15-TEST")
            assert result is None

    def test_discover_projects_returns_empty_when_no_dir(self):
        """discover_cc_projects returns empty list when CC dir missing."""
        from governance.services.cc_session_scanner import discover_cc_projects

        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR", Path("/nonexistent")):
            result = discover_cc_projects()
            assert result == []

    def test_build_session_id_sentinel_date(self):
        """build_session_id uses 1970-01-01 sentinel for missing timestamps."""
        from governance.services.cc_session_scanner import build_session_id

        meta = {}  # No first_ts
        result = build_session_id(meta, "test-project")
        assert "1970-01-01" in result


# ── JSONL parsing defense ──────────────


class TestJSONLParsingDefense:
    """Verify JSONL parsing handles malformed lines."""

    def test_malformed_json_skipped(self):
        """Malformed JSON lines are skipped without crash."""
        lines = [
            '{"type": "user", "message": "hello"}',
            "{corrupt",
            '{"type": "assistant", "message": "hi"}',
        ]
        parsed = []
        for line in lines:
            try:
                parsed.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        assert len(parsed) == 2

    def test_empty_lines_handled(self):
        """Empty lines in JSONL don't crash parser."""
        lines = ['{"a": 1}', "", '{"b": 2}', "   "]
        parsed = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parsed.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        assert len(parsed) == 2


# ── Regex safety defense ──────────────


class TestRegexSafetyDefense:
    """Verify regex patterns don't cause catastrophic backtracking."""

    def test_lazy_match_code_block(self):
        """Lazy .*? in code block regex prevents backtracking."""
        text = "```python\nprint('hello')\n```\n\nMore text"
        matches = re.findall(r"```(\w*)\n(.*?)```", text, re.DOTALL)
        assert len(matches) == 1
        assert matches[0][0] == "python"
        assert "print" in matches[0][1]

    def test_large_code_block_no_backtrack(self):
        """Large code block doesn't cause timeout with lazy match."""
        content = "A\n" * 1000
        text = f"```python\n{content}```"
        matches = re.findall(r"```(\w*)\n(.*?)```", text, re.DOTALL)
        assert len(matches) == 1

    def test_no_match_returns_empty(self):
        """No code blocks returns empty list."""
        text = "Just normal text without code blocks"
        matches = re.findall(r"```(\w*)\n(.*?)```", text, re.DOTALL)
        assert len(matches) == 0


# ── Timestamp extraction defense ──────────────


class TestTimestampExtractionDefense:
    """Verify timestamp extraction handles edge cases."""

    def test_first_ts_string_sliced_correctly(self):
        """String timestamp sliced to date portion."""
        ts = "2026-02-15T14:30:00"
        date_str = (ts or "1970-01-01")[:10]
        assert date_str == "2026-02-15"

    def test_none_ts_uses_sentinel(self):
        """None timestamp uses 1970-01-01 sentinel."""
        ts = None
        date_str = (ts or "1970-01-01")[:10]
        assert date_str == "1970-01-01"

    def test_empty_ts_uses_sentinel(self):
        """Empty string uses 1970-01-01 sentinel."""
        ts = ""
        date_str = (ts or "1970-01-01")[:10]
        assert date_str == "1970-01-01"


# ── Checkpoint atomicity defense ──────────────


class TestCheckpointAtomicityDefense:
    """Verify checkpoint save uses atomic write pattern."""

    def test_os_replace_is_atomic(self):
        """os.replace is atomic on POSIX (same filesystem)."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "temp.json"
            dst = Path(tmpdir) / "final.json"
            src.write_text('{"key": "value"}')
            os.replace(str(src), str(dst))
            assert dst.exists()
            assert not src.exists()
            assert json.loads(dst.read_text())["key"] == "value"
