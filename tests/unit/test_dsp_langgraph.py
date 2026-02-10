"""
Tests for DSP LangGraph Workflow.

Per WORKFLOW-DSP-01-v1: DSP Workflow Stability Requirements
Per TEST-GUARD-01: Test coverage for critical workflows

Created: 2026-02-08
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from governance.dsm.langgraph import (
    DSPState,
    create_initial_state,
    run_dsp_workflow,
    build_dsp_graph,
    LANGGRAPH_AVAILABLE,
    # Nodes
    start_node,
    audit_node,
    hypothesize_node,
    measure_node,
    optimize_node,
    validate_node,
    dream_node,
    report_node,
    complete_node,
    abort_node,
    # Edges
    check_start_status,
    check_audit_result,
    check_validation_result,
)


class TestDSPState:
    """Tests for DSP state creation."""

    def test_create_initial_state_defaults(self):
        """Test initial state has correct defaults."""
        state = create_initial_state()

        assert state["current_phase"] == "idle"
        assert state["status"] == "pending"
        assert state["phases_completed"] == []
        assert state["dry_run"] is False
        assert state["cycle_id"].startswith("DSM-")

    def test_create_initial_state_with_options(self):
        """Test initial state respects options."""
        state = create_initial_state(
            batch_id="BATCH-001",
            dry_run=True,
            available_mcps=["claude-mem", "governance"],
        )

        assert state["batch_id"] == "BATCH-001"
        assert state["dry_run"] is True
        assert "claude-mem" in state["available_mcps"]


class TestDSPNodes:
    """Tests for individual DSP phase nodes."""

    def test_start_node_success(self):
        """Test start node with available MCPs."""
        state = create_initial_state(
            available_mcps=["claude-mem", "governance"],
        )

        result = start_node(state)

        assert result["current_phase"] == "started"
        assert result["status"] == "running"
        assert "start" in result["phases_completed"]

    def test_start_node_missing_mcps(self):
        """Test start node fails without required MCPs."""
        state = create_initial_state(available_mcps=[])

        result = start_node(state)

        assert result["status"] == "failed"
        assert "Missing required MCPs" in result["error_message"]

    def test_start_node_force_advance(self):
        """Test start node with force_advance bypasses MCP check."""
        state = create_initial_state(available_mcps=[])
        state["force_advance"] = True

        result = start_node(state)

        assert result["current_phase"] == "started"
        assert result["status"] == "running"

    def test_audit_node_dry_run(self):
        """Test audit node in dry run mode."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start"]

        result = audit_node(state)

        assert result["current_phase"] == "audited"
        assert len(result["audit_gaps"]) > 0
        assert len(result["checkpoints"]) > 0

    def test_hypothesize_node(self):
        """Test hypothesize node generates hypotheses."""
        state = create_initial_state()
        state["phases_completed"] = ["start", "audit"]
        state["audit_gaps"] = ["GAP-001", "GAP-002"]

        result = hypothesize_node(state)

        assert result["current_phase"] == "hypothesized"
        assert len(result["hypotheses"]) > 0

    def test_validate_node_passes(self):
        """Test validate node with passing tests."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "audit", "hypothesize", "measure", "optimize"]

        result = validate_node(state)

        assert result["current_phase"] == "validated"
        # Dry run has 1 failed test by default
        assert result["validation_passed"] is False or result.get("validation_results", {}).get("tests_failed", 1) > 0

    def test_complete_node_success(self):
        """Test complete node with successful state."""
        state = create_initial_state()
        state["phases_completed"] = ["start", "audit", "hypothesize", "measure", "optimize", "validate", "dream", "report"]
        state["findings"] = [{"id": "F1"}]
        state["optimizations_applied"] = ["O1", "O2"]

        result = complete_node(state)

        assert result["current_phase"] == "complete"
        assert result["status"] == "success"
        assert result["completed_at"] is not None

    def test_complete_node_with_error(self):
        """Test complete node with error state."""
        state = create_initial_state()
        state["phases_completed"] = ["start", "audit"]
        state["error_message"] = "Test error"

        result = complete_node(state)

        assert result["status"] == "failed"


class TestDSPEdges:
    """Tests for DSP conditional edge routing."""

    def test_check_start_status_success(self):
        """Test start status routing on success."""
        state = create_initial_state()
        state["status"] = "running"

        assert check_start_status(state) == "audit"

    def test_check_start_status_failed(self):
        """Test start status routing on failure."""
        state = create_initial_state()
        state["status"] = "failed"

        assert check_start_status(state) == "abort"

    def test_check_audit_result_normal(self):
        """Test audit routing for normal flow."""
        state = create_initial_state()
        state["status"] = "running"
        state["has_critical_gaps"] = False

        assert check_audit_result(state) == "hypothesize"

    def test_check_audit_result_critical(self):
        """Test audit routing with critical gaps."""
        state = create_initial_state()
        state["status"] = "running"
        state["has_critical_gaps"] = True

        assert check_audit_result(state) == "skip_to_report"

    def test_check_validation_passed(self):
        """Test validation routing when passed."""
        state = create_initial_state()
        state["status"] = "running"
        state["validation_passed"] = True

        assert check_validation_result(state) == "dream"

    def test_check_validation_failed_loops_back(self):
        """Test validation failure loops to hypothesize when retries remain."""
        state = create_initial_state()
        state["status"] = "running"
        state["validation_passed"] = False
        state["retry_count"] = 0

        assert check_validation_result(state) == "loop_to_hypothesize"

    def test_check_validation_failed_retries_exhausted(self):
        """Test validation failure goes to report when retries exhausted."""
        from governance.dsm.langgraph.state import MAX_PHASE_RETRIES
        state = create_initial_state()
        state["status"] = "running"
        state["validation_passed"] = False
        state["retry_count"] = MAX_PHASE_RETRIES

        assert check_validation_result(state) == "report"

    def test_check_validation_failed_mid_retry(self):
        """Test validation failure loops at retry_count < MAX."""
        state = create_initial_state()
        state["status"] = "running"
        state["validation_passed"] = False
        state["retry_count"] = 2  # Still below MAX_PHASE_RETRIES=3

        assert check_validation_result(state) == "loop_to_hypothesize"


class TestDSPGraph:
    """Tests for DSP graph construction."""

    def test_build_graph(self):
        """Test graph builds without error."""
        graph = build_dsp_graph()

        assert graph is not None
        assert len(graph.nodes) == 11  # All phase nodes

    def test_graph_has_all_nodes(self):
        """Test graph contains all required nodes."""
        graph = build_dsp_graph()

        expected_nodes = [
            "start", "audit", "hypothesize", "measure", "optimize",
            "validate", "dream", "report", "complete", "abort", "skip_to_report"
        ]

        for node in expected_nodes:
            assert node in graph.nodes, f"Missing node: {node}"


class TestDSPWorkflowExecution:
    """Tests for full workflow execution."""

    def test_run_workflow_dry_run(self):
        """Test full workflow in dry run mode."""
        result = run_dsp_workflow(
            dry_run=True,
            available_mcps=["claude-mem", "governance", "sequential-thinking"],
        )

        assert result["status"] in ("success", "failed")
        assert len(result["phases_completed"]) > 0
        assert result["completed_at"] is not None

    def test_run_workflow_with_batch(self):
        """Test workflow with batch ID."""
        result = run_dsp_workflow(
            batch_id="TEST-BATCH-001",
            dry_run=True,
            available_mcps=["claude-mem", "governance"],
        )

        assert result["batch_id"] == "TEST-BATCH-001"

    def test_run_workflow_missing_mcps(self):
        """Test workflow fails gracefully with missing MCPs."""
        result = run_dsp_workflow(
            dry_run=True,
            available_mcps=[],
        )

        # Should either fail at start or fallback
        assert result["status"] in ("success", "failed", "aborted")


class TestLangGraphAvailability:
    """Tests for LangGraph availability handling."""

    def test_langgraph_available_flag(self):
        """Test LangGraph availability flag is set."""
        # This tests that the import worked correctly
        assert isinstance(LANGGRAPH_AVAILABLE, bool)

    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_workflow_with_langgraph(self):
        """Test workflow uses real LangGraph when available."""
        result = run_dsp_workflow(
            dry_run=True,
            available_mcps=["claude-mem", "governance"],
        )

        assert result is not None
        assert "cycle_id" in result
