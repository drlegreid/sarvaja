"""
Unit tests for Orchestrator State Management.

Per DOC-SIZE-01-v1: Tests for workflows/orchestrator/state.py module.
Tests: create_initial_state, add_to_backlog, PRIORITY_ORDER, MAX_RETRIES.
"""

import pytest

from governance.workflows.orchestrator.state import (
    create_initial_state,
    add_to_backlog,
    PRIORITY_ORDER,
    MAX_RETRIES,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """Tests for module-level constants."""

    def test_priority_order(self):
        assert PRIORITY_ORDER["CRITICAL"] < PRIORITY_ORDER["HIGH"]
        assert PRIORITY_ORDER["HIGH"] < PRIORITY_ORDER["MEDIUM"]
        assert PRIORITY_ORDER["MEDIUM"] < PRIORITY_ORDER["LOW"]

    def test_max_retries(self):
        assert MAX_RETRIES == 3


# ---------------------------------------------------------------------------
# create_initial_state
# ---------------------------------------------------------------------------
class TestCreateInitialState:
    """Tests for create_initial_state()."""

    def test_default_state(self):
        state = create_initial_state()
        assert state["current_phase"] == "idle"
        assert state["status"] == "pending"
        assert state["backlog"] == []
        assert state["current_task"] is None
        assert state["cycles_completed"] == 0
        assert state["max_cycles"] == 10
        assert state["retry_count"] == 0
        assert state["dry_run"] is False

    def test_custom_max_cycles(self):
        state = create_initial_state(max_cycles=5)
        assert state["max_cycles"] == 5

    def test_dry_run_flag(self):
        state = create_initial_state(dry_run=True)
        assert state["dry_run"] is True

    def test_cycle_id_format(self):
        state = create_initial_state()
        assert state["cycle_id"].startswith("ORCH-")

    def test_empty_collections(self):
        state = create_initial_state()
        assert state["gaps_discovered"] == []
        assert state["cycle_history"] == []

    def test_null_fields(self):
        state = create_initial_state()
        assert state["specification"] is None
        assert state["implementation"] is None
        assert state["validation_results"] is None
        assert state["validation_passed"] is None
        assert state["gate_decision"] is None


# ---------------------------------------------------------------------------
# add_to_backlog
# ---------------------------------------------------------------------------
class TestAddToBacklog:
    """Tests for add_to_backlog()."""

    def test_adds_task(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "HIGH", "Fix bug")
        assert len(state["backlog"]) == 1
        assert state["backlog"][0]["task_id"] == "T-1"
        assert state["backlog"][0]["priority"] == "HIGH"
        assert state["backlog"][0]["description"] == "Fix bug"

    def test_sorts_by_priority(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "LOW", "Low task")
        state = add_to_backlog(state, "T-2", "CRITICAL", "Critical task")
        state = add_to_backlog(state, "T-3", "MEDIUM", "Medium task")

        assert state["backlog"][0]["task_id"] == "T-2"  # CRITICAL
        assert state["backlog"][1]["task_id"] == "T-3"  # MEDIUM
        assert state["backlog"][2]["task_id"] == "T-1"  # LOW

    def test_rejects_duplicates(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "HIGH", "First")
        state = add_to_backlog(state, "T-1", "CRITICAL", "Duplicate")
        assert len(state["backlog"]) == 1
        assert state["backlog"][0]["priority"] == "HIGH"  # original preserved

    def test_unknown_priority_sorts_last(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "HIGH", "Known")
        state = add_to_backlog(state, "T-2", "UNKNOWN", "Custom")
        assert state["backlog"][0]["task_id"] == "T-1"
        assert state["backlog"][1]["task_id"] == "T-2"

    def test_multiple_same_priority(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "HIGH", "First")
        state = add_to_backlog(state, "T-2", "HIGH", "Second")
        assert len(state["backlog"]) == 2

    def test_returns_state(self):
        state = create_initial_state()
        result = add_to_backlog(state, "T-1", "HIGH", "Task")
        assert result is not state  # returns new dict (immutable pattern)
