"""
Unit tests for DSP LangGraph Graph Construction.

Per DOC-SIZE-01-v1: Tests for dsm/langgraph/graph.py module.
Tests: build_dsp_graph, run_dsp_workflow, _run_fallback_workflow.
"""

from unittest.mock import patch, MagicMock

import pytest

from governance.dsm.langgraph.graph import (
    build_dsp_graph,
    run_dsp_workflow,
    _run_fallback_workflow,
    LANGGRAPH_AVAILABLE,
)
from governance.dsm.langgraph.state import create_initial_state


class TestBuildDspGraph:
    def test_builds_graph(self):
        graph = build_dsp_graph()
        assert graph is not None

    def test_has_all_nodes(self):
        graph = build_dsp_graph()
        expected_nodes = [
            "start", "audit", "hypothesize", "measure",
            "optimize", "validate", "dream", "report",
            "complete", "abort", "skip_to_report",
        ]
        for node in expected_nodes:
            assert node in graph.nodes, f"Missing node: {node}"

    def test_has_edges(self):
        graph = build_dsp_graph()
        # MockStateGraph stores edges
        assert len(graph.edges) > 0

    def test_has_conditional_edges(self):
        graph = build_dsp_graph()
        assert len(graph.conditional_edges) > 0


class TestRunDspWorkflow:
    def test_dry_run(self):
        state = run_dsp_workflow(dry_run=True)
        assert isinstance(state, dict)
        assert "cycle_id" in state

    def test_with_batch_id(self):
        state = run_dsp_workflow(batch_id="test-batch", dry_run=True)
        assert isinstance(state, dict)

    def test_with_mcps(self):
        state = run_dsp_workflow(
            dry_run=True,
            available_mcps=["governance", "claude-mem"],
        )
        assert isinstance(state, dict)


class TestFallbackWorkflow:
    def test_linear_execution(self):
        graph = build_dsp_graph()
        initial = create_initial_state(dry_run=True)
        state = _run_fallback_workflow(graph, initial)
        assert isinstance(state, dict)
        # Should have completed some phases
        assert "phases_completed" in state

    def test_abort_on_failure(self):
        graph = build_dsp_graph()
        initial = create_initial_state(dry_run=True)
        initial["status"] = "failed"
        state = _run_fallback_workflow(graph, initial)
        assert isinstance(state, dict)

    def test_skip_dream_flag(self):
        graph = build_dsp_graph()
        initial = create_initial_state(dry_run=True)
        initial["should_skip_dream"] = True
        state = _run_fallback_workflow(graph, initial)
        assert isinstance(state, dict)

    def test_validation_retry_loop(self):
        graph = build_dsp_graph()
        initial = create_initial_state(dry_run=True)
        # Replace nodes with no-ops so workflow reaches validate
        for name in list(graph.nodes):
            if name != "validate":
                graph.nodes[name] = lambda s: s
        # validate returns validation_passed=False to trigger retry
        graph.nodes["validate"] = lambda s: {**s, "validation_passed": False}
        initial["validation_passed"] = False
        initial["retry_count"] = 0
        state = _run_fallback_workflow(graph, initial)
        assert isinstance(state, dict)
        # Should have retried (retry_count > 0)
        assert state.get("retry_count", 0) >= 1

    def test_node_exception_sets_failed(self):
        graph = build_dsp_graph()
        initial = create_initial_state(dry_run=True)
        # Replace start_node with one that raises
        graph.nodes["start"] = MagicMock(side_effect=Exception("Node crash"))
        state = _run_fallback_workflow(graph, initial)
        assert state["status"] == "failed"
        assert "Node 'start' failed: Exception" in state.get("error_message", "")
