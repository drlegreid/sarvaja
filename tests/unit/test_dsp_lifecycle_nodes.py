"""
Unit tests for DSP LangGraph Lifecycle Nodes.

Per DOC-SIZE-01-v1: Tests for extracted nodes_lifecycle.py module.
Tests: _create_phase_result, start_node, complete_node, abort_node,
       skip_to_report_node.
"""

import pytest


from governance.dsm.langgraph.nodes_lifecycle import (
    _create_phase_result,
    start_node,
    complete_node,
    abort_node,
    skip_to_report_node,
)


def _base_state(**overrides):
    """Create a minimal DSP state dict."""
    state = {
        "cycle_id": "DSM-TEST-001",
        "batch_id": "B-01",
        "current_phase": "idle",
        "phases_completed": [],
        "status": "pending",
        "available_mcps": ["claude-mem", "governance"],
        "checkpoints": [],
        "findings": [],
        "metrics": {},
        "evidence_files": [],
        "error_message": None,
        "abort_reason": None,
        "optimizations_applied": [],
        "phase_results": [],
    }
    state.update(overrides)
    return state


class TestCreatePhaseResult:
    """Tests for _create_phase_result()."""

    def test_basic_result(self):
        state = _base_state()
        result = _create_phase_result("start", "success", state, duration_ms=10)
        assert result["phase"] == "start"
        assert result["status"] == "success"
        assert result["duration_ms"] == 10
        assert result["error"] is None

    def test_with_error(self):
        state = _base_state()
        result = _create_phase_result("audit", "failed", state, error="MCP down")
        assert result["error"] == "MCP down"

    def test_counts_phase_checkpoints(self):
        state = _base_state(checkpoints=[
            {"phase": "audit", "data": "cp1"},
            {"phase": "audit", "data": "cp2"},
            {"phase": "measure", "data": "cp3"},
        ])
        result = _create_phase_result("audit", "success", state)
        assert result["checkpoints"] == 2

    def test_counts_phase_findings(self):
        state = _base_state(findings=[
            {"phase": "audit", "text": "f1"},
            {"phase": "hypothesize", "text": "f2"},
        ])
        result = _create_phase_result("audit", "success", state)
        assert result["findings"] == 1


class TestStartNode:
    """Tests for start_node()."""

    def test_success(self):
        state = _base_state()
        result = start_node(state)
        assert result["current_phase"] == "started"
        assert result["status"] == "running"
        assert "start" in result["phases_completed"]
        assert "started_at" in result

    def test_missing_mcps(self):
        state = _base_state(available_mcps=[])
        result = start_node(state)
        assert result["current_phase"] == "start_failed"
        assert result["status"] == "failed"
        assert "Missing required MCPs" in result["error_message"]

    def test_force_advance_ignores_missing(self):
        state = _base_state(available_mcps=[], force_advance=True)
        result = start_node(state)
        assert result["current_phase"] == "started"
        assert result["status"] == "running"

    def test_phase_result_appended(self):
        state = _base_state()
        result = start_node(state)
        assert len(result["phase_results"]) == 1
        assert result["phase_results"][0]["phase"] == "start"


class TestCompleteNode:
    """Tests for complete_node()."""

    def test_success(self):
        state = _base_state(phases_completed=["start", "audit"])
        result = complete_node(state)
        assert result["current_phase"] == "complete"
        assert result["status"] == "success"
        assert "complete" in result["phases_completed"]
        assert "completed_at" in result

    def test_with_error_sets_failed(self):
        state = _base_state(
            phases_completed=["start"],
            error_message="Something broke",
        )
        result = complete_node(state)
        assert result["status"] == "failed"

    def test_with_abort_reason(self):
        state = _base_state(
            phases_completed=["start"],
            abort_reason="User requested abort",
        )
        result = complete_node(state)
        assert result["status"] == "aborted"

    def test_metrics_include_counts(self):
        state = _base_state(
            phases_completed=["start", "audit"],
            findings=[{"phase": "audit", "text": "f1"}],
            optimizations_applied=["opt1", "opt2"],
        )
        result = complete_node(state)
        assert result["metrics"]["total_findings"] == 1
        assert result["metrics"]["total_optimizations"] == 2
        assert result["metrics"]["phases_completed_count"] == 3


class TestAbortNode:
    """Tests for abort_node()."""

    def test_basic_abort(self):
        state = _base_state(
            phases_completed=["start"],
            error_message="Critical failure",
        )
        result = abort_node(state)
        assert result["current_phase"] == "aborted"
        assert result["status"] == "aborted"
        assert result["abort_reason"] == "Critical failure"
        assert "completed_at" in result

    def test_abort_with_reason(self):
        state = _base_state(
            phases_completed=["start"],
            abort_reason="User abort",
        )
        result = abort_node(state)
        assert result["abort_reason"] == "User abort"

    def test_abort_unknown_reason(self):
        state = _base_state(phases_completed=["start"])
        result = abort_node(state)
        assert result["abort_reason"] == "Unknown reason"


class TestSkipToReportNode:
    """Tests for skip_to_report_node()."""

    def test_skip(self):
        state = _base_state(phases_completed=["start", "audit"])
        result = skip_to_report_node(state)
        assert result["current_phase"] == "skipped_to_report"
        assert result["should_skip_dream"] is True
        assert "skip_to_report" in result["phases_completed"]
