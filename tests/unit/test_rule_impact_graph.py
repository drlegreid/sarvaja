"""
Unit tests for Rule Impact Graph & Clustering Mixin.

Per DOC-SIZE-01-v1: Tests for extracted rule_impact_graph.py module.
Tests: get_impact_graph, get_subgraph, identify_clusters, get_rule_cluster.
"""

import pytest
from typing import Any, Dict, List, Optional

from agent.rule_impact_graph import RuleImpactGraphMixin


class MockGraphAnalyzer(RuleImpactGraphMixin):
    """Host class for mixin testing."""

    def __init__(self, rules=None, deps=None):
        self._graph_cache = None
        self._rules = rules or []
        self._deps = deps or {}  # {rule_id: [required_ids]}

    def _fetch_rules(self):
        return self._rules

    def _get_rule(self, rule_id):
        for r in self._rules:
            rid = r.get("id") or r.get("rule_id", "")
            if rid == rule_id:
                return r
        return None

    def get_required_rules(self, rule_id):
        return self._deps.get(rule_id, [])

    def get_dependent_rules(self, rule_id):
        result = []
        for rid, deps in self._deps.items():
            if rule_id in deps:
                result.append(rid)
        return result


@pytest.fixture
def simple_graph():
    """R-01 -> R-02 -> R-03 (chain)."""
    rules = [
        {"id": "R-01", "name": "Rule 1", "priority": "HIGH"},
        {"id": "R-02", "name": "Rule 2", "priority": "MEDIUM"},
        {"id": "R-03", "name": "Rule 3", "priority": "LOW"},
    ]
    deps = {"R-01": ["R-02"], "R-02": ["R-03"]}
    return MockGraphAnalyzer(rules, deps)


class TestGetImpactGraph:
    """Tests for get_impact_graph()."""

    def test_empty(self):
        analyzer = MockGraphAnalyzer()
        graph = analyzer.get_impact_graph()
        assert graph["node_count"] == 0
        assert graph["edge_count"] == 0

    def test_builds_nodes_and_edges(self, simple_graph):
        graph = simple_graph.get_impact_graph()
        assert graph["node_count"] == 3
        assert graph["edge_count"] == 2
        node_ids = {n["id"] for n in graph["nodes"]}
        assert node_ids == {"R-01", "R-02", "R-03"}

    def test_edge_structure(self, simple_graph):
        graph = simple_graph.get_impact_graph()
        edges = graph["edges"]
        assert any(e["source"] == "R-01" and e["target"] == "R-02" for e in edges)
        assert any(e["source"] == "R-02" and e["target"] == "R-03" for e in edges)

    def test_caches_result(self, simple_graph):
        g1 = simple_graph.get_impact_graph()
        g2 = simple_graph.get_impact_graph()
        assert g1 is g2

    def test_node_metadata(self, simple_graph):
        graph = simple_graph.get_impact_graph()
        r1 = next(n for n in graph["nodes"] if n["id"] == "R-01")
        assert r1["name"] == "Rule 1"
        assert r1["priority"] == "HIGH"


class TestGetSubgraph:
    """Tests for get_subgraph()."""

    def test_single_node(self):
        analyzer = MockGraphAnalyzer(
            rules=[{"id": "R-01", "name": "Solo"}],
            deps={},
        )
        sub = analyzer.get_subgraph("R-01")
        assert sub["center"] == "R-01"
        assert len(sub["nodes"]) == 1
        assert len(sub["edges"]) == 0

    def test_includes_deps(self, simple_graph):
        sub = simple_graph.get_subgraph("R-01", depth=2)
        node_ids = {n["id"] for n in sub["nodes"]}
        assert "R-01" in node_ids
        assert "R-02" in node_ids
        assert "R-03" in node_ids

    def test_depth_limiting(self, simple_graph):
        sub = simple_graph.get_subgraph("R-01", depth=1)
        node_ids = {n["id"] for n in sub["nodes"]}
        assert "R-01" in node_ids
        assert "R-02" in node_ids
        # R-03 is depth 2, should be excluded
        assert "R-03" not in node_ids

    def test_includes_dependents(self, simple_graph):
        sub = simple_graph.get_subgraph("R-03", depth=2)
        node_ids = {n["id"] for n in sub["nodes"]}
        assert "R-02" in node_ids  # depends on R-03

    def test_node_has_depth(self, simple_graph):
        sub = simple_graph.get_subgraph("R-01", depth=2)
        r1 = next(n for n in sub["nodes"] if n["id"] == "R-01")
        assert r1["depth"] == 0


class TestIdentifyClusters:
    """Tests for identify_clusters()."""

    def test_empty(self):
        analyzer = MockGraphAnalyzer()
        assert analyzer.identify_clusters() == []

    def test_single_cluster(self, simple_graph):
        clusters = simple_graph.identify_clusters()
        assert len(clusters) == 1
        assert set(clusters[0]) == {"R-01", "R-02", "R-03"}

    def test_disconnected_clusters(self):
        rules = [
            {"id": "R-01"}, {"id": "R-02"},
            {"id": "R-03"}, {"id": "R-04"},
        ]
        deps = {"R-01": ["R-02"]}  # R-03, R-04 are orphans
        analyzer = MockGraphAnalyzer(rules, deps)
        clusters = analyzer.identify_clusters()
        assert len(clusters) == 3  # {R-01, R-02}, {R-03}, {R-04}


class TestGetRuleCluster:
    """Tests for get_rule_cluster()."""

    def test_finds_cluster(self, simple_graph):
        cluster = simple_graph.get_rule_cluster("R-02")
        assert cluster is not None
        assert "R-01" in cluster
        assert "R-02" in cluster
        assert "R-03" in cluster

    def test_not_found(self, simple_graph):
        cluster = simple_graph.get_rule_cluster("R-NONEXISTENT")
        assert cluster is None
