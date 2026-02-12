"""
Unit tests for DSM Tracker.

Per DOC-SIZE-01-v1: Tests for dsm/tracker.py module.
Tests: DSMTracker lifecycle, start_cycle, advance_phase, checkpoint, etc.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from governance.dsm.tracker import DSMTracker, get_tracker, reset_tracker
from governance.dsm.phases import DSPPhase


@pytest.fixture
def tracker(tmp_path):
    """Create a tracker with temp dirs."""
    return DSMTracker(
        evidence_dir=str(tmp_path / "evidence"),
        state_file=str(tmp_path / "state.json"),
    )


@pytest.fixture(autouse=True)
def _reset_global():
    """Reset global tracker after each test."""
    yield
    reset_tracker()


class TestDSMTrackerInit:
    """Tests for DSMTracker initialization."""

    def test_no_active_cycle(self, tracker):
        assert tracker.current_cycle is None
        assert tracker.completed_cycles == []

    def test_custom_dirs(self, tmp_path):
        t = DSMTracker(evidence_dir=str(tmp_path), state_file=str(tmp_path / "s.json"))
        assert t.evidence_dir == tmp_path
        assert t.state_file == tmp_path / "s.json"


class TestStartCycle:
    """Tests for start_cycle()."""

    def test_basic(self, tracker):
        cycle = tracker.start_cycle()
        assert cycle is not None
        assert cycle.cycle_id.startswith("DSM-")
        assert cycle.current_phase == "idle"

    def test_with_batch_id(self, tracker):
        cycle = tracker.start_cycle(batch_id="BATCH-001")
        assert cycle.batch_id == "BATCH-001"

    def test_raises_if_cycle_active(self, tracker):
        tracker.start_cycle()
        with pytest.raises(ValueError, match="already in progress"):
            tracker.start_cycle()


class TestGetCurrentPhase:
    """Tests for get_current_phase()."""

    def test_no_cycle(self, tracker):
        assert tracker.get_current_phase() == DSPPhase.IDLE

    def test_after_start(self, tracker):
        tracker.start_cycle()
        assert tracker.get_current_phase() == DSPPhase.IDLE


class TestAdvancePhase:
    """Tests for advance_phase()."""

    def test_no_cycle_raises(self, tracker):
        with pytest.raises(ValueError, match="No cycle"):
            tracker.advance_phase()

    def test_idle_to_audit(self, tracker):
        tracker.start_cycle()
        phase = tracker.advance_phase()
        assert phase == DSPPhase.AUDIT

    def test_force_advance(self, tracker):
        tracker.start_cycle()
        tracker.advance_phase()  # IDLE -> AUDIT
        # Force advance without evidence
        phase = tracker.advance_phase(force=True)
        assert phase == DSPPhase.HYPOTHESIZE


class TestGoToPhase:
    """Tests for go_to_phase()."""

    def test_no_cycle_raises(self, tracker):
        with pytest.raises(ValueError, match="No cycle"):
            tracker.go_to_phase(DSPPhase.AUDIT)

    def test_jump_to_phase(self, tracker):
        tracker.start_cycle()
        result = tracker.go_to_phase(DSPPhase.MEASURE)
        assert result == DSPPhase.MEASURE
        assert tracker.get_current_phase() == DSPPhase.MEASURE

    def test_cannot_jump_to_idle(self, tracker):
        tracker.start_cycle()
        with pytest.raises(ValueError, match="Cannot jump"):
            tracker.go_to_phase(DSPPhase.IDLE)

    def test_cannot_jump_to_complete(self, tracker):
        tracker.start_cycle()
        with pytest.raises(ValueError, match="Cannot jump"):
            tracker.go_to_phase(DSPPhase.COMPLETE)


class TestCheckpoint:
    """Tests for checkpoint()."""

    def test_no_cycle_raises(self, tracker):
        with pytest.raises(ValueError, match="No cycle"):
            tracker.checkpoint("test")

    def test_basic(self, tracker):
        tracker.start_cycle()
        cp = tracker.checkpoint("Initial checkpoint")
        assert cp.description == "Initial checkpoint"
        assert len(tracker.current_cycle.checkpoints) == 1

    def test_with_metrics(self, tracker):
        tracker.start_cycle()
        cp = tracker.checkpoint("With metrics", metrics={"score": 0.9})
        assert cp.metrics["score"] == 0.9

    def test_with_evidence(self, tracker):
        tracker.start_cycle()
        cp = tracker.checkpoint("With evidence", evidence=["file.md"])
        assert "file.md" in cp.evidence


class TestAddFinding:
    """Tests for add_finding()."""

    def test_no_cycle_raises(self, tracker):
        with pytest.raises(ValueError, match="No cycle"):
            tracker.add_finding("gap", "test")

    def test_basic(self, tracker):
        tracker.start_cycle()
        f = tracker.add_finding("gap", "Missing coverage")
        assert f["type"] == "gap"
        assert f["severity"] == "MEDIUM"
        assert f["id"] == "FINDING-001"

    def test_sequential_ids(self, tracker):
        tracker.start_cycle()
        f1 = tracker.add_finding("gap", "Gap 1")
        f2 = tracker.add_finding("orphan", "Orphan 1")
        assert f1["id"] == "FINDING-001"
        assert f2["id"] == "FINDING-002"

    def test_with_rules(self, tracker):
        tracker.start_cycle()
        f = tracker.add_finding("conflict", "Overlap", related_rules=["RULE-001"])
        assert "RULE-001" in f["related_rules"]


class TestUpdateMetrics:
    """Tests for update_metrics()."""

    def test_no_cycle_raises(self, tracker):
        with pytest.raises(ValueError, match="No cycle"):
            tracker.update_metrics({"score": 1})

    def test_basic(self, tracker):
        tracker.start_cycle()
        tracker.update_metrics({"files_scanned": 10})
        assert tracker.current_cycle.metrics["files_scanned"] == 10

    def test_merge(self, tracker):
        tracker.start_cycle()
        tracker.update_metrics({"a": 1})
        tracker.update_metrics({"b": 2})
        assert tracker.current_cycle.metrics["a"] == 1
        assert tracker.current_cycle.metrics["b"] == 2


class TestCompleteCycle:
    """Tests for complete_cycle()."""

    def test_no_cycle_raises(self, tracker):
        with pytest.raises(ValueError, match="No cycle"):
            tracker.complete_cycle()

    def test_completes_and_archives(self, tracker):
        tracker.start_cycle()
        tracker.advance_phase()  # IDLE -> AUDIT
        tracker.checkpoint("Done audit")
        evidence_path = tracker.complete_cycle()
        assert tracker.current_cycle is None
        assert len(tracker.completed_cycles) == 1
        assert evidence_path  # Returns a path

    def test_retention_cap_50(self, tracker):
        for i in range(55):
            tracker.start_cycle(batch_id=f"B-{i}")
            tracker.advance_phase()  # IDLE -> AUDIT
            tracker.checkpoint(f"CP {i}")
            tracker.complete_cycle()
        assert len(tracker.completed_cycles) <= 50


class TestAbortCycle:
    """Tests for abort_cycle()."""

    def test_no_cycle_no_error(self, tracker):
        tracker.abort_cycle()  # Should not raise

    def test_abort_clears_cycle(self, tracker):
        tracker.start_cycle()
        tracker.abort_cycle(reason="Testing")
        assert tracker.current_cycle is None


class TestGetStatus:
    """Tests for get_status()."""

    def test_no_cycle(self, tracker):
        status = tracker.get_status()
        assert status["active"] is False

    def test_active_cycle(self, tracker):
        tracker.start_cycle()
        status = tracker.get_status()
        assert status["active"] is True
        assert "cycle_id" in status
        assert "progress" in status
        assert status["current_phase"] == "idle"


class TestToDict:
    """Tests for to_dict()."""

    def test_no_cycle(self, tracker):
        d = tracker.to_dict()
        assert d["current_cycle"] is None
        assert d["completed_cycles_count"] == 0

    def test_with_cycle(self, tracker):
        tracker.start_cycle()
        d = tracker.to_dict()
        assert d["current_cycle"] is not None


class TestToJson:
    """Tests for to_json()."""

    def test_valid_json(self, tracker):
        j = tracker.to_json()
        parsed = json.loads(j)
        assert "current_cycle" in parsed


class TestGlobalTracker:
    """Tests for get_tracker() and reset_tracker()."""

    def test_get_tracker_returns_instance(self):
        t = get_tracker()
        assert isinstance(t, DSMTracker)

    def test_singleton(self):
        t1 = get_tracker()
        t2 = get_tracker()
        assert t1 is t2

    def test_reset_creates_new(self):
        t1 = get_tracker()
        reset_tracker()
        t2 = get_tracker()
        assert t1 is not t2
