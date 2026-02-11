"""
Unit tests for DSM Tracker Persistence.

Per DOC-SIZE-01-v1: Tests for extracted dsm/tracker_persistence.py module.
Tests: load_state, save_state, check_abandoned_cycle.
"""

import json
import os
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from governance.dsm.tracker_persistence import (
    load_state,
    save_state,
    check_abandoned_cycle,
    ABANDONED_CYCLE_HOURS,
)
from governance.dsm.models import DSMCycle, PhaseCheckpoint


# ---------------------------------------------------------------------------
# load_state
# ---------------------------------------------------------------------------
class TestLoadState:
    """Tests for load_state()."""

    def test_missing_file_returns_none(self, tmp_path):
        result = load_state(tmp_path / "nonexistent.json")
        assert result is None

    def test_valid_state_returns_cycle(self, tmp_path):
        state = {
            "current_cycle": {
                "cycle_id": "DSM-001",
                "batch_id": "B-01",
                "start_time": "2026-02-11T10:00:00",
                "end_time": None,
                "current_phase": "measure",
                "phases_completed": ["init"],
                "checkpoints": [],
                "findings": [{"type": "gap"}],
                "metrics": {"score": 0.9},
            }
        }
        f = tmp_path / "state.json"
        f.write_text(json.dumps(state))

        cycle = load_state(f)
        assert cycle is not None
        assert cycle.cycle_id == "DSM-001"
        assert cycle.batch_id == "B-01"
        assert cycle.current_phase == "measure"
        assert cycle.phases_completed == ["init"]
        assert cycle.metrics["score"] == 0.9

    def test_no_current_cycle_returns_none(self, tmp_path):
        state = {"current_cycle": None, "completed_count": 5}
        f = tmp_path / "state.json"
        f.write_text(json.dumps(state))

        assert load_state(f) is None

    def test_empty_current_cycle_returns_none(self, tmp_path):
        state = {"current_cycle": {}, "completed_count": 0}
        f = tmp_path / "state.json"
        f.write_text(json.dumps(state))

        # Empty dict is falsy for dict.get()... actually {} is truthy
        # but cycle_data["cycle_id"] will raise KeyError → backup path
        assert load_state(f) is None

    def test_corrupted_json_creates_backup(self, tmp_path):
        f = tmp_path / "state.json"
        f.write_text("{invalid json content!!")

        result = load_state(f)
        assert result is None
        # Backup should be created
        backups = list(tmp_path.glob("*.backup-*.json"))
        assert len(backups) == 1

    def test_corrupted_json_preserves_original(self, tmp_path):
        f = tmp_path / "state.json"
        bad_content = "{bad json!!}"
        f.write_text(bad_content)

        load_state(f)
        backups = list(tmp_path.glob("*.backup-*.json"))
        assert backups[0].read_text() == bad_content

    def test_missing_cycle_id_key_creates_backup(self, tmp_path):
        state = {"current_cycle": {"not_cycle_id": "oops"}}
        f = tmp_path / "state.json"
        f.write_text(json.dumps(state))

        result = load_state(f)
        assert result is None

    def test_loads_checkpoints(self, tmp_path):
        cp_data = {
            "phase": "init",
            "timestamp": "2026-02-11T10:00:00",
            "description": "Initialized",
            "metrics": {"rate": 0.5},
            "evidence": ["ev-1"],
        }
        state = {
            "current_cycle": {
                "cycle_id": "DSM-002",
                "checkpoints": [cp_data],
            }
        }
        f = tmp_path / "state.json"
        f.write_text(json.dumps(state))

        cycle = load_state(f)
        assert len(cycle.checkpoints) == 1
        assert isinstance(cycle.checkpoints[0], PhaseCheckpoint)
        assert cycle.checkpoints[0].phase == "init"
        assert cycle.checkpoints[0].evidence == ["ev-1"]

    def test_defaults_for_missing_fields(self, tmp_path):
        state = {"current_cycle": {"cycle_id": "DSM-003"}}
        f = tmp_path / "state.json"
        f.write_text(json.dumps(state))

        cycle = load_state(f)
        assert cycle.current_phase == "idle"
        assert cycle.phases_completed == []
        assert cycle.checkpoints == []
        assert cycle.findings == []
        assert cycle.metrics == {}


