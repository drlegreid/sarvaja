"""
Unit tests for Compat - DSM Tracker Exports.

Per DOC-SIZE-01-v1: Tests for compat/dsm.py module.
Tests: dsm_start, dsm_advance, dsm_checkpoint, dsm_status,
       dsm_complete, dsm_finding, dsm_metrics.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from governance.dsm.tracker import DSMTracker, reset_tracker


@pytest.fixture(autouse=True)
def _fresh_tracker(tmp_path):
    """Reset tracker singleton and provide temp paths."""
    reset_tracker()
    yield tmp_path
    reset_tracker()


def _make_tracker(tmp_path):
    """Create a DSMTracker with temp directories."""
    return DSMTracker(
        evidence_dir=str(tmp_path),
        state_file=str(tmp_path / "state.json"),
    )


class TestDsmStart:
    """Tests for dsm_start()."""

    @patch("governance.compat.dsm._DSM_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.dsm import dsm_start
        result = json.loads(dsm_start())
        assert "error" in result

    def test_success(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_start
            result = json.loads(dsm_start("batch-1"))
            assert "cycle_id" in result
            assert result["batch_id"] == "batch-1"

    def test_double_start_error(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_start
            dsm_start("batch-1")
            result = json.loads(dsm_start("batch-2"))
            assert "error" in result


class TestDsmAdvance:
    """Tests for dsm_advance()."""

    @patch("governance.compat.dsm._DSM_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.dsm import dsm_advance
        result = json.loads(dsm_advance())
        assert "error" in result

    def test_no_cycle_error(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_advance
            result = json.loads(dsm_advance())
            assert "error" in result


class TestDsmCheckpoint:
    """Tests for dsm_checkpoint()."""

    @patch("governance.compat.dsm._DSM_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.dsm import dsm_checkpoint
        result = json.loads(dsm_checkpoint("test"))
        assert "error" in result

    def test_invalid_metrics_json(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_checkpoint
            result = json.loads(dsm_checkpoint("test", metrics="{bad json"))
            assert "error" in result

    def test_metrics_as_dict(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        tracker.start_cycle()
        tracker.advance_phase()  # Move past IDLE
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_checkpoint
            result = json.loads(dsm_checkpoint("test cp", metrics={"score": 0.9}))
            assert result.get("message") == "Checkpoint recorded"


class TestDsmStatus:
    """Tests for dsm_status()."""

    @patch("governance.compat.dsm._DSM_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.dsm import dsm_status
        result = json.loads(dsm_status())
        assert "error" in result

    def test_returns_status(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_status
            result = json.loads(dsm_status())
            assert isinstance(result, dict)


class TestDsmComplete:
    """Tests for dsm_complete()."""

    @patch("governance.compat.dsm._DSM_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.dsm import dsm_complete
        result = json.loads(dsm_complete())
        assert "error" in result

    def test_no_cycle_error(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_complete
            result = json.loads(dsm_complete())
            assert "error" in result


class TestDsmFinding:
    """Tests for dsm_finding()."""

    @patch("governance.compat.dsm._DSM_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.dsm import dsm_finding
        result = json.loads(dsm_finding("bug", "test"))
        assert "error" in result

    def test_no_cycle_error(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_finding
            result = json.loads(dsm_finding("bug", "test"))
            assert "error" in result

    def test_parses_csv_rules(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        tracker.start_cycle()
        tracker.advance_phase()
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_finding
            result = json.loads(dsm_finding("gap", "desc", related_rules="R-1, R-2"))
            assert result["related_rules"] == ["R-1", "R-2"]


class TestDsmMetrics:
    """Tests for dsm_metrics()."""

    @patch("governance.compat.dsm._DSM_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.dsm import dsm_metrics
        result = json.loads(dsm_metrics("{}"))
        assert "error" in result

    def test_invalid_json(self, _fresh_tracker):
        tracker = _make_tracker(_fresh_tracker)
        with patch("governance.compat.dsm.get_tracker", return_value=tracker):
            from governance.compat.dsm import dsm_metrics
            result = json.loads(dsm_metrics("{invalid"))
            assert "error" in result
