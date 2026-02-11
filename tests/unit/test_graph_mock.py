"""
Unit tests for DSP Mock LangGraph classes.

Per DOC-SIZE-01-v1: Tests for extracted graph_mock.py.
Tests: StateGraph, CompiledMockGraph, MemorySaver.
"""

import pytest

from governance.dsm.langgraph.graph_mock import (
    StateGraph,
    CompiledMockGraph,
    MemorySaver,
)


class TestStateGraph:
    """Tests for mock StateGraph."""

    def test_init(self):
        g = StateGraph(dict)
        assert g.state_type is dict
        assert g.nodes == {}
        assert g.edges == []
        assert g.conditional_edges == []

    def test_add_node(self):
        g = StateGraph(dict)
        fn = lambda x: x
        g.add_node("test", fn)
        assert "test" in g.nodes
        assert g.nodes["test"] is fn

    def test_add_edge(self):
        g = StateGraph(dict)
        g.add_edge("a", "b")
        assert ("a", "b") in g.edges

    def test_add_conditional_edges(self):
        g = StateGraph(dict)
        cond = lambda x: "next"
        mapping = {"next": "b"}
        g.add_conditional_edges("a", cond, mapping)
        assert len(g.conditional_edges) == 1
        assert g.conditional_edges[0][0] == "a"

    def test_compile_returns_compiled_graph(self):
        g = StateGraph(dict)
        compiled = g.compile()
        assert isinstance(compiled, CompiledMockGraph)

    def test_compile_with_checkpointer(self):
        g = StateGraph(dict)
        compiled = g.compile(checkpointer=MemorySaver())
        assert isinstance(compiled, CompiledMockGraph)


class TestCompiledMockGraph:
    """Tests for mock CompiledMockGraph."""

    def test_stream_yields_initial_state(self):
        g = StateGraph(dict)
        compiled = g.compile()
        results = list(compiled.stream({"key": "value"}, {}))
        assert len(results) == 1
        assert "start" in results[0]
        assert results[0]["start"]["key"] == "value"

    def test_stream_does_not_modify_original(self):
        g = StateGraph(dict)
        compiled = g.compile()
        state = {"key": "value"}
        list(compiled.stream(state, {}))
        assert state == {"key": "value"}


class TestMemorySaver:
    """Tests for mock MemorySaver."""

    def test_instantiation(self):
        ms = MemorySaver()
        assert ms is not None
