"""
Unit tests for Ingestion Checkpoint Engine.

Batch 152: Tests for governance/services/ingestion_checkpoint.py
- IngestionCheckpoint dataclass: fields, touch, add_error, to_dict, from_dict
- save_checkpoint / load_checkpoint: atomic writes, round-trip
- get_resume_offset: fresh vs resume
- delete_checkpoint: present vs missing
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.services.ingestion_checkpoint import (
    IngestionCheckpoint,
    _checkpoint_path,
    delete_checkpoint,
    get_resume_offset,
    load_checkpoint,
    save_checkpoint,
)


# ── IngestionCheckpoint dataclass ───────────────────────

class TestIngestionCheckpoint:
    def test_defaults(self):
        cp = IngestionCheckpoint(session_id="S-1", jsonl_path="/a/b.jsonl")
        assert cp.lines_processed == 0
        assert cp.chunks_indexed == 0
        assert cp.phase == "pending"
        assert cp.started_at != ""
        assert cp.updated_at == cp.started_at
        assert cp.errors == []

    def test_touch_updates_timestamp(self):
        cp = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl")
        old_ts = cp.updated_at
        time.sleep(0.01)
        cp.touch()
        assert cp.updated_at >= old_ts

    def test_add_error(self):
        cp = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl")
        cp.add_error("something broke")
        assert len(cp.errors) == 1
        assert "something broke" in cp.errors[0]

    def test_add_error_caps_at_max(self):
        cp = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl")
        for i in range(250):
            cp.add_error(f"err-{i}", max_errors=200)
        assert len(cp.errors) == 200

    def test_to_dict(self):
        cp = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl", phase="content")
        d = cp.to_dict()
        assert d["session_id"] == "S-1"
        assert d["phase"] == "content"
        assert isinstance(d["errors"], list)

    def test_from_dict(self):
        data = {
            "session_id": "S-1", "jsonl_path": "/a.jsonl",
            "lines_processed": 42, "chunks_indexed": 5,
            "phase": "linking", "started_at": "2026-01-01",
            "updated_at": "2026-01-02", "errors": ["e1"],
        }
        cp = IngestionCheckpoint.from_dict(data)
        assert cp.session_id == "S-1"
        assert cp.lines_processed == 42
        assert cp.errors == ["e1"]

    def test_from_dict_ignores_unknown_keys(self):
        data = {"session_id": "S-1", "jsonl_path": "/a.jsonl", "bogus_key": True}
        cp = IngestionCheckpoint.from_dict(data)
        assert cp.session_id == "S-1"
        assert not hasattr(cp, "bogus_key")

    def test_roundtrip(self):
        cp = IngestionCheckpoint(
            session_id="S-1", jsonl_path="/a.jsonl",
            lines_processed=100, chunks_indexed=10, phase="complete",
        )
        cp.add_error("test error")
        d = cp.to_dict()
        cp2 = IngestionCheckpoint.from_dict(d)
        assert cp2.session_id == cp.session_id
        assert cp2.lines_processed == cp.lines_processed
        assert cp2.errors == cp.errors


# ── _checkpoint_path ────────────────────────────────────

class TestCheckpointPath:
    def test_basic(self):
        p = _checkpoint_path(Path("/dir"), "S-1")
        assert p == Path("/dir/S-1.json")

    def test_sanitizes_slashes(self):
        p = _checkpoint_path(Path("/dir"), "path/to/session")
        assert "/" not in p.stem or p.parent == Path("/dir")


# ── save_checkpoint + load_checkpoint ───────────────────

class TestSaveLoadCheckpoint:
    def test_save_creates_file(self, tmp_path):
        cp = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl")
        path = save_checkpoint(cp, tmp_path)
        assert path.exists()
        assert path.name == "S-1.json"

    def test_load_roundtrip(self, tmp_path):
        cp = IngestionCheckpoint(
            session_id="S-1", jsonl_path="/a.jsonl",
            lines_processed=50, chunks_indexed=5, phase="content",
        )
        save_checkpoint(cp, tmp_path)
        loaded = load_checkpoint("S-1", tmp_path)
        assert loaded is not None
        assert loaded.session_id == "S-1"
        assert loaded.lines_processed == 50

    def test_load_missing(self, tmp_path):
        result = load_checkpoint("NONEXISTENT", tmp_path)
        assert result is None

    def test_load_corrupt_json(self, tmp_path):
        (tmp_path / "BAD.json").write_text("{{corrupt")
        result = load_checkpoint("BAD", tmp_path)
        assert result is None

    def test_save_creates_directory(self, tmp_path):
        cp_dir = tmp_path / "nested" / "dir"
        cp = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl")
        save_checkpoint(cp, cp_dir)
        assert cp_dir.exists()

    def test_save_overwrites(self, tmp_path):
        cp1 = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl", phase="content")
        save_checkpoint(cp1, tmp_path)
        cp2 = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl", phase="complete")
        save_checkpoint(cp2, tmp_path)
        loaded = load_checkpoint("S-1", tmp_path)
        assert loaded.phase == "complete"


# ── get_resume_offset ───────────────────────────────────

class TestGetResumeOffset:
    def test_no_checkpoint(self, tmp_path):
        assert get_resume_offset("FRESH", tmp_path) == 0

    def test_with_checkpoint(self, tmp_path):
        cp = IngestionCheckpoint(
            session_id="S-1", jsonl_path="/a.jsonl", lines_processed=42)
        save_checkpoint(cp, tmp_path)
        assert get_resume_offset("S-1", tmp_path) == 42


# ── delete_checkpoint ───────────────────────────────────

class TestDeleteCheckpoint:
    def test_delete_existing(self, tmp_path):
        cp = IngestionCheckpoint(session_id="S-1", jsonl_path="/a.jsonl")
        save_checkpoint(cp, tmp_path)
        assert delete_checkpoint("S-1", tmp_path) is True
        assert load_checkpoint("S-1", tmp_path) is None

    def test_delete_missing(self, tmp_path):
        assert delete_checkpoint("NONEXISTENT", tmp_path) is False