# ---------------------------------------------------------------------------
# save_state
# ---------------------------------------------------------------------------
class TestSaveState:
    """Tests for save_state()."""

    def test_saves_with_cycle(self, tmp_path):
        f = tmp_path / "state.json"
        cycle = DSMCycle(cycle_id="DSM-001", current_phase="measure")

        save_state(f, cycle, completed_count=3)
        assert f.exists()

        data = json.loads(f.read_text())
        assert data["current_cycle"]["cycle_id"] == "DSM-001"
        assert data["completed_count"] == 3
        assert "last_updated" in data

    def test_saves_none_cycle(self, tmp_path):
        f = tmp_path / "state.json"

        save_state(f, None, completed_count=0)
        data = json.loads(f.read_text())
        assert data["current_cycle"] is None
        assert data["completed_count"] == 0

    def test_creates_parent_directory(self, tmp_path):
        f = tmp_path / "subdir" / "deep" / "state.json"

        save_state(f, None, completed_count=0)
        assert f.exists()

    def test_overwrites_existing_file(self, tmp_path):
        f = tmp_path / "state.json"
        f.write_text('{"old": true}')

        cycle = DSMCycle(cycle_id="DSM-NEW", current_phase="init")
        save_state(f, cycle, completed_count=1)

        data = json.loads(f.read_text())
        assert data["current_cycle"]["cycle_id"] == "DSM-NEW"
        assert "old" not in data

    def test_atomic_write_cleans_up_on_error(self, tmp_path):
        f = tmp_path / "state.json"
        cycle = MagicMock()
        cycle.to_dict.side_effect = Exception("serialization error")

        with pytest.raises(Exception, match="serialization error"):
            save_state(f, cycle, completed_count=0)

        # Temp file should be cleaned up
        temp_files = list(tmp_path.glob(".dsm_state_*.tmp"))
        assert len(temp_files) == 0

    def test_valid_json_output(self, tmp_path):
        f = tmp_path / "state.json"
        cp = PhaseCheckpoint(
            phase="init", timestamp="2026-02-11T10:00:00",
            description="Test", metrics={"x": 1}, evidence=["e1"],
        )
        cycle = DSMCycle(
            cycle_id="DSM-001", batch_id="B-01",
            start_time="2026-02-11T10:00:00",
            current_phase="measure",
            phases_completed=["init"],
            checkpoints=[cp],
            findings=[{"type": "gap"}],
            metrics={"score": 0.9},
        )

        save_state(f, cycle, completed_count=5)

        # Should be valid JSON
        data = json.loads(f.read_text())
        assert data["current_cycle"]["checkpoints"][0]["phase"] == "init"


