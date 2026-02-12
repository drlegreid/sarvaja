"""
Unit tests for Rule Impact Analysis.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/data_access/impact.py.
Tests: get_rule_dependencies, get_rule_dependents, get_rule_conflicts,
       build_dependency_graph, calculate_rule_impact,
       _get_impact_recommendation, generate_mermaid_graph.
"""

from unittest.mock import patch, MagicMock

from agent.governance_ui.data_access.impact import (
    get_rule_dependencies, get_rule_dependents, get_rule_conflicts,
    build_dependency_graph, calculate_rule_impact,
    _get_impact_recommendation, generate_mermaid_graph,
)


def _mock_client(connect_ok=True, **attrs):
    """Create a mock TypeDB client."""
    client = MagicMock()
    client.connect.return_value = connect_ok
    for k, v in attrs.items():
        setattr(client, k, MagicMock(return_value=v))
    return client


# ── get_rule_dependencies ────────────────────────────────


class TestGetRuleDependencies:
    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_returns_deps(self, mock_get_client):
        mock_get_client.return_value = _mock_client(
            get_rule_dependencies=["R-2", "R-3"]
        )
        result = get_rule_dependencies("R-1")
        assert result == ["R-2", "R-3"]

    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_connect_failure(self, mock_get_client):
        mock_get_client.return_value = _mock_client(connect_ok=False)
        assert get_rule_dependencies("R-1") == []

    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_none_returns_empty(self, mock_get_client):
        mock_get_client.return_value = _mock_client(get_rule_dependencies=None)
        assert get_rule_dependencies("R-1") == []


# ── get_rule_dependents ──────────────────────────────────


class TestGetRuleDependents:
    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_returns_dependents(self, mock_get_client):
        mock_get_client.return_value = _mock_client(
            get_rules_depending_on=["R-4"]
        )
        assert get_rule_dependents("R-1") == ["R-4"]

    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_connect_failure(self, mock_get_client):
        mock_get_client.return_value = _mock_client(connect_ok=False)
        assert get_rule_dependents("R-1") == []


# ── get_rule_conflicts ───────────────────────────────────


class TestGetRuleConflicts:
    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_returns_conflicts(self, mock_get_client):
        conflicts = [{"rule1_id": "R-1", "rule2_id": "R-2", "reason": "overlap"}]
        mock_get_client.return_value = _mock_client(find_conflicts=conflicts)
        assert get_rule_conflicts() == conflicts

    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_connect_failure(self, mock_get_client):
        mock_get_client.return_value = _mock_client(connect_ok=False)
        assert get_rule_conflicts() == []


# ── _get_impact_recommendation ───────────────────────────


class TestGetImpactRecommendation:
    def test_critical(self):
        assert "HALT" in _get_impact_recommendation("CRITICAL", 10)

    def test_high(self):
        r = _get_impact_recommendation("HIGH", 4)
        assert "CAUTION" in r
        assert "4" in r

    def test_medium(self):
        r = _get_impact_recommendation("MEDIUM", 2)
        assert "PROCEED" in r

    def test_low(self):
        assert "SAFE" in _get_impact_recommendation("LOW", 0)


# ── build_dependency_graph ───────────────────────────────


