"""
Tests for test result persistence.

Per D.2: Persist test results across restarts.
Batch 160 deepening (was 2 tests, now 10).
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestResultPersistence:
    """Tests for test result file persistence."""

    def test_persist_result_writes_file(self):
        """_persist_result should write JSON file to results directory."""
        from governance.routes.tests.runner_store import _persist_result
        with tempfile.TemporaryDirectory() as tmpdir:
            result = {
                "status": "completed",
                "total": 10,
                "passed": 9,
                "failed": 1,
            }
            _persist_result("test-run-001", result, results_dir=tmpdir)
            written = Path(tmpdir) / "test-run-001.json"
            assert written.exists()
            data = json.loads(written.read_text())
            assert data["status"] == "completed"

    def test_load_persisted_results(self):
        """_load_persisted_results should read JSON files from directory."""
        from governance.routes.tests.runner_store import _load_persisted_results
        with tempfile.TemporaryDirectory() as tmpdir:
            result = {"status": "completed", "total": 5, "passed": 5}
            Path(tmpdir, "run-123.json").write_text(json.dumps(result))

            loaded = _load_persisted_results(results_dir=tmpdir)
            assert "run-123" in loaded
            assert loaded["run-123"]["status"] == "completed"

    def test_persist_creates_directory(self):
        """_persist_result should create the directory if missing."""
        from governance.routes.tests.runner_store import _persist_result
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = str(Path(tmpdir) / "nested" / "results")
            _persist_result("run-1", {"status": "ok"}, results_dir=subdir)
            assert Path(subdir, "run-1.json").exists()

    def test_load_empty_directory(self):
        """_load_persisted_results returns empty dict for empty dir."""
        from governance.routes.tests.runner_store import _load_persisted_results
        with tempfile.TemporaryDirectory() as tmpdir:
            loaded = _load_persisted_results(results_dir=tmpdir)
            assert loaded == {}

    def test_load_nonexistent_directory(self):
        """_load_persisted_results returns empty dict for missing dir."""
        from governance.routes.tests.runner_store import _load_persisted_results
        loaded = _load_persisted_results(results_dir="/nonexistent/path/xyzzy")
        assert loaded == {}

    def test_load_skips_corrupt_json(self):
        """_load_persisted_results skips files with invalid JSON."""
        from governance.routes.tests.runner_store import _load_persisted_results
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "good.json").write_text('{"status":"ok"}')
            Path(tmpdir, "bad.json").write_text("not json at all{{{")
            loaded = _load_persisted_results(results_dir=tmpdir)
            assert "good" in loaded
            assert "bad" not in loaded

    def test_load_caps_at_50_results(self):
        """_load_persisted_results should load at most 50 files."""
        from governance.routes.tests.runner_store import _load_persisted_results
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(60):
                Path(tmpdir, f"run-{i:03d}.json").write_text(
                    json.dumps({"status": "ok", "idx": i})
                )
            loaded = _load_persisted_results(results_dir=tmpdir)
            assert len(loaded) == 50

    def test_persist_handles_non_serializable(self):
        """_persist_result uses default=str for non-serializable values."""
        from governance.routes.tests.runner_store import _persist_result
        with tempfile.TemporaryDirectory() as tmpdir:
            result = {"status": "ok", "path": Path("/tmp")}
            _persist_result("run-path", result, results_dir=tmpdir)
            data = json.loads(Path(tmpdir, "run-path.json").read_text())
            assert data["path"] == "/tmp"


class TestResolveTestRoot:
    def test_resolve_returns_string(self):
        from governance.routes.tests.runner_store import _resolve_test_root
        root = _resolve_test_root()
        assert isinstance(root, str)

    def test_resolve_contains_tests_dir(self):
        from governance.routes.tests.runner_store import _resolve_test_root
        root = _resolve_test_root()
        assert Path(root, "tests").is_dir()
