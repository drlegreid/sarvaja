"""
Unit tests for DSP LangGraph State Schema.

Per DOC-SIZE-01-v1: Tests for dsm/langgraph/state.py module.
Tests: PhaseResult, DSPState, constants, create_initial_state().
"""

from governance.dsm.langgraph.state import (
    PhaseResult,
    DSPState,
    MIN_CHECKPOINT_CHARS,
    MIN_FINDING_COUNT,
    MIN_HYPOTHESIS_CHARS,
    MIN_MEASUREMENT_METRICS,
    MAX_CYCLE_HOURS,
    MAX_PHASE_RETRIES,
    CRITICAL_SEVERITY_THRESHOLD,
    create_initial_state,
)


class TestConstants:
    def test_thresholds(self):
        assert MIN_CHECKPOINT_CHARS == 20
        assert MIN_FINDING_COUNT == 1
        assert MIN_HYPOTHESIS_CHARS == 30
        assert MIN_MEASUREMENT_METRICS == 1

    def test_limits(self):
        assert MAX_CYCLE_HOURS == 24
        assert MAX_PHASE_RETRIES == 3
        assert CRITICAL_SEVERITY_THRESHOLD == 3


class TestCreateInitialState:
    def test_defaults(self):
        state = create_initial_state()
        assert state["current_phase"] == "idle"
        assert state["status"] == "pending"
        assert state["dry_run"] is False
        assert state["force_advance"] is False
        assert state["retry_count"] == 0
        assert state["available_mcps"] == []

    def test_custom(self):
        state = create_initial_state(
            batch_id="BATCH-1", dry_run=True,
            available_mcps=["governance"],
            force_advance=True,
        )
        assert state["batch_id"] == "BATCH-1"
        assert state["dry_run"] is True
        assert state["force_advance"] is True
        assert "governance" in state["available_mcps"]

    def test_cycle_id_format(self):
        state = create_initial_state()
        assert state["cycle_id"].startswith("DSM-")

    def test_empty_collections(self):
        state = create_initial_state()
        assert state["phases_completed"] == []
        assert state["checkpoints"] == []
        assert state["findings"] == []
        assert state["hypotheses"] == []
        assert state["evidence_files"] == []

    def test_boolean_defaults(self):
        state = create_initial_state()
        assert state["has_critical_gaps"] is False
        assert state["validation_passed"] is False
        assert state["should_skip_dream"] is False

    def test_none_fields(self):
        state = create_initial_state()
        assert state["batch_id"] is None
        assert state["error_message"] is None
        assert state["abort_reason"] is None
        assert state["started_at"] is None
