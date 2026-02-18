"""
Unit tests for DSP LangGraph Execution Nodes.

Per DOC-SIZE-01-v1: Tests for extracted nodes_execution.py module.
Tests: optimize_node, validate_node, dream_node, report_node.
"""

import pytest
from unittest.mock import patch

from governance.dsm.langgraph.state import create_initial_state


def _base_state(**overrides):
    """Create a base DSP state for testing."""
    state = create_initial_state(dry_run=True, force_advance=True)
    state["phases_completed"] = ["audit", "hypothesize", "measure"]
    state["audit_gaps"] = ["GAP-001", "GAP-002"]
    state["audit_orphans"] = ["ORPHAN-001"]
    state["hypotheses"] = ["Addressing GAP-001 will improve integrity"]
    state["measurements"] = {"gaps_count": 2, "orphans_count": 1}
    state.update(overrides)
    return state


class TestOptimizeNode:
    """Tests for optimize_node()."""

    def test_dry_run_returns_optimizations(self):
        from governance.dsm.langgraph.nodes_execution import optimize_node

        state = _base_state()
        result = optimize_node(state)
        assert result["current_phase"] == "optimized"
        assert "optimize" in result["phases_completed"]
        assert len(result["optimizations_applied"]) == 2
        assert "[DRY-RUN]" in result["optimizations_applied"][0]

    def test_non_dry_run_uses_hypotheses(self):
        from governance.dsm.langgraph.nodes_execution import optimize_node

        state = _base_state(dry_run=False)
        result = optimize_node(state)
        assert result["current_phase"] == "optimized"
        assert len(result["optimizations_applied"]) == 1
        assert "Applied optimization for" in result["optimizations_applied"][0]

    def test_creates_checkpoint(self):
        from governance.dsm.langgraph.nodes_execution import optimize_node

        state = _base_state()
        result = optimize_node(state)
        opt_cp = [c for c in result["checkpoints"] if c["phase"] == "optimize"]
        assert len(opt_cp) == 1
        assert "optimizations" in opt_cp[0]["metrics"]
        assert "dry_run" in opt_cp[0]["metrics"]

    def test_appends_phase_result(self):
        from governance.dsm.langgraph.nodes_execution import optimize_node

        state = _base_state()
        result = optimize_node(state)
        assert len(result["phase_results"]) == 1
        assert result["phase_results"][0]["phase"] == "optimize"
        assert result["phase_results"][0]["status"] == "success"

    def test_caps_at_2_hypotheses(self):
        from governance.dsm.langgraph.nodes_execution import optimize_node

        state = _base_state(
            dry_run=False,
            hypotheses=["H1-long-enough-to-pass", "H2-long-enough-to-pass", "H3-long-enough-to-pass", "H4-not-used"],
        )
        result = optimize_node(state)
        assert len(result["optimizations_applied"]) == 2


class TestValidateNode:
    """Tests for validate_node()."""

    def test_dry_run_returns_test_results(self):
        from governance.dsm.langgraph.nodes_execution import validate_node

        state = _base_state()
        result = validate_node(state)
        assert result["current_phase"] == "validated"
        assert "validate" in result["phases_completed"]
        assert result["validation_results"]["tests_run"] == 10
        assert result["validation_results"]["tests_passed"] == 9

    def test_dry_run_validation_not_passed(self):
        from governance.dsm.langgraph.nodes_execution import validate_node

        state = _base_state()
        result = validate_node(state)
        # 1 test failed in dry run
        assert result["validation_passed"] is False

    def test_non_dry_run_zero_tests(self):
        from governance.dsm.langgraph.nodes_execution import validate_node

        state = _base_state(dry_run=False)
        result = validate_node(state)
        # Production stub now sets tests_run=1 (BUG-349-NE-001)
        assert result["validation_results"]["tests_run"] == 1
        assert result["validation_results"]["stub"] is True
        assert result["validation_passed"] is True  # 0 failures = passed

    def test_creates_checkpoint(self):
        from governance.dsm.langgraph.nodes_execution import validate_node

        state = _base_state()
        result = validate_node(state)
        val_cp = [c for c in result["checkpoints"] if c["phase"] == "validate"]
        assert len(val_cp) == 1
        assert "tests_run" in val_cp[0]["metrics"]

    def test_appends_phase_result(self):
        from governance.dsm.langgraph.nodes_execution import validate_node

        state = _base_state()
        result = validate_node(state)
        assert len(result["phase_results"]) == 1
        assert result["phase_results"][0]["phase"] == "validate"


