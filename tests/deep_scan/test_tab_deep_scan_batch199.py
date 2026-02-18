"""Batch 199 — Context + ingestion layer defense tests.

Validates fixes for:
- BUG-199-INGEST-003: Negative page index guard
- BUG-199-CKPT-001: OSError in checkpoint load
- BUG-199-ORCH-001: encoding= on file open
- Checkpoint + orchestrator defense
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-199-INGEST-003: Negative page guard ────────────────────────

class TestIngestionPaginationGuard:
    """Pagination must not return wrong data for page < 1."""

    def test_pagination_uses_max_zero(self):
        """Verify start = max(0, ...) pattern in pagination."""
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        assert "max(0," in src, "Pagination must use max(0, ...) to guard negative page"

    def test_pagination_guard_for_tool_calls_and_thinking(self):
        """Both tool_calls and thinking_blocks pagination should be guarded."""
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        count = src.count("max(0, (page - 1)")
        assert count >= 2, f"Expected at least 2 pagination guards, found {count}"


# ── BUG-199-CKPT-001: OSError in checkpoint load ───────────────────

class TestCheckpointOSError:
    """load_checkpoint must catch OSError."""

    def test_load_checkpoint_catches_oserror(self):
        """Verify OSError is in the except tuple."""
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        assert "OSError" in src

    def test_load_checkpoint_returns_none_on_corrupt(self):
        """load_checkpoint returns None for corrupt/unreadable files."""
        from governance.services.ingestion_checkpoint import load_checkpoint
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a corrupt checkpoint file
            ckpt_dir = Path(tmpdir)
            ckpt_file = ckpt_dir / "test-session.json"
            ckpt_file.write_text("not valid json{{{", encoding="utf-8")
            result = load_checkpoint("test-session", ckpt_dir)
            assert result is None

    def test_save_and_load_checkpoint_roundtrip(self):
        """save_checkpoint + load_checkpoint roundtrip works."""
        from governance.services.ingestion_checkpoint import (
            IngestionCheckpoint, save_checkpoint, load_checkpoint,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_dir = Path(tmpdir)
            ckpt = IngestionCheckpoint(
                session_id="test-roundtrip",
                jsonl_path="/tmp/test.jsonl",
                phase="content",
                chunks_indexed=42,
            )
            save_checkpoint(ckpt, ckpt_dir)
            loaded = load_checkpoint("test-roundtrip", ckpt_dir)
            assert loaded is not None
            assert loaded.session_id == "test-roundtrip"
            assert loaded.chunks_indexed == 42


# ── BUG-199-ORCH-001: File encoding ────────────────────────────────

class TestOrchestratorEncoding:
    """estimate_ingestion must specify encoding."""

    def test_estimate_ingestion_uses_utf8(self):
        """Verify encoding='utf-8' in file open."""
        src = (SRC / "governance/services/ingestion_orchestrator.py").read_text()
        assert 'encoding="utf-8"' in src or "encoding='utf-8'" in src

    def test_estimate_ingestion_callable(self):
        """estimate_ingestion should be importable."""
        from governance.services.ingestion_orchestrator import estimate_ingestion
        assert callable(estimate_ingestion)


# ── Additional defense tests ────────────────────────────────────────

class TestIngestionDefense:
    """Defense tests for ingestion components."""

    def test_checkpoint_from_dict_handles_missing_fields(self):
        """IngestionCheckpoint.from_dict raises on missing required fields."""
        from governance.services.ingestion_checkpoint import IngestionCheckpoint
        try:
            IngestionCheckpoint.from_dict({"phase": "content"})
            assert False, "Should raise TypeError for missing session_id"
        except TypeError:
            pass  # Expected — missing required fields

    def test_get_resume_offset_returns_zero_on_missing(self):
        """get_resume_offset returns 0 when no checkpoint exists."""
        from governance.services.ingestion_checkpoint import get_resume_offset
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_resume_offset("nonexistent-session", Path(tmpdir))
            assert result == 0
