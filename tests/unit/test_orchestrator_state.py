"""
Unit tests for Orchestrator State.

Per DOC-SIZE-01-v1: Tests for workflows/orchestrator/state.py module.
Tests: create_initial_state(), add_to_backlog(), PRIORITY_ORDER, MAX_RETRIES.
"""

from governance.workflows.orchestrator.state import (
    create_initial_state,
    add_to_backlog,
    PRIORITY_ORDER,
    MAX_RETRIES,
)


class TestConstants:
    def test_priority_order(self):
        assert PRIORITY_ORDER["CRITICAL"] < PRIORITY_ORDER["HIGH"]
        assert PRIORITY_ORDER["HIGH"] < PRIORITY_ORDER["MEDIUM"]
        assert PRIORITY_ORDER["MEDIUM"] < PRIORITY_ORDER["LOW"]

    def test_max_retries(self):
        assert MAX_RETRIES == 3


class TestCreateInitialState:
    def test_defaults(self):
        state = create_initial_state()
        assert state["current_phase"] == "idle"
        assert state["status"] == "pending"
        assert state["backlog"] == []
        assert state["current_task"] is None
        assert state["cycles_completed"] == 0
        assert state["max_cycles"] == 10
        assert state["dry_run"] is False
        assert state["retry_count"] == 0

    def test_custom_max_cycles(self):
        state = create_initial_state(max_cycles=5)
        assert state["max_cycles"] == 5

    def test_dry_run(self):
        state = create_initial_state(dry_run=True)
        assert state["dry_run"] is True

    def test_cycle_id_format(self):
        state = create_initial_state()
        assert state["cycle_id"].startswith("ORCH-")

    def test_empty_history(self):
        state = create_initial_state()
        assert state["cycle_history"] == []
        assert state["gaps_discovered"] == []


class TestAddToBacklog:
    def test_add_single(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "HIGH", "Fix bug")
        assert len(state["backlog"]) == 1
        assert state["backlog"][0]["task_id"] == "T-1"

    def test_sorted_by_priority(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "LOW", "Low task")
        state = add_to_backlog(state, "T-2", "CRITICAL", "Critical task")
        state = add_to_backlog(state, "T-3", "HIGH", "High task")
        assert state["backlog"][0]["priority"] == "CRITICAL"
        assert state["backlog"][1]["priority"] == "HIGH"
        assert state["backlog"][2]["priority"] == "LOW"

    def test_reject_duplicate(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "HIGH", "First")
        state = add_to_backlog(state, "T-1", "LOW", "Duplicate")
        assert len(state["backlog"]) == 1
        assert state["backlog"][0]["priority"] == "HIGH"  # original kept

    def test_unknown_priority_sorts_last(self):
        state = create_initial_state()
        state = add_to_backlog(state, "T-1", "HIGH", "Known")
        state = add_to_backlog(state, "T-2", "WEIRD", "Unknown")
        assert state["backlog"][0]["priority"] == "HIGH"
        assert state["backlog"][1]["priority"] == "WEIRD"
