"""
Unit tests for DSP LangGraph State Schema.

Per DOC-SIZE-01-v1: Tests for extracted state.py module.
Tests: create_initial_state, constants, PhaseResult, DSPState.
"""

import pytest

from governance.dsm.langgraph.state import (
    create_initial_state,
    MIN_CHECKPOINT_CHARS,
    MIN_FINDING_COUNT,
    MIN_HYPOTHESIS_CHARS,
    MIN_MEASUREMENT_METRICS,
    MAX_CYCLE_HOURS,
    MAX_PHASE_RETRIES,
    CRITICAL_SEVERITY_THRESHOLD,
)


class TestConstants:
    """Tests for DSP state constants."""

    def test_min_checkpoint_chars(self):
        assert MIN_CHECKPOINT_CHARS == 20

    def test_min_finding_count(self):
        assert MIN_FINDING_COUNT == 1

    def test_min_hypothesis_chars(self):
        assert MIN_HYPOTHESIS_CHARS == 30

    def test_min_measurement_metrics(self):
        assert MIN_MEASUREMENT_METRICS == 1

    def test_max_cycle_hours(self):
        assert MAX_CYCLE_HOURS == 24

    def test_max_phase_retries(self):
        assert MAX_PHASE_RETRIES == 3

    def test_critical_severity_threshold(self):
        assert CRITICAL_SEVERITY_THRESHOLD == 3


class TestCreateInitialState:
    """Tests for create_initial_state() function."""

    def test_default_state(self):
        state = create_initial_state()
        assert state["cycle_id"].startswith("DSM-")
        assert state["batch_id"] is None
        assert state["current_phase"] == "idle"
        assert state["phases_completed"] == []
        assert state["phase_results"] == []
        assert state["status"] == "pending"

    def test_with_batch_id(self):
        state = create_initial_state(batch_id="BATCH-001")
        assert state["batch_id"] == "BATCH-001"

    def test_with_dry_run(self):
        state = create_initial_state(dry_run=True)
        assert state["dry_run"] is True

    def test_with_available_mcps(self):
        mcps = ["claude-mem", "governance"]
        state = create_initial_state(available_mcps=mcps)
        assert state["available_mcps"] == ["claude-mem", "governance"]

    def test_default_mcps_empty(self):
        state = create_initial_state()
        assert state["available_mcps"] == []

    def test_with_force_advance(self):
        state = create_initial_state(force_advance=True)
        assert state["force_advance"] is True

    def test_empty_collections(self):
        state = create_initial_state()
        assert state["checkpoints"] == []
        assert state["findings"] == []
        assert state["metrics"] == {}
        assert state["evidence_files"] == []
        assert state["audit_gaps"] == []
        assert state["audit_orphans"] == []
        assert state["hypotheses"] == []
        assert state["measurements"] == {}
        assert state["optimizations_applied"] == []
        assert state["validation_results"] == {}
        assert state["dream_insights"] == []

    def test_decision_routing_defaults(self):
        state = create_initial_state()
        assert state["has_critical_gaps"] is False
        assert state["validation_passed"] is False
        assert state["should_skip_dream"] is False

    def test_error_fields_none(self):
        state = create_initial_state()
        assert state["error_message"] is None
        assert state["abort_reason"] is None
        assert state["started_at"] is None
        assert state["completed_at"] is None

    def test_retry_count_zero(self):
        state = create_initial_state()
        assert state["retry_count"] == 0

    def test_cycle_id_format(self):
        state = create_initial_state()
        # DSM-YYYY-MM-DD-HHMMSS
        parts = state["cycle_id"].split("-")
        assert parts[0] == "DSM"
        assert len(parts) >= 4

    def test_missing_mcps_empty(self):
        state = create_initial_state()
        assert state["missing_mcps"] == []

    def test_independent_instances(self):
        """Verify each call creates independent state objects."""
        s1 = create_initial_state()
        s2 = create_initial_state()
        s1["checkpoints"].append({"test": True})
        assert len(s2["checkpoints"]) == 0
