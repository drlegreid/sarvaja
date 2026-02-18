"""Batch 194 — Evidence + Ingestion layer defense tests.

Validates fixes for:
- BUG-194-002: JSONL existence check in cc_content_indexer
- BUG-194-005: Evidence file write try-except safety
- Evidence rendering defense (markdown table pipes, truncation)
"""
import ast
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-194-002: JSONL existence guard ──────────────────────────────

class TestContentIndexerJSONLGuard:
    """cc_content_indexer must check JSONL existence before parsing."""

    def test_index_session_content_has_existence_check(self):
        """Verify the Path(jsonl_path).exists() guard is present."""
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        assert "not Path(jsonl_path).exists()" in src or "jsonl_path).exists()" in src

    def test_index_session_returns_error_for_missing_file(self):
        """index_session_content returns error status for missing file."""
        from governance.services.cc_content_indexer import index_session_content
        result = index_session_content(
            jsonl_path=Path("/nonexistent/file.jsonl"),
            session_id="test-session",
            dry_run=True,
        )
        assert result["status"] == "error"
        assert any("not found" in e.lower() or "nonexistent" in e.lower() for e in result["errors"])


# ── BUG-194-005: Evidence file write safety ─────────────────────────

class TestEvidenceWriteSafety:
    """session_evidence.generate_session_evidence must handle write errors."""

    def test_generate_evidence_has_try_except_on_write(self):
        """Verify write_text is wrapped in try-except."""
        src = (SRC / "governance/services/session_evidence.py").read_text()
        assert "except OSError" in src

    def test_generate_evidence_returns_none_on_write_error(self):
        """generate_session_evidence returns None on OSError."""
        from governance.services.session_evidence import generate_session_evidence
        session_data = {
            "session_id": "SESSION-2026-01-01-TEST",
            "status": "COMPLETED",
            "start_time": "2026-01-01T09:00:00",
            "end_time": "2026-01-01T10:00:00",
        }
        # Use a path that doesn't exist and can't be created
        result = generate_session_evidence(session_data, output_dir=Path("/proc/nonexistent"))
        assert result is None


# ── Evidence rendering defense ──────────────────────────────────────

class TestEvidenceRendering:
    """Evidence markdown rendering must handle edge cases."""

    def test_compile_evidence_data_handles_empty_session(self):
        """compile_evidence_data should not crash on empty dict."""
        from governance.services.session_evidence import compile_evidence_data
        result = compile_evidence_data({})
        assert result["session_id"] == "UNKNOWN"
        assert result["tool_calls"] == []
        assert result["decisions"] == []
        assert result["tasks"] == []

    def test_render_evidence_escapes_pipes_in_decisions(self):
        """Pipe characters in decision titles must be escaped for markdown tables."""
        from governance.services.session_evidence import render_evidence_markdown
        data = {
            "session_id": "TEST",
            "decisions": [{"decision_id": "D1", "title": "Use A | B", "rationale": "Because"}],
            "tool_calls": [],
            "tasks": [],
        }
        md = render_evidence_markdown(data)
        # The pipe in "Use A | B" should be escaped
        assert "\\|" in md

    def test_render_evidence_escapes_pipes_in_tasks(self):
        """Pipe characters in task descriptions must be escaped."""
        from governance.services.session_evidence import render_evidence_markdown
        data = {
            "session_id": "TEST",
            "decisions": [],
            "tool_calls": [],
            "tasks": [{"task_id": "T1", "description": "Do X | Y", "status": "DONE"}],
        }
        md = render_evidence_markdown(data)
        assert "\\|" in md

    def test_truncate_helper(self):
        """_truncate should add ellipsis for long strings."""
        from governance.services.session_evidence import _truncate
        assert _truncate("short", 100) == "short"
        assert _truncate("a" * 200, 50).endswith("...")
        assert len(_truncate("a" * 200, 50)) == 50

    def test_compute_duration_handles_reversed_timestamps(self):
        """_compute_duration with end before start returns negative result or 'unknown'."""
        from governance.services.session_evidence import _compute_duration
        result = _compute_duration("2026-01-01T10:00:00", "2026-01-01T09:00:00")
        # It returns the raw math (negative minutes) — not crashing is the key
        assert isinstance(result, str)

    def test_generate_evidence_skips_non_completed(self):
        """generate_session_evidence returns None for non-completed sessions."""
        from governance.services.session_evidence import generate_session_evidence
        result = generate_session_evidence({"session_id": "TEST", "status": "ACTIVE"})
        assert result is None
