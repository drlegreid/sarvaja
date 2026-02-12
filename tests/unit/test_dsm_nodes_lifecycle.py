"""
Unit tests for DSP LangGraph Lifecycle Nodes.

Per DOC-SIZE-01-v1: Tests for dsm/langgraph/nodes_lifecycle.py module.
Tests: _create_phase_result, start_node, complete_node, abort_node, skip_to_report_node.
"""

from governance.dsm.langgraph.nodes_lifecycle import (
    _create_phase_result,
    start_node,
    complete_node,
    abort_node,
    skip_to_report_node,
)


def _base_state(**kw):
    defaults = {
        "cycle_id": "DSP-TEST-001",
        "phases_completed": [],
        "phase_results": [],
        "checkpoints": [],
        "findings": [],
        "metrics": {},
        "evidence_files": [],
        "available_mcps": ["claude-mem", "governance"],
    }
    defaults.update(kw)
    return defaults


class TestCreatePhaseResult:
    def test_basic(self):
        result = _create_phase_result("audit", "success", _base_state())
        assert result["phase"] == "audit"
        assert result["status"] == "success"
        assert result["error"] is None

    def test_with_error(self):
        result = _create_phase_result("audit", "failed", _base_state(), error="boom")
        assert result["error"] == "boom"

    def test_counts_checkpoints(self):
        state = _base_state(checkpoints=[
            {"phase": "audit"}, {"phase": "audit"}, {"phase": "optimize"},
        ])
        result = _create_phase_result("audit", "success", state)
        assert result["checkpoints"] == 2

    def test_counts_findings(self):
        state = _base_state(findings=[
            {"phase": "audit"}, {"phase": "optimize"},
        ])
        result = _create_phase_result("audit", "success", state)
        assert result["findings"] == 1


class TestStartNode:
    def test_success(self):
        result = start_node(_base_state())
        assert result["current_phase"] == "started"
        assert result["status"] == "running"
        assert "start" in result["phases_completed"]

    def test_missing_mcps(self):
        result = start_node(_base_state(available_mcps=[]))
        assert result["current_phase"] == "start_failed"
        assert result["status"] == "failed"

    def test_force_advance(self):
        result = start_node(_base_state(available_mcps=[], force_advance=True))
        assert result["current_phase"] == "started"


class TestCompleteNode:
    def test_success(self):
        result = complete_node(_base_state())
        assert result["status"] == "success"
        assert "complete" in result["phases_completed"]

    def test_failed(self):
        result = complete_node(_base_state(error_message="bad"))
        assert result["status"] == "failed"

    def test_aborted(self):
        result = complete_node(_base_state(abort_reason="no budget"))
        assert result["status"] == "aborted"

    def test_metrics(self):
        state = _base_state(
            findings=[{"type": "gap"}],
            optimizations_applied=["o1", "o2"],
        )
        result = complete_node(state)
        assert result["metrics"]["total_findings"] == 1
        assert result["metrics"]["total_optimizations"] == 2


class TestAbortNode:
    def test_with_error(self):
        result = abort_node(_base_state(error_message="crashed"))
        assert result["status"] == "aborted"
        assert result["abort_reason"] == "crashed"

    def test_with_reason(self):
        result = abort_node(_base_state(abort_reason="budget"))
        assert result["abort_reason"] == "budget"

    def test_unknown(self):
        result = abort_node(_base_state())
        assert result["abort_reason"] == "Unknown reason"


class TestSkipToReportNode:
    def test_basic(self):
        result = skip_to_report_node(_base_state())
        assert result["current_phase"] == "skipped_to_report"
        assert result["should_skip_dream"] is True
