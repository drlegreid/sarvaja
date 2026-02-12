"""
Unit tests for Rule Impact Analysis Functions.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/data_access/impact.py.
Tests: _get_impact_recommendation, generate_mermaid_graph,
       build_dependency_graph, calculate_rule_impact.
"""

from unittest.mock import patch

from agent.governance_ui.data_access.impact import (
    _get_impact_recommendation,
    generate_mermaid_graph,
    build_dependency_graph,
    calculate_rule_impact,
)

_PATCH_BASE = "agent.governance_ui.data_access.impact"


# ── _get_impact_recommendation ────────────────────────


class TestGetImpactRecommendation:
    def test_critical(self):
        result = _get_impact_recommendation("CRITICAL", 10)
        assert "HALT" in result

    def test_high(self):
        result = _get_impact_recommendation("HIGH", 4)
        assert "CAUTION" in result
        assert "4" in result

    def test_medium(self):
        result = _get_impact_recommendation("MEDIUM", 2)
        assert "PROCEED WITH CARE" in result
        assert "2" in result

    def test_low(self):
        result = _get_impact_recommendation("LOW", 0)
        assert "SAFE" in result


# ── generate_mermaid_graph ────────────────────────────


class TestGenerateMermaidGraph:
    def test_empty_graph(self):
        graph = {"nodes": [], "edges": []}
        result = generate_mermaid_graph(graph)
        assert result.startswith("graph TD")
        assert "classDef active" in result

    def test_nodes_with_status(self):
        graph = {
            "nodes": [
                {"id": "R-1", "label": "Rule One", "status": "ACTIVE"},
                {"id": "R-2", "label": "Rule Two", "status": "DEPRECATED"},
                {"id": "R-3", "label": "Rule Three", "status": "DRAFT"},
            ],
            "edges": [],
        }
        result = generate_mermaid_graph(graph)
        assert ':::active' in result
        assert ':::deprecated' in result
        assert ':::draft' in result

    def test_dependency_edges(self):
        graph = {
            "nodes": [
                {"id": "R-1", "label": "R1"},
                {"id": "R-2", "label": "R2"},
            ],
            "edges": [{"source": "R-1", "target": "R-2", "type": "depends_on"}],
        }
        result = generate_mermaid_graph(graph)
        assert "R_1 --> R_2" in result

    def test_conflict_edges(self):
        graph = {
            "nodes": [],
            "edges": [{"source": "R-1", "target": "R-2", "type": "conflicts_with"}],
        }
        result = generate_mermaid_graph(graph)
        assert "R_1 -.- R_2" in result

    def test_hyphens_replaced_in_ids(self):
        graph = {
            "nodes": [{"id": "RULE-ABC-01", "label": "Rule", "status": "ACTIVE"}],
            "edges": [],
        }
        result = generate_mermaid_graph(graph)
        assert "RULE_ABC_01" in result

    def test_style_definitions(self):
        result = generate_mermaid_graph({"nodes": [], "edges": []})
        assert "classDef active fill:#4CAF50" in result
        assert "classDef deprecated fill:#F44336" in result
        assert "classDef draft fill:#9E9E9E" in result


# ── build_dependency_graph ────────────────────────────


class TestBuildDependencyGraph:
    @patch(f"{_PATCH_BASE}.get_rule_conflicts", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    def test_nodes_from_rules(self, mock_deps, mock_conflicts):
        rules = [
            {"id": "R-1", "name": "First Rule", "status": "ACTIVE",
             "category": "governance", "priority": "HIGH"},
        ]
        result = build_dependency_graph(rules)
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["id"] == "R-1"
        assert result["nodes"][0]["label"] == "First Rule"

    @patch(f"{_PATCH_BASE}.get_rule_conflicts", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    def test_rule_id_fallback(self, mock_deps, mock_conflicts):
        rules = [{"rule_id": "R-1"}]
        result = build_dependency_graph(rules)
        assert result["nodes"][0]["id"] == "R-1"

    @patch(f"{_PATCH_BASE}.get_rule_conflicts", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=["R-2"])
    def test_dependency_edges(self, mock_deps, mock_conflicts):
        rules = [{"id": "R-1"}, {"id": "R-2"}]
        result = build_dependency_graph(rules)
        dep_edges = [e for e in result["edges"] if e["type"] == "depends_on"]
        assert len(dep_edges) >= 1

    @patch(f"{_PATCH_BASE}.get_rule_conflicts",
           return_value=[{"rule1_id": "R-1", "rule2_id": "R-2", "reason": "overlap"}])
    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    def test_conflict_edges(self, mock_deps, mock_conflicts):
        rules = [{"id": "R-1"}, {"id": "R-2"}]
        result = build_dependency_graph(rules)
        conflict_edges = [e for e in result["edges"] if e["type"] == "conflicts_with"]
        assert len(conflict_edges) == 1
        assert conflict_edges[0]["reason"] == "overlap"

    @patch(f"{_PATCH_BASE}.get_rule_conflicts", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    def test_stats_computed(self, mock_deps, mock_conflicts):
        rules = [{"id": "R-1"}]
        result = build_dependency_graph(rules)
        assert result["stats"]["total_nodes"] == 1
        assert "total_edges" in result["stats"]
        assert "dependency_edges" in result["stats"]
        assert "conflict_edges" in result["stats"]

    @patch(f"{_PATCH_BASE}.get_rule_conflicts", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    def test_skips_rules_without_id(self, mock_deps, mock_conflicts):
        rules = [{"name": "No ID Rule"}]
        result = build_dependency_graph(rules)
        assert len(result["nodes"]) == 0


# ── calculate_rule_impact ─────────────────────────────


class TestCalculateRuleImpact:
    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependents", return_value=[])
    def test_no_impact(self, mock_dependents, mock_deps):
        result = calculate_rule_impact("R-1", [])
        assert result["risk_level"] == "LOW"
        assert result["risk_score"] == 0.1
        assert result["total_affected"] == 0

    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=["R-0"])
    @patch(f"{_PATCH_BASE}.get_rule_dependents", return_value=["R-2"])
    def test_medium_impact(self, mock_dependents, mock_deps):
        result = calculate_rule_impact("R-1", [])
        assert result["risk_level"] == "MEDIUM"
        assert result["total_affected"] == 1
        assert result["dependencies"] == ["R-0"]

    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependents",
           side_effect=[["R-2", "R-3", "R-4"], [], [], []])
    def test_high_impact(self, mock_dependents, mock_deps):
        result = calculate_rule_impact("R-1", [])
        assert result["risk_level"] == "HIGH"
        assert result["total_affected"] == 3

    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependents", return_value=["R-2"])
    def test_critical_when_affected_is_critical_priority(self, mock_dep, mock_deps):
        rules = [{"id": "R-2", "priority": "CRITICAL"}]
        result = calculate_rule_impact("R-1", rules)
        assert result["risk_level"] == "CRITICAL"
        assert result["risk_score"] == 1.0
        assert result["critical_rules_affected"] == ["R-2"]

    @patch(f"{_PATCH_BASE}.get_rule_dependencies", return_value=[])
    @patch(f"{_PATCH_BASE}.get_rule_dependents", return_value=[])
    def test_recommendation_included(self, mock_dep, mock_deps):
        result = calculate_rule_impact("R-1", [])
        assert "recommendation" in result
        assert "SAFE" in result["recommendation"]
