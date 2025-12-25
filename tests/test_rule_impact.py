"""
Rule Impact Analyzer Tests (P9.4)
Created: 2024-12-25

Tests for rule dependency analysis and impact visualization.
Strategic Goal: Understand rule relationships and change impacts.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
AGENT_DIR = PROJECT_ROOT / "agent"


class TestRuleImpactModule:
    """Verify P9.4 rule impact analyzer module exists."""

    @pytest.mark.unit
    def test_rule_impact_module_exists(self):
        """Rule impact module must exist."""
        impact_file = AGENT_DIR / "rule_impact.py"
        assert impact_file.exists(), "agent/rule_impact.py not found"

    @pytest.mark.unit
    def test_rule_impact_class(self):
        """RuleImpactAnalyzer class must be importable."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        assert analyzer is not None

    @pytest.mark.unit
    def test_analyzer_has_required_methods(self):
        """Analyzer must have required methods."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()

        assert hasattr(analyzer, 'analyze_dependencies')
        assert hasattr(analyzer, 'get_impact_graph')
        assert hasattr(analyzer, 'simulate_change')
        assert hasattr(analyzer, 'get_affected_rules')


class TestDependencyAnalysis:
    """Tests for rule dependency analysis."""

    @pytest.mark.unit
    def test_analyze_dependencies(self):
        """Should analyze rule dependencies."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        result = analyzer.analyze_dependencies("RULE-001")

        assert isinstance(result, dict)
        assert 'rule_id' in result

    @pytest.mark.unit
    def test_find_dependent_rules(self):
        """Should find rules that depend on a given rule."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        dependents = analyzer.get_dependent_rules("RULE-001")

        assert isinstance(dependents, list)

    @pytest.mark.unit
    def test_find_required_rules(self):
        """Should find rules required by a given rule."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        required = analyzer.get_required_rules("RULE-011")

        assert isinstance(required, list)


class TestImpactGraph:
    """Tests for impact graph generation."""

    @pytest.mark.unit
    def test_get_impact_graph(self):
        """Should generate impact graph for rules."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        graph = analyzer.get_impact_graph()

        assert isinstance(graph, dict)
        assert 'nodes' in graph or 'rules' in graph

    @pytest.mark.unit
    def test_graph_has_edges(self):
        """Impact graph should have edges (dependencies)."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        graph = analyzer.get_impact_graph()

        assert 'edges' in graph or 'dependencies' in graph

    @pytest.mark.unit
    def test_get_subgraph_for_rule(self):
        """Should get subgraph centered on a specific rule."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        subgraph = analyzer.get_subgraph("RULE-001", depth=2)

        assert isinstance(subgraph, dict)


class TestChangeSimulation:
    """Tests for change simulation."""

    @pytest.mark.unit
    def test_simulate_change(self):
        """Should simulate impact of changing a rule."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        result = analyzer.simulate_change(
            rule_id="RULE-001",
            change_type="modify"
        )

        assert isinstance(result, dict)
        assert 'affected' in result or 'impact' in result

    @pytest.mark.unit
    def test_simulate_deprecation(self):
        """Should simulate deprecating a rule."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        result = analyzer.simulate_change(
            rule_id="RULE-001",
            change_type="deprecate"
        )

        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_get_affected_rules(self):
        """Should get list of affected rules for a change."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        affected = analyzer.get_affected_rules("RULE-011")

        assert isinstance(affected, list)


class TestImpactScoring:
    """Tests for impact scoring."""

    @pytest.mark.unit
    def test_calculate_impact_score(self):
        """Should calculate impact score for a rule."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        score = analyzer.calculate_impact_score("RULE-001")

        assert isinstance(score, (int, float))
        assert score >= 0

    @pytest.mark.unit
    def test_rank_rules_by_impact(self):
        """Should rank rules by their impact scores."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        ranked = analyzer.rank_by_impact()

        assert isinstance(ranked, list)


class TestRuleClusters:
    """Tests for rule clustering."""

    @pytest.mark.unit
    def test_identify_clusters(self):
        """Should identify rule clusters."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        clusters = analyzer.identify_clusters()

        assert isinstance(clusters, list)

    @pytest.mark.unit
    def test_get_cluster_for_rule(self):
        """Should get cluster containing a specific rule."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        cluster = analyzer.get_rule_cluster("RULE-001")

        assert isinstance(cluster, (dict, list, type(None)))


class TestImpactIntegration:
    """Integration tests for rule impact analyzer."""

    @pytest.mark.unit
    def test_uses_mcp_tools(self):
        """Analyzer should use MCP tools internally."""
        from agent.rule_impact import RuleImpactAnalyzer

        analyzer = RuleImpactAnalyzer()
        assert hasattr(analyzer, '_fetch_rules')

    @pytest.mark.unit
    def test_factory_function(self):
        """Factory function should create analyzer."""
        from agent.rule_impact import create_impact_analyzer

        analyzer = create_impact_analyzer()
        assert analyzer is not None
