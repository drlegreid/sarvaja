"""
Unit tests for DSM Tracker Persistence.

Per DOC-SIZE-01-v1: Tests for extracted tracker_persistence.py module.
Tests: load_state, save_state, check_abandoned_cycle.
"""

import json
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
from governance.dsm.models import DSMCycle


@pytest.fixture
def state_file(tmp_path):
    return tmp_path / ".dsm_state.json"


@pytest.fixture
def sample_cycle():
    return DSMCycle(
        cycle_id="DSM-001",
        batch_id="B-01",
        start_time=datetime.now(timezone.utc).isoformat(),
        current_phase="measure",
        phases_completed=["init", "hypothesize"],
        checkpoints=[],
        findings=["finding-1"],
        metrics={"score": 0.8},
    )


class TestLoadState:
    """Tests for load_state()."""

    def test_file_not_exists(self, state_file):
        assert load_state(state_file) is None

    def test_loads_cycle(self, state_file):
        state = {
            "current_cycle": {
                "cycle_id": "DSM-001",
                "batch_id": "B-01",
                "start_time": "2026-02-11T10:00:00",
                "end_time": None,
                "current_phase": "measure",
                "phases_completed": ["init"],
                "checkpoints": [],
                "findings": [],
                "metrics": {},
            },
            "completed_count": 5,
        }
        state_file.write_text(json.dumps(state))
        cycle = load_state(state_file)
        assert cycle is not None
        assert cycle.cycle_id == "DSM-001"
        assert cycle.current_phase == "measure"

    def test_no_current_cycle_returns_none(self, state_file):
        state_file.write_text(json.dumps({"current_cycle": None, "completed_count": 3}))
        assert load_state(state_file) is None

    def test_corrupted_json_returns_none(self, state_file):
        state_file.write_text("{invalid json")
        assert load_state(state_file) is None

    def test_corrupted_creates_backup(self, state_file):
        state_file.write_text("{bad")
        load_state(state_file)
        backups = list(state_file.parent.glob("*.backup-*.json"))
        assert len(backups) == 1


class TestSaveState:
    """Tests for save_state()."""

    def test_saves_with_cycle(self, state_file, sample_cycle):
        save_state(state_file, sample_cycle, 5)
        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["current_cycle"]["cycle_id"] == "DSM-001"
        assert data["completed_count"] == 5
        assert "last_updated" in data

    def test_saves_without_cycle(self, state_file):
        save_state(state_file, None, 10)
        data = json.loads(state_file.read_text())
        assert data["current_cycle"] is None
        assert data["completed_count"] == 10

    def test_creates_parent_dirs(self, tmp_path):
        deep = tmp_path / "a" / "b" / "state.json"
        save_state(deep, None, 0)
        assert deep.exists()

    def test_atomic_write(self, state_file, sample_cycle):
        # Write initial data
        save_state(state_file, None, 0)
        # Overwrite with cycle
        save_state(state_file, sample_cycle, 1)
        data = json.loads(state_file.read_text())
        assert data["current_cycle"]["cycle_id"] == "DSM-001"


class TestCheckAbandonedCycle:
    """Tests for check_abandoned_cycle()."""

    def test_none_cycle(self):
        assert check_abandoned_cycle(None) is False

    def test_completed_cycle_not_abandoned(self):
        cycle = DSMCycle(
            cycle_id="DSM-001",
            start_time=datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat(),
            current_phase="complete",
        )
        assert check_abandoned_cycle(cycle) is False

    def test_recent_cycle_not_abandoned(self):
        cycle = DSMCycle(
            cycle_id="DSM-001",
            start_time=datetime.now(timezone.utc).isoformat(),
            current_phase="measure",
        )
        assert check_abandoned_cycle(cycle) is False

    def test_old_cycle_is_abandoned(self):
        old = datetime.now(timezone.utc) - timedelta(hours=ABANDONED_CYCLE_HOURS + 1)
        cycle = DSMCycle(
            cycle_id="DSM-OLD",
            start_time=old.isoformat(),
            current_phase="hypothesize",
            metrics={},
        )
        result = check_abandoned_cycle(cycle)
        assert result is True
        assert cycle.current_phase == "aborted"
        assert cycle.metrics.get("auto_aborted") is True

    def test_no_start_time(self):
        cycle = DSMCycle(cycle_id="DSM-001", current_phase="measure")
        assert check_abandoned_cycle(cycle) is False

    def test_z_suffix_timezone(self):
        old = datetime.now(timezone.utc) - timedelta(hours=30)
        cycle = DSMCycle(
            cycle_id="DSM-Z",
            start_time=old.strftime("%Y-%m-%dT%H:%M:%SZ"),
            current_phase="init",
            metrics={},
        )
        assert check_abandoned_cycle(cycle) is True
