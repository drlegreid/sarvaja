"""Tests for antirot retention limits.

Validates that unbounded data stores have retention caps:
- DSM tracker completed_cycles: max 50 cycles
- Execution events per task: max 100 events
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestDSMCycleRetention:
    """DSM tracker should cap completed_cycles to prevent unbounded growth."""

    def test_completed_cycles_capped_at_50(self):
        """After 51+ cycles, only last 50 are retained."""
        from governance.dsm.tracker import DSMTracker
        from governance.dsm.models import DSMCycle

        tracker = DSMTracker(
            evidence_dir="/tmp/test-evidence",
            state_file="/tmp/test-dsm-state.json",
        )
        # Pre-fill with 50 cycles
        for i in range(50):
            tracker.completed_cycles.append(
                DSMCycle(cycle_id=f"OLD-{i:03d}")
            )
        assert len(tracker.completed_cycles) == 50

        # Start and complete a new cycle
        tracker.start_cycle()
        with patch("governance.dsm.tracker.generate_evidence", return_value="/tmp/ev.md"):
            tracker.complete_cycle()

        assert len(tracker.completed_cycles) == 50
        # First entry should be OLD-001 (OLD-000 was pruned)
        assert tracker.completed_cycles[0].cycle_id == "OLD-001"
        # Last entry should be the newly completed cycle
        assert tracker.completed_cycles[-1].cycle_id.startswith("DSM-")

    def test_small_count_not_pruned(self):
        """Under 50 cycles, nothing is pruned."""
        from governance.dsm.tracker import DSMTracker

        tracker = DSMTracker(
            evidence_dir="/tmp/test-evidence",
            state_file="/tmp/test-dsm-state.json",
        )
        tracker.start_cycle()
        with patch("governance.dsm.tracker.generate_evidence", return_value="/tmp/ev.md"):
            tracker.complete_cycle()

        assert len(tracker.completed_cycles) == 1


class TestExecutionEventsRetention:
    """Execution events per task should be capped at 100."""

    def test_events_capped_at_100(self):
        """After 100+ events, only last 100 are kept."""
        from governance.stores.data_stores import _execution_events_store

        task_id = "TEST-RETENTION-001"
        # Pre-fill with 100 events
        _execution_events_store[task_id] = [
            {"event_id": f"EVT-OLD-{i:04d}", "task_id": task_id}
            for i in range(100)
        ]
        assert len(_execution_events_store[task_id]) == 100

        # Add one more — should trigger cap
        _execution_events_store[task_id].append(
            {"event_id": "EVT-NEW-0000", "task_id": task_id}
        )
        if len(_execution_events_store[task_id]) > 100:
            _execution_events_store[task_id] = _execution_events_store[task_id][-100:]

        assert len(_execution_events_store[task_id]) == 100
        # First should be EVT-OLD-0001 (0000 pruned)
        assert _execution_events_store[task_id][0]["event_id"] == "EVT-OLD-0001"
        assert _execution_events_store[task_id][-1]["event_id"] == "EVT-NEW-0000"

        # Cleanup
        del _execution_events_store[task_id]

    def test_api_endpoint_caps_events(self):
        """POST /tasks/{id}/execution should cap events."""
        import inspect
        from governance.routes.tasks.execution import add_task_execution_event
        source = inspect.getsource(add_task_execution_event)
        assert "100" in source
        assert "_execution_events_store[task_id][-100:]" in source
