"""
Tests for test result persistence.

Per D.2: Persist test results across restarts.
Verifies:
- Test results are written to JSON files
- On startup, existing results are loaded from disk
- Results survive in-memory dict reset

Created: 2026-02-01
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
        from governance.routes.tests.runner import _persist_result
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
        from governance.routes.tests.runner import _load_persisted_results
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a result file
            result = {"status": "completed", "total": 5, "passed": 5}
            Path(tmpdir, "run-123.json").write_text(json.dumps(result))

            loaded = _load_persisted_results(results_dir=tmpdir)
            assert "run-123" in loaded
            assert loaded["run-123"]["status"] == "completed"
