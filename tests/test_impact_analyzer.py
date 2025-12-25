"""
Impact Analyzer Tests (P9.4)
============================
Tests for rule impact analysis and dependency graph functionality.

Per RULE-012: DSP Semantic Code Structure
Per TDD: Write tests first, then implement
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Reusable constant for mock path (DRY principle)
TYPEDB_CLIENT_MOCK_PATH = 'governance.mcp_tools.common.get_typedb_client'


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_rules():
    """Sample rules for testing."""
    return [
        {
            'id': 'RULE-001',
            'name': 'Session Evidence Logging',
            'category': 'governance',
            'priority': 'CRITICAL',
            'status': 'ACTIVE',
        },
        {
            'id': 'RULE-002',
            'name': 'MCP Protocol',
            'category': 'technical',
            'priority': 'HIGH',
            'status': 'ACTIVE',
        },
        {
            'id': 'RULE-003',
            'name': 'Testing Standards',
            'category': 'operational',
            'priority': 'MEDIUM',
            'status': 'ACTIVE',
        },
        {
            'id': 'RULE-004',
            'name': 'Deprecated Rule',
            'category': 'governance',
            'priority': 'LOW',
            'status': 'DEPRECATED',
        },
    ]


@pytest.fixture
def mock_client():
    """Create a mock TypeDBClient."""
    client = Mock()
    client.connect.return_value = True
    client.close.return_value = None
    return client


# =============================================================================
# DATA ACCESS TESTS
# =============================================================================

class TestGetRuleDependencies:
    """Tests for get_rule_dependencies function."""

    def test_returns_empty_list_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        from agent.governance_ui.data_access import get_rule_dependencies
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_rule_dependencies('RULE-001')

            assert result == []
            mock_client.close.assert_called_once()

    def test_returns_dependencies_list(self, mock_client):
        """Test returns list of dependency IDs."""
        mock_client.get_rule_dependencies.return_value = ['RULE-002', 'RULE-003']

        from agent.governance_ui.data_access import get_rule_dependencies
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_rule_dependencies('RULE-001')

            assert result == ['RULE-002', 'RULE-003']

    def test_returns_empty_list_when_no_dependencies(self, mock_client):
        """Test returns empty list when rule has no dependencies."""
        mock_client.get_rule_dependencies.return_value = []

        from agent.governance_ui.data_access import get_rule_dependencies
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_rule_dependencies('RULE-001')

            assert result == []


class TestGetRuleDependents:
    """Tests for get_rule_dependents function."""

    def test_returns_empty_list_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        from agent.governance_ui.data_access import get_rule_dependents
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_rule_dependents('RULE-001')

            assert result == []

    def test_returns_dependents_list(self, mock_client):
        """Test returns list of dependent rule IDs."""
        mock_client.get_rules_depending_on.return_value = ['RULE-002', 'RULE-003']

        from agent.governance_ui.data_access import get_rule_dependents
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_rule_dependents('RULE-001')

            assert result == ['RULE-002', 'RULE-003']


class TestGetRuleConflicts:
    """Tests for get_rule_conflicts function."""

    def test_returns_empty_list_on_connection_failure(self):
        """Test returns empty list when connection fails."""
        from agent.governance_ui.data_access import get_rule_conflicts
        with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
            mock_client = Mock()
            mock_client.connect.return_value = False
            mock_get_client.return_value = mock_client

            result = get_rule_conflicts()

            assert result == []

    def test_returns_conflicts_list(self, mock_client):
        """Test returns list of conflict dicts."""
        mock_client.find_conflicts.return_value = [
            {'rule1': 'RULE-001', 'rule2': 'RULE-002', 'reason': 'Conflicting directives'}
        ]

        from agent.governance_ui.data_access import get_rule_conflicts
        with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
            result = get_rule_conflicts()

            assert len(result) == 1
            assert result[0]['reason'] == 'Conflicting directives'


class TestBuildDependencyGraph:
    """Tests for build_dependency_graph function."""

    def test_builds_nodes_from_rules(self, sample_rules):
        """Test builds node list from rules."""
        with patch('agent.governance_ui.data_access.get_rule_dependencies', return_value=[]):
            with patch('agent.governance_ui.data_access.get_rule_conflicts', return_value=[]):
                from agent.governance_ui.data_access import build_dependency_graph
                graph = build_dependency_graph(sample_rules)

                assert len(graph['nodes']) == 4
                assert graph['stats']['total_nodes'] == 4

    def test_builds_edges_from_dependencies(self, sample_rules):
        """Test builds edge list from dependencies."""
        def mock_deps(rule_id):
            if rule_id == 'RULE-002':
                return ['RULE-001']
            return []

        with patch('agent.governance_ui.data_access.get_rule_dependencies', side_effect=mock_deps):
            with patch('agent.governance_ui.data_access.get_rule_conflicts', return_value=[]):
                from agent.governance_ui.data_access import build_dependency_graph
                graph = build_dependency_graph(sample_rules)

                assert graph['stats']['dependency_edges'] == 1
                edge = [e for e in graph['edges'] if e['type'] == 'depends_on'][0]
                assert edge['source'] == 'RULE-002'
                assert edge['target'] == 'RULE-001'

    def test_includes_conflict_edges(self, sample_rules):
        """Test includes conflict edges in graph."""
        with patch('agent.governance_ui.data_access.get_rule_dependencies', return_value=[]):
            with patch('agent.governance_ui.data_access.get_rule_conflicts', return_value=[
                {'rule1': 'RULE-001', 'rule2': 'RULE-002', 'reason': 'Conflict'}
            ]):
                from agent.governance_ui.data_access import build_dependency_graph
                graph = build_dependency_graph(sample_rules)

                assert graph['stats']['conflict_edges'] == 1


class TestCalculateRuleImpact:
    """Tests for calculate_rule_impact function."""

    def test_returns_low_risk_when_no_dependents(self, sample_rules):
        """Test returns LOW risk when no rules depend on this rule."""
        with patch('agent.governance_ui.data_access.get_rule_dependents', return_value=[]):
            with patch('agent.governance_ui.data_access.get_rule_dependencies', return_value=[]):
                from agent.governance_ui.data_access import calculate_rule_impact
                impact = calculate_rule_impact('RULE-004', sample_rules)

                assert impact['risk_level'] == 'LOW'
                assert impact['total_affected'] == 0

    def test_returns_medium_risk_when_few_dependents(self, sample_rules):
        """Test returns MEDIUM risk when 1-2 rules depend on this rule."""
        with patch('agent.governance_ui.data_access.get_rule_dependents', return_value=['RULE-002']):
            with patch('agent.governance_ui.data_access.get_rule_dependencies', return_value=[]):
                from agent.governance_ui.data_access import calculate_rule_impact
                impact = calculate_rule_impact('RULE-001', sample_rules)

                assert impact['risk_level'] == 'MEDIUM'
                assert impact['total_affected'] == 1

    def test_returns_critical_when_critical_rule_affected(self, sample_rules):
        """Test returns CRITICAL when a CRITICAL priority rule is affected."""
        with patch('agent.governance_ui.data_access.get_rule_dependents', return_value=['RULE-001']):
            with patch('agent.governance_ui.data_access.get_rule_dependencies', return_value=[]):
                from agent.governance_ui.data_access import calculate_rule_impact
                impact = calculate_rule_impact('RULE-002', sample_rules)

                assert impact['risk_level'] == 'CRITICAL'
                assert 'RULE-001' in impact['critical_rules_affected']

    def test_includes_recommendation(self, sample_rules):
        """Test includes recommendation based on risk level."""
        with patch('agent.governance_ui.data_access.get_rule_dependents', return_value=[]):
            with patch('agent.governance_ui.data_access.get_rule_dependencies', return_value=[]):
                from agent.governance_ui.data_access import calculate_rule_impact
                impact = calculate_rule_impact('RULE-004', sample_rules)

                assert 'recommendation' in impact
                assert 'SAFE' in impact['recommendation']


class TestGenerateMermaidGraph:
    """Tests for generate_mermaid_graph function."""

    def test_generates_mermaid_syntax(self):
        """Test generates valid Mermaid diagram syntax."""
        graph = {
            'nodes': [
                {'id': 'RULE-001', 'label': 'Rule 1', 'status': 'ACTIVE'},
                {'id': 'RULE-002', 'label': 'Rule 2', 'status': 'DRAFT'},
            ],
            'edges': [
                {'source': 'RULE-002', 'target': 'RULE-001', 'type': 'depends_on'},
            ],
        }

        from agent.governance_ui.data_access import generate_mermaid_graph
        mermaid = generate_mermaid_graph(graph)

        assert 'graph TD' in mermaid
        assert 'RULE_001' in mermaid
        assert 'RULE_002' in mermaid
        assert '-->' in mermaid  # Dependency edge

    def test_applies_status_classes(self):
        """Test applies CSS classes based on status."""
        graph = {
            'nodes': [
                {'id': 'RULE-001', 'label': 'Active Rule', 'status': 'ACTIVE'},
                {'id': 'RULE-002', 'label': 'Deprecated Rule', 'status': 'DEPRECATED'},
            ],
            'edges': [],
        }

        from agent.governance_ui.data_access import generate_mermaid_graph
        mermaid = generate_mermaid_graph(graph)

        assert ':::active' in mermaid
        assert ':::deprecated' in mermaid

    def test_handles_conflict_edges(self):
        """Test handles conflict edges with dotted lines."""
        graph = {
            'nodes': [
                {'id': 'RULE-001', 'label': 'Rule 1', 'status': 'ACTIVE'},
                {'id': 'RULE-002', 'label': 'Rule 2', 'status': 'ACTIVE'},
            ],
            'edges': [
                {'source': 'RULE-001', 'target': 'RULE-002', 'type': 'conflicts_with'},
            ],
        }

        from agent.governance_ui.data_access import generate_mermaid_graph
        mermaid = generate_mermaid_graph(graph)

        assert '-.-' in mermaid  # Conflict edge (dotted)


# =============================================================================
# STATE MANAGEMENT TESTS
# =============================================================================

class TestImpactAnalyzerState:
    """Tests for impact analyzer state management."""

    def test_initial_state_has_impact_fields(self):
        """Test initial state includes impact analyzer fields."""
        from agent.governance_ui.state import get_initial_state
        state = get_initial_state()

        assert 'impact_selected_rule' in state
        assert 'impact_analysis' in state
        assert 'dependency_graph' in state
        assert 'mermaid_diagram' in state
        assert 'show_graph_view' in state

    def test_navigation_includes_impact(self):
        """Test navigation items include impact analyzer."""
        from agent.governance_ui.state import NAVIGATION_ITEMS

        nav_values = [item['value'] for item in NAVIGATION_ITEMS]
        assert 'impact' in nav_values

    def test_with_impact_analysis_transform(self):
        """Test with_impact_analysis state transform."""
        from agent.governance_ui.state import get_initial_state, with_impact_analysis

        state = get_initial_state()
        analysis = {'rule_id': 'RULE-001', 'risk_level': 'HIGH'}
        graph = {'nodes': [], 'edges': []}

        new_state = with_impact_analysis(state, 'RULE-001', analysis, graph, 'graph TD')

        assert new_state['impact_selected_rule'] == 'RULE-001'
        assert new_state['impact_analysis'] == analysis
        assert new_state['dependency_graph'] == graph
        assert new_state['mermaid_diagram'] == 'graph TD'

    def test_with_graph_view_transform(self):
        """Test with_graph_view state transform."""
        from agent.governance_ui.state import get_initial_state, with_graph_view

        state = get_initial_state()
        new_state = with_graph_view(state, False)

        assert new_state['show_graph_view'] is False


class TestRiskHelpers:
    """Tests for risk-related helper functions."""

    def test_risk_colors_defined(self):
        """Test risk colors are defined for all levels."""
        from agent.governance_ui.state import RISK_COLORS

        assert 'CRITICAL' in RISK_COLORS
        assert 'HIGH' in RISK_COLORS
        assert 'MEDIUM' in RISK_COLORS
        assert 'LOW' in RISK_COLORS

    def test_get_risk_color(self):
        """Test get_risk_color returns correct colors."""
        from agent.governance_ui.state import get_risk_color

        assert get_risk_color('CRITICAL') == 'error'
        assert get_risk_color('LOW') == 'success'
        assert get_risk_color('UNKNOWN') == 'grey'  # Default

    def test_format_impact_summary(self):
        """Test format_impact_summary formats correctly."""
        from agent.governance_ui.state import format_impact_summary

        impact = {
            'rule_id': 'RULE-001',
            'risk_level': 'HIGH',
            'total_affected': 3,
            'direct_dependents': ['RULE-002', 'RULE-003'],
            'dependencies': ['RULE-004'],
            'recommendation': 'Proceed with caution',
            'critical_rules_affected': [],
        }

        formatted = format_impact_summary(impact)

        assert formatted['rule_id'] == 'RULE-001'
        assert formatted['risk_level'] == 'HIGH'
        assert formatted['risk_color'] == 'warning'
        assert formatted['total_affected'] == 3
        assert formatted['direct_dependents'] == 2
        assert formatted['dependencies'] == 1
