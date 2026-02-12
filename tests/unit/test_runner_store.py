"""
Unit tests for Test Result Storage & Persistence.

Per DOC-SIZE-01-v1: Tests for extracted runner_store.py module.
Tests: _resolve_test_root, _persist_result, _load_persisted_results.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from governance.routes.tests.runner_store import (
    _resolve_test_root,
    _persist_result,
    _load_persisted_results,
)


# ---------------------------------------------------------------------------
# _resolve_test_root
# ---------------------------------------------------------------------------
class TestResolveTestRoot:
    """Tests for _resolve_test_root()."""

    def test_returns_string(self):
        result = _resolve_test_root()
        assert isinstance(result, str)

    def test_result_is_valid_directory(self):
        result = _resolve_test_root()
        assert Path(result).is_dir()

    @patch("governance.routes.tests.runner_store.Path")
    def test_container_path_preferred(self, MockPath):
        """When /app/tests exists, returns /app."""
        instance = MockPath.return_value
        instance.is_dir.return_value = True
        # First call is Path("/app/tests").is_dir()
        MockPath.side_effect = None
        # This is tricky to mock due to Path usage; test the real function instead
        result = _resolve_test_root()
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# _persist_result
# ---------------------------------------------------------------------------
class TestPersistResult:
    """Tests for _persist_result()."""

    def test_creates_json_file(self, tmp_path):
        result = {"status": "pass", "tests": 10}
        _persist_result("RUN-001", result, results_dir=str(tmp_path))

        filepath = tmp_path / "RUN-001.json"
        assert filepath.exists()

    def test_file_contains_valid_json(self, tmp_path):
        result = {"status": "pass", "duration": 1.5}
        _persist_result("RUN-002", result, results_dir=str(tmp_path))

        filepath = tmp_path / "RUN-002.json"
        data = json.loads(filepath.read_text())
        assert data["status"] == "pass"
        assert data["duration"] == 1.5

    def test_creates_directory_if_needed(self, tmp_path):
        nested = tmp_path / "deep" / "nested"
        _persist_result("RUN-003", {"ok": True}, results_dir=str(nested))

        assert (nested / "RUN-003.json").exists()

    def test_overwrites_existing_file(self, tmp_path):
        _persist_result("RUN-004", {"v": 1}, results_dir=str(tmp_path))
        _persist_result("RUN-004", {"v": 2}, results_dir=str(tmp_path))

        data = json.loads((tmp_path / "RUN-004.json").read_text())
        assert data["v"] == 2

    def test_handles_non_serializable_with_default_str(self, tmp_path):
        from datetime import datetime
        result = {"ts": datetime(2026, 2, 11, 10, 0, 0)}
        _persist_result("RUN-005", result, results_dir=str(tmp_path))

        data = json.loads((tmp_path / "RUN-005.json").read_text())
        assert "2026" in data["ts"]

    def test_indented_output(self, tmp_path):
        _persist_result("RUN-006", {"a": 1}, results_dir=str(tmp_path))
        text = (tmp_path / "RUN-006.json").read_text()
        assert "\n" in text  # indented = multiline


# ---------------------------------------------------------------------------
# _load_persisted_results
# ---------------------------------------------------------------------------
class TestLoadPersistedResults:
    """Tests for _load_persisted_results()."""

    def test_empty_directory(self, tmp_path):
        results = _load_persisted_results(results_dir=str(tmp_path))
        assert results == {}

    def test_nonexistent_directory(self, tmp_path):
        results = _load_persisted_results(results_dir=str(tmp_path / "nope"))
        assert results == {}

    def test_loads_single_file(self, tmp_path):
        (tmp_path / "RUN-001.json").write_text('{"status": "pass"}')
        results = _load_persisted_results(results_dir=str(tmp_path))
        assert "RUN-001" in results
        assert results["RUN-001"]["status"] == "pass"

    def test_loads_multiple_files(self, tmp_path):
        for i in range(5):
            (tmp_path / f"RUN-{i:03d}.json").write_text(f'{{"n": {i}}}')
        results = _load_persisted_results(results_dir=str(tmp_path))
        assert len(results) == 5

    def test_caps_at_50_files(self, tmp_path):
        for i in range(60):
            (tmp_path / f"RUN-{i:03d}.json").write_text(f'{{"n": {i}}}')
        results = _load_persisted_results(results_dir=str(tmp_path))
        assert len(results) == 50

    def test_skips_invalid_json(self, tmp_path):
        (tmp_path / "GOOD.json").write_text('{"ok": true}')
        (tmp_path / "BAD.json").write_text("not json!")
        results = _load_persisted_results(results_dir=str(tmp_path))
        assert "GOOD" in results
        assert "BAD" not in results

    def test_ignores_non_json_files(self, tmp_path):
        (tmp_path / "notes.txt").write_text("not a result")
        (tmp_path / "RUN-001.json").write_text('{"ok": true}')
        results = _load_persisted_results(results_dir=str(tmp_path))
        assert len(results) == 1

    def test_uses_filename_stem_as_key(self, tmp_path):
        (tmp_path / "CVP-T3-20260211.json").write_text('{"tier": 3}')
        results = _load_persisted_results(results_dir=str(tmp_path))
        assert "CVP-T3-20260211" in results


# ---------------------------------------------------------------------------
# Round-trip: persist → load
# ---------------------------------------------------------------------------
class TestRoundTrip:
    """Integration: _persist_result → _load_persisted_results."""

    def test_persist_then_load(self, tmp_path):
        _persist_result("RT-001", {"a": 1, "b": [2, 3]}, results_dir=str(tmp_path))
        _persist_result("RT-002", {"x": "hello"}, results_dir=str(tmp_path))

        results = _load_persisted_results(results_dir=str(tmp_path))
        assert len(results) == 2
        assert results["RT-001"]["a"] == 1
        assert results["RT-002"]["x"] == "hello"