class TestBuildDependencyGraph:
    @patch("agent.governance_ui.data_access.impact.get_rule_conflicts", return_value=[])
    @patch("agent.governance_ui.data_access.impact.get_rule_dependencies", return_value=[])
    def test_empty_rules(self, mock_deps, mock_conflicts):
        result = build_dependency_graph([])
        assert result["nodes"] == []
        assert result["edges"] == []
        assert result["stats"]["total_nodes"] == 0

    @patch("agent.governance_ui.data_access.impact.get_rule_conflicts", return_value=[])
    @patch("agent.governance_ui.data_access.impact.get_rule_dependencies")
    def test_nodes_and_edges(self, mock_deps, mock_conflicts):
        mock_deps.side_effect = lambda rid: ["R-2"] if rid == "R-1" else []
        rules = [
            {"rule_id": "R-1", "name": "Rule 1", "status": "ACTIVE"},
            {"rule_id": "R-2", "name": "Rule 2", "status": "ACTIVE"},
        ]
        result = build_dependency_graph(rules)
        assert len(result["nodes"]) == 2
        assert result["stats"]["dependency_edges"] == 1

    @patch("agent.governance_ui.data_access.impact.get_rule_conflicts")
    @patch("agent.governance_ui.data_access.impact.get_rule_dependencies", return_value=[])
    def test_conflict_edges(self, mock_deps, mock_conflicts):
        mock_conflicts.return_value = [
            {"rule1_id": "R-1", "rule2_id": "R-2", "reason": "overlap"}
        ]
        rules = [{"rule_id": "R-1"}, {"rule_id": "R-2"}]
        result = build_dependency_graph(rules)
        assert result["stats"]["conflict_edges"] == 1

    @patch("agent.governance_ui.data_access.impact.get_rule_conflicts", return_value=[])
    @patch("agent.governance_ui.data_access.impact.get_rule_dependencies", return_value=[])
    def test_uses_id_fallback(self, mock_deps, mock_conflicts):
        rules = [{"id": "R-X", "title": "Fallback"}]
        result = build_dependency_graph(rules)
        assert result["nodes"][0]["id"] == "R-X"
        assert result["nodes"][0]["label"] == "Fallback"


# ── calculate_rule_impact ────────────────────────────────


class TestCalculateRuleImpact:
    @patch("agent.governance_ui.data_access.impact.get_rule_dependencies", return_value=[])
    @patch("agent.governance_ui.data_access.impact.get_rule_dependents", return_value=[])
    def test_no_impact(self, mock_dependents, mock_deps):
        result = calculate_rule_impact("R-1", [])
        assert result["risk_level"] == "LOW"
        assert result["total_affected"] == 0

    @patch("agent.governance_ui.data_access.impact.get_rule_dependencies", return_value=["R-0"])
    @patch("agent.governance_ui.data_access.impact.get_rule_dependents")
    def test_medium_impact(self, mock_dependents, mock_deps):
        mock_dependents.side_effect = lambda rid: ["R-3"] if rid == "R-1" else []
        result = calculate_rule_impact("R-1", [])
        assert result["risk_level"] == "MEDIUM"
        assert result["dependencies"] == ["R-0"]

    @patch("agent.governance_ui.data_access.impact.get_rule_dependencies", return_value=[])
    @patch("agent.governance_ui.data_access.impact.get_rule_dependents")
    def test_critical_from_priority(self, mock_dependents, mock_deps):
        mock_dependents.side_effect = lambda rid: ["R-2"] if rid == "R-1" else []
        rules = [{"rule_id": "R-2", "priority": "CRITICAL"}]
        result = calculate_rule_impact("R-1", rules)
        assert result["risk_level"] == "CRITICAL"
        assert result["risk_score"] == 1.0


# ── generate_mermaid_graph ───────────────────────────────


class TestGenerateMermaidGraph:
    def test_empty_graph(self):
        result = generate_mermaid_graph({"nodes": [], "edges": []})
        assert result.startswith("graph TD")
        assert "classDef active" in result

    def test_nodes_with_styles(self):
        graph = {
            "nodes": [
                {"id": "R-1", "label": "Rule 1", "status": "ACTIVE"},
                {"id": "R-2", "label": "Rule 2", "status": "DEPRECATED"},
                {"id": "R-3", "label": "Rule 3", "status": "DRAFT"},
            ],
            "edges": [],
        }
        result = generate_mermaid_graph(graph)
        assert ":::active" in result
        assert ":::deprecated" in result
        assert ":::draft" in result

    def test_edge_types(self):
        graph = {
            "nodes": [],
            "edges": [
                {"source": "R-1", "target": "R-2", "type": "depends_on"},
                {"source": "R-1", "target": "R-3", "type": "conflicts_with"},
            ],
        }
        result = generate_mermaid_graph(graph)
        assert "-->" in result
        assert "-.-" in result

    def test_dashes_replaced_in_ids(self):
        graph = {"nodes": [{"id": "R-1", "label": "X", "status": "ACTIVE"}], "edges": []}
        result = generate_mermaid_graph(graph)
        assert "R_1" in result
