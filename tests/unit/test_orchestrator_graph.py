"""
Unit tests for Orchestrator Graph Construction.

Per DOC-SIZE-01-v1: Tests for workflows/orchestrator/graph.py module.
Tests: MockStateGraph, build_orchestrator_graph(), run_single_cycle().
"""

from governance.workflows.orchestrator.graph import (
    MockStateGraph,
    build_orchestrator_graph,
    run_single_cycle,
)


class TestMockStateGraph:
    def test_add_node(self):
        g = MockStateGraph()
        g.add_node("test", lambda s: s)
        assert "test" in g.nodes

    def test_add_edge(self):
        g = MockStateGraph()
        g.add_edge("a", "b")
        assert ("a", "b") in g._edges

    def test_set_entry_point(self):
        g = MockStateGraph()
        g.set_entry_point("gate")
        assert g._entry_point == "gate"

    def test_compile_returns_self(self):
        g = MockStateGraph()
        assert g.compile() is g

    def test_add_conditional_edges(self):
        g = MockStateGraph()
        g.add_conditional_edges("validate", lambda s: "x", {"x": "y"})
        assert len(g._conditional_edges) == 1


class TestBuildOrchestratorGraph:
    def test_has_all_nodes(self):
        graph = build_orchestrator_graph()
        expected = ["gate", "backlog", "spec", "implement",
                     "validate", "inject", "complete_cycle",
                     "park_task", "certify", "complete"]
        for name in expected:
            assert name in graph.nodes

    def test_entry_point(self):
        graph = build_orchestrator_graph()
        assert graph._entry_point == "gate"

    def test_has_edges(self):
        graph = build_orchestrator_graph()
        assert len(graph._edges) > 0
        assert len(graph._conditional_edges) == 2


class TestRunSingleCycle:
    def test_dry_run(self):
        result = run_single_cycle("T-TEST", "Test task", dry_run=True)
        assert result["status"] in ("completed", "aborted", "success")
        assert result["dry_run"] is True

    def test_completes(self):
        result = run_single_cycle("T-1", "Quick test", dry_run=True)
        assert result["cycles_completed"] >= 0