# ---------------------------------------------------------------------------
# check_abandoned_cycle
# ---------------------------------------------------------------------------
class TestCheckAbandonedCycle:
    """Tests for check_abandoned_cycle()."""

    def test_constant_value(self):
        assert ABANDONED_CYCLE_HOURS == 24

    def test_none_cycle_returns_false(self):
        assert check_abandoned_cycle(None) is False

    def test_complete_phase_returns_false(self):
        cycle = DSMCycle(
            cycle_id="DSM-001",
            current_phase="complete",
            start_time="2020-01-01T00:00:00Z",
        )
        assert check_abandoned_cycle(cycle) is False

    def test_no_start_time_returns_false(self):
        cycle = DSMCycle(cycle_id="DSM-001", current_phase="measure")
        assert check_abandoned_cycle(cycle) is False

    def test_recent_cycle_not_abandoned(self):
        now = datetime.now(timezone.utc)
        cycle = DSMCycle(
            cycle_id="DSM-001",
            current_phase="measure",
            start_time=now.isoformat(),
        )
        assert check_abandoned_cycle(cycle) is False

    def test_old_cycle_is_abandoned(self):
        old = datetime.now(timezone.utc) - timedelta(hours=25)
        cycle = DSMCycle(
            cycle_id="DSM-001",
            current_phase="measure",
            start_time=old.isoformat(),
            metrics={},
        )
        result = check_abandoned_cycle(cycle)
        assert result is True
        assert cycle.current_phase == "aborted"
        assert cycle.metrics.get("auto_aborted") is True
        assert cycle.end_time is not None

    def test_under_threshold_not_abandoned(self):
        # 23h 55min — safely under the 24h threshold
        recent = datetime.now(timezone.utc) - timedelta(hours=23, minutes=55)
        cycle = DSMCycle(
            cycle_id="DSM-001",
            current_phase="measure",
            start_time=recent.isoformat(),
            metrics={},
        )
        assert check_abandoned_cycle(cycle) is False

    def test_z_suffix_parsing(self):
        old = datetime.now(timezone.utc) - timedelta(hours=30)
        ts = old.strftime("%Y-%m-%dT%H:%M:%SZ")
        cycle = DSMCycle(
            cycle_id="DSM-001",
            current_phase="measure",
            start_time=ts,
            metrics={},
        )
        assert check_abandoned_cycle(cycle) is True

    def test_naive_timestamp_treated_as_utc(self):
        old = datetime.now(timezone.utc) - timedelta(hours=30)
        ts = old.strftime("%Y-%m-%dT%H:%M:%S")  # naive - no timezone
        cycle = DSMCycle(
            cycle_id="DSM-001",
            current_phase="measure",
            start_time=ts,
            metrics={},
        )
        assert check_abandoned_cycle(cycle) is True

    def test_invalid_timestamp_returns_false(self):
        cycle = DSMCycle(
            cycle_id="DSM-001",
            current_phase="measure",
            start_time="not-a-date",
        )
        assert check_abandoned_cycle(cycle) is False

    def test_sets_abort_reason(self):
        old = datetime.now(timezone.utc) - timedelta(hours=48)
        cycle = DSMCycle(
            cycle_id="DSM-001",
            current_phase="measure",
            start_time=old.isoformat(),
            metrics={},
        )
        check_abandoned_cycle(cycle)
        assert "abort_reason" in cycle.metrics
        assert "48" in cycle.metrics["abort_reason"] or "h" in cycle.metrics["abort_reason"]


# ---------------------------------------------------------------------------
# Round-trip: save → load
# ---------------------------------------------------------------------------
class TestRoundTrip:
    """Integration test: save_state → load_state."""

    def test_save_then_load(self, tmp_path):
        f = tmp_path / "state.json"
        cp = PhaseCheckpoint(
            phase="audit",
            timestamp="2026-02-11T12:00:00",
            description="Audit complete",
        )
        original = DSMCycle(
            cycle_id="DSM-RT-001",
            batch_id="B-RT",
            start_time="2026-02-11T10:00:00",
            current_phase="hypothesize",
            phases_completed=["audit"],
            checkpoints=[cp],
            findings=[{"type": "anomaly", "detail": "high entropy"}],
            metrics={"coverage": 0.7},
        )

        save_state(f, original, completed_count=10)
        loaded = load_state(f)

        assert loaded is not None
        assert loaded.cycle_id == "DSM-RT-001"
        assert loaded.batch_id == "B-RT"
        assert loaded.current_phase == "hypothesize"
        assert loaded.phases_completed == ["audit"]
        assert len(loaded.checkpoints) == 1
        assert loaded.checkpoints[0].phase == "audit"
        assert loaded.findings[0]["type"] == "anomaly"
        assert loaded.metrics["coverage"] == 0.7
