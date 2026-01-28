"""
Robot Framework Library for Impact Analyzer Tests.

Per P9.4: Rule impact analysis and dependency graph.
Migrated from tests/test_impact_analyzer.py
"""
from unittest.mock import Mock, patch
from robot.api.deco import keyword


# Constants for mocking
TYPEDB_CLIENT_MOCK_PATH = 'governance.mcp_tools.common.get_typedb_client'
IMPACT_MODULE = 'agent.governance_ui.data_access.impact'


class ImpactAnalyzerLibrary:
    """Library for testing impact analyzer functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_sample_rules(self):
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

    # =============================================================================
    # Get Rule Dependencies Tests
    # =============================================================================

    @keyword("Get Rule Dependencies Connection Failure")
    def get_rule_dependencies_connection_failure(self):
        """Test returns empty list when connection fails."""
        try:
            from agent.governance_ui.data_access import get_rule_dependencies
            with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
                mock_client = Mock()
                mock_client.connect.return_value = False
                mock_get_client.return_value = mock_client

                result = get_rule_dependencies('RULE-001')

                return {
                    "empty_result": result == [],
                    "close_called": mock_client.close.called
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Rule Dependencies Returns List")
    def get_rule_dependencies_returns_list(self):
        """Test returns list of dependency IDs."""
        try:
            from agent.governance_ui.data_access import get_rule_dependencies
            mock_client = Mock()
            mock_client.connect.return_value = True
            mock_client.get_rule_dependencies.return_value = ['RULE-002', 'RULE-003']

            with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
                result = get_rule_dependencies('RULE-001')

                return {
                    "correct_result": result == ['RULE-002', 'RULE-003']
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Rule Dependencies Empty When None")
    def get_rule_dependencies_empty_when_none(self):
        """Test returns empty list when rule has no dependencies."""
        try:
            from agent.governance_ui.data_access import get_rule_dependencies
            mock_client = Mock()
            mock_client.connect.return_value = True
            mock_client.get_rule_dependencies.return_value = []

            with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
                result = get_rule_dependencies('RULE-001')

                return {"empty_result": result == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Get Rule Dependents Tests
    # =============================================================================

    @keyword("Get Rule Dependents Connection Failure")
    def get_rule_dependents_connection_failure(self):
        """Test returns empty list when connection fails."""
        try:
            from agent.governance_ui.data_access import get_rule_dependents
            with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
                mock_client = Mock()
                mock_client.connect.return_value = False
                mock_get_client.return_value = mock_client

                result = get_rule_dependents('RULE-001')

                return {"empty_result": result == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Rule Dependents Returns List")
    def get_rule_dependents_returns_list(self):
        """Test returns list of dependent rule IDs."""
        try:
            from agent.governance_ui.data_access import get_rule_dependents
            mock_client = Mock()
            mock_client.connect.return_value = True
            mock_client.get_rules_depending_on.return_value = ['RULE-002', 'RULE-003']

            with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
                result = get_rule_dependents('RULE-001')

                return {
                    "correct_result": result == ['RULE-002', 'RULE-003']
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Get Rule Conflicts Tests
    # =============================================================================

    @keyword("Get Rule Conflicts Connection Failure")
    def get_rule_conflicts_connection_failure(self):
        """Test returns empty list when connection fails."""
        try:
            from agent.governance_ui.data_access import get_rule_conflicts
            with patch(TYPEDB_CLIENT_MOCK_PATH) as mock_get_client:
                mock_client = Mock()
                mock_client.connect.return_value = False
                mock_get_client.return_value = mock_client

                result = get_rule_conflicts()

                return {"empty_result": result == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Rule Conflicts Returns List")
    def get_rule_conflicts_returns_list(self):
        """Test returns list of conflict dicts."""
        try:
            from agent.governance_ui.data_access import get_rule_conflicts
            mock_client = Mock()
            mock_client.connect.return_value = True
            mock_client.find_conflicts.return_value = [
                {'rule1': 'RULE-001', 'rule2': 'RULE-002', 'reason': 'Conflicting directives'}
            ]

            with patch(TYPEDB_CLIENT_MOCK_PATH, return_value=mock_client):
                result = get_rule_conflicts()

                return {
                    "has_one": len(result) == 1,
                    "correct_reason": result[0]['reason'] == 'Conflicting directives'
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Build Dependency Graph Tests
    # =============================================================================

    @keyword("Build Dependency Graph Nodes From Rules")
    def build_dependency_graph_nodes_from_rules(self):
        """Test builds node list from rules."""
        try:
            from agent.governance_ui.data_access import build_dependency_graph
            sample_rules = self._get_sample_rules()

            with patch(f'{IMPACT_MODULE}.get_rule_dependencies', return_value=[]):
                with patch(f'{IMPACT_MODULE}.get_rule_conflicts', return_value=[]):
                    graph = build_dependency_graph(sample_rules)

                    return {
                        "nodes_count": len(graph['nodes']) == 4,
                        "stats_count": graph['stats']['total_nodes'] == 4
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Build Dependency Graph Edges From Dependencies")
    def build_dependency_graph_edges_from_dependencies(self):
        """Test builds edge list from dependencies."""
        try:
            from agent.governance_ui.data_access import build_dependency_graph
            sample_rules = self._get_sample_rules()

            def mock_deps(rule_id):
                if rule_id == 'RULE-002':
                    return ['RULE-001']
                return []

            with patch(f'{IMPACT_MODULE}.get_rule_dependencies', side_effect=mock_deps):
                with patch(f'{IMPACT_MODULE}.get_rule_conflicts', return_value=[]):
                    graph = build_dependency_graph(sample_rules)

                    edge = [e for e in graph['edges'] if e['type'] == 'depends_on']
                    return {
                        "one_edge": graph['stats']['dependency_edges'] == 1,
                        "source_correct": edge[0]['source'] == 'RULE-002' if edge else False,
                        "target_correct": edge[0]['target'] == 'RULE-001' if edge else False
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Build Dependency Graph Includes Conflict Edges")
    def build_dependency_graph_includes_conflict_edges(self):
        """Test includes conflict edges in graph."""
        try:
            from agent.governance_ui.data_access import build_dependency_graph
            sample_rules = self._get_sample_rules()

            with patch(f'{IMPACT_MODULE}.get_rule_dependencies', return_value=[]):
                with patch(f'{IMPACT_MODULE}.get_rule_conflicts', return_value=[
                    {'rule1': 'RULE-001', 'rule2': 'RULE-002', 'reason': 'Conflict'}
                ]):
                    graph = build_dependency_graph(sample_rules)

                    return {
                        "one_conflict": graph['stats']['conflict_edges'] == 1
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Calculate Rule Impact Tests
    # =============================================================================

    @keyword("Calculate Rule Impact Low Risk No Dependents")
    def calculate_rule_impact_low_risk_no_dependents(self):
        """Test returns LOW risk when no rules depend on this rule."""
        try:
            from agent.governance_ui.data_access import calculate_rule_impact
            sample_rules = self._get_sample_rules()

            with patch(f'{IMPACT_MODULE}.get_rule_dependents', return_value=[]):
                with patch(f'{IMPACT_MODULE}.get_rule_dependencies', return_value=[]):
                    impact = calculate_rule_impact('RULE-004', sample_rules)

                    return {
                        "low_risk": impact['risk_level'] == 'LOW',
                        "zero_affected": impact['total_affected'] == 0
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Calculate Rule Impact Medium Risk Few Dependents")
    def calculate_rule_impact_medium_risk_few_dependents(self):
        """Test returns MEDIUM risk when 1-2 rules depend on this rule."""
        try:
            from agent.governance_ui.data_access import calculate_rule_impact
            sample_rules = self._get_sample_rules()

            with patch(f'{IMPACT_MODULE}.get_rule_dependents', return_value=['RULE-002']):
                with patch(f'{IMPACT_MODULE}.get_rule_dependencies', return_value=[]):
                    impact = calculate_rule_impact('RULE-001', sample_rules)

                    return {
                        "medium_risk": impact['risk_level'] == 'MEDIUM',
                        "one_affected": impact['total_affected'] == 1
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Calculate Rule Impact Critical When Critical Affected")
    def calculate_rule_impact_critical_when_critical_affected(self):
        """Test returns CRITICAL when a CRITICAL priority rule is affected."""
        try:
            from agent.governance_ui.data_access import calculate_rule_impact
            sample_rules = self._get_sample_rules()

            with patch(f'{IMPACT_MODULE}.get_rule_dependents', return_value=['RULE-001']):
                with patch(f'{IMPACT_MODULE}.get_rule_dependencies', return_value=[]):
                    impact = calculate_rule_impact('RULE-002', sample_rules)

                    return {
                        "critical_risk": impact['risk_level'] == 'CRITICAL',
                        "critical_affected": 'RULE-001' in impact['critical_rules_affected']
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Calculate Rule Impact Includes Recommendation")
    def calculate_rule_impact_includes_recommendation(self):
        """Test includes recommendation based on risk level."""
        try:
            from agent.governance_ui.data_access import calculate_rule_impact
            sample_rules = self._get_sample_rules()

            with patch(f'{IMPACT_MODULE}.get_rule_dependents', return_value=[]):
                with patch(f'{IMPACT_MODULE}.get_rule_dependencies', return_value=[]):
                    impact = calculate_rule_impact('RULE-004', sample_rules)

                    return {
                        "has_recommendation": 'recommendation' in impact,
                        "has_safe": 'SAFE' in impact['recommendation']
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