class TestDreamNode:
    """Tests for dream_node()."""

    def test_generates_insights(self):
        from governance.dsm.langgraph.nodes_execution import dream_node

        state = _base_state(
            optimizations_applied=["opt1", "opt2"],
            validation_passed=True,
        )
        result = dream_node(state)
        assert result["current_phase"] == "dreamed"
        assert "dream" in result["phases_completed"]
        assert len(result["dream_insights"]) == 3

    def test_insights_reflect_state(self):
        from governance.dsm.langgraph.nodes_execution import dream_node

        state = _base_state(
            audit_gaps=["G1", "G2", "G3"],
            optimizations_applied=["O1"],
            validation_passed=False,
        )
        result = dream_node(state)
        assert "3 gaps" in result["dream_insights"][0]
        assert "1 optimizations" in result["dream_insights"][1]
        assert "had issues" in result["dream_insights"][2]

    def test_validation_passed_insight(self):
        from governance.dsm.langgraph.nodes_execution import dream_node

        state = _base_state(
            audit_gaps=[],
            optimizations_applied=[],
            validation_passed=True,
        )
        result = dream_node(state)
        assert "passed" in result["dream_insights"][2]

    def test_creates_checkpoint(self):
        from governance.dsm.langgraph.nodes_execution import dream_node

        state = _base_state(
            optimizations_applied=[],
            validation_passed=True,
        )
        result = dream_node(state)
        dream_cp = [c for c in result["checkpoints"] if c["phase"] == "dream"]
        assert len(dream_cp) == 1
        assert dream_cp[0]["metrics"]["insights"] == 3

    def test_appends_phase_result(self):
        from governance.dsm.langgraph.nodes_execution import dream_node

        state = _base_state(
            optimizations_applied=[],
            validation_passed=True,
        )
        result = dream_node(state)
        assert result["phase_results"][0]["phase"] == "dream"
        assert result["phase_results"][0]["status"] == "success"


class TestReportNode:
    """Tests for report_node()."""

    def test_dry_run_generates_evidence_path(self):
        from governance.dsm.langgraph.nodes_execution import report_node

        state = _base_state()
        result = report_node(state)
        assert result["current_phase"] == "reported"
        assert "report" in result["phases_completed"]
        assert len(result["evidence_files"]) == 1
        assert "[DRY-RUN]" in result["evidence_files"][0]

    def test_preserves_existing_evidence(self):
        from governance.dsm.langgraph.nodes_execution import report_node

        state = _base_state(evidence_files=["existing-evidence.md"])
        result = report_node(state)
        assert len(result["evidence_files"]) == 2
        assert result["evidence_files"][0] == "existing-evidence.md"

    def test_creates_checkpoint(self):
        from governance.dsm.langgraph.nodes_execution import report_node

        state = _base_state()
        result = report_node(state)
        rpt_cp = [c for c in result["checkpoints"] if c["phase"] == "report"]
        assert len(rpt_cp) == 1
        assert "evidence_files" in rpt_cp[0]["metrics"]

    def test_appends_phase_result(self):
        from governance.dsm.langgraph.nodes_execution import report_node

        state = _base_state()
        result = report_node(state)
        assert result["phase_results"][0]["phase"] == "report"
        assert result["phase_results"][0]["status"] == "success"

    def test_non_dry_run_failure_returns_error(self):
        from governance.dsm.langgraph.nodes_execution import report_node

        # Non-dry-run will try to import generate_evidence which may fail
        state = _base_state(dry_run=False)
        result = report_node(state)
        # Either succeeds or fails gracefully
        if result["current_phase"] == "report_failed":
            assert "REPORT phase failed" in result["error_message"]
        else:
            assert result["current_phase"] == "reported"
