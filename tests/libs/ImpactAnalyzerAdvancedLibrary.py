"""
Robot Framework Library for Impact Analyzer Advanced Tests.

Per P9.4: Mermaid graph generation, state management, and risk helpers.
Split from ImpactAnalyzerLibrary.py per DOC-SIZE-01-v1.
"""
from unittest.mock import patch
from robot.api.deco import keyword


# Constants for mocking
IMPACT_MODULE = 'agent.governance_ui.data_access.impact'


class ImpactAnalyzerAdvancedLibrary:
    """Library for testing impact analyzer: mermaid, state, and risk helpers."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Generate Mermaid Graph Tests
    # =============================================================================

    @keyword("Generate Mermaid Syntax")
    def generate_mermaid_syntax(self):
        """Test generates valid Mermaid diagram syntax."""
        try:
            from agent.governance_ui.data_access import generate_mermaid_graph
            graph = {
                'nodes': [
                    {'id': 'RULE-001', 'label': 'Rule 1', 'status': 'ACTIVE'},
                    {'id': 'RULE-002', 'label': 'Rule 2', 'status': 'DRAFT'},
                ],
                'edges': [
                    {'source': 'RULE-002', 'target': 'RULE-001', 'type': 'depends_on'},
                ],
            }

            mermaid = generate_mermaid_graph(graph)

            return {
                "has_graph_td": 'graph TD' in mermaid,
                "has_rule_001": 'RULE_001' in mermaid,
                "has_rule_002": 'RULE_002' in mermaid,
                "has_edge": '-->' in mermaid
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Mermaid Applies Status Classes")
    def generate_mermaid_applies_status_classes(self):
        """Test applies CSS classes based on status."""
        try:
            from agent.governance_ui.data_access import generate_mermaid_graph
            graph = {
                'nodes': [
                    {'id': 'RULE-001', 'label': 'Active Rule', 'status': 'ACTIVE'},
                    {'id': 'RULE-002', 'label': 'Deprecated Rule', 'status': 'DEPRECATED'},
                ],
                'edges': [],
            }

            mermaid = generate_mermaid_graph(graph)

            return {
                "has_active": ':::active' in mermaid,
                "has_deprecated": ':::deprecated' in mermaid
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Generate Mermaid Handles Conflict Edges")
    def generate_mermaid_handles_conflict_edges(self):
        """Test handles conflict edges with dotted lines."""
        try:
            from agent.governance_ui.data_access import generate_mermaid_graph
            graph = {
                'nodes': [
                    {'id': 'RULE-001', 'label': 'Rule 1', 'status': 'ACTIVE'},
                    {'id': 'RULE-002', 'label': 'Rule 2', 'status': 'ACTIVE'},
                ],
                'edges': [
                    {'source': 'RULE-001', 'target': 'RULE-002', 'type': 'conflicts_with'},
                ],
            }

            mermaid = generate_mermaid_graph(graph)

            return {"has_dotted": '-.-' in mermaid}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # State Management Tests
    # =============================================================================

    @keyword("Initial State Has Impact Fields")
    def initial_state_has_impact_fields(self):
        """Test initial state includes impact analyzer fields."""
        try:
            from agent.governance_ui.state import get_initial_state
            state = get_initial_state()

            return {
                "has_selected": 'impact_selected_rule' in state,
                "has_analysis": 'impact_analysis' in state,
                "has_graph": 'dependency_graph' in state,
                "has_mermaid": 'mermaid_diagram' in state,
                "has_view": 'show_graph_view' in state
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Navigation Includes Impact")
    def navigation_includes_impact(self):
        """Test navigation items include impact analyzer."""
        try:
            from agent.governance_ui.state import NAVIGATION_ITEMS
            nav_values = [item['value'] for item in NAVIGATION_ITEMS]
            return {"has_impact": 'impact' in nav_values}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Impact Analysis Transform")
    def with_impact_analysis_transform(self):
        """Test with_impact_analysis state transform."""
        try:
            from agent.governance_ui.state import get_initial_state, with_impact_analysis

            state = get_initial_state()
            analysis = {'rule_id': 'RULE-001', 'risk_level': 'HIGH'}
            graph = {'nodes': [], 'edges': []}

            new_state = with_impact_analysis(state, 'RULE-001', analysis, graph, 'graph TD')

            return {
                "selected_rule": new_state['impact_selected_rule'] == 'RULE-001',
                "analysis_set": new_state['impact_analysis'] == analysis,
                "graph_set": new_state['dependency_graph'] == graph,
                "mermaid_set": new_state['mermaid_diagram'] == 'graph TD'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Graph View Transform")
    def with_graph_view_transform(self):
        """Test with_graph_view state transform."""
        try:
            from agent.governance_ui.state import get_initial_state, with_graph_view

            state = get_initial_state()
            new_state = with_graph_view(state, False)

            return {"view_false": new_state['show_graph_view'] is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Risk Helpers Tests
    # =============================================================================

    @keyword("Risk Colors Defined")
    def risk_colors_defined(self):
        """Test risk colors are defined for all levels."""
        try:
            from agent.governance_ui.state import RISK_COLORS
            return {
                "has_critical": 'CRITICAL' in RISK_COLORS,
                "has_high": 'HIGH' in RISK_COLORS,
                "has_medium": 'MEDIUM' in RISK_COLORS,
                "has_low": 'LOW' in RISK_COLORS
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Risk Color")
    def get_risk_color(self):
        """Test get_risk_color returns correct colors."""
        try:
            from agent.governance_ui.state import get_risk_color
            return {
                "critical_error": get_risk_color('CRITICAL') == 'error',
                "low_success": get_risk_color('LOW') == 'success',
                "unknown_grey": get_risk_color('UNKNOWN') == 'grey'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Format Impact Summary")
    def format_impact_summary(self):
        """Test format_impact_summary formats correctly."""
        try:
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

            return {
                "rule_id": formatted['rule_id'] == 'RULE-001',
                "risk_level": formatted['risk_level'] == 'HIGH',
                "risk_color": formatted['risk_color'] == 'warning',
                "total_affected": formatted['total_affected'] == 3,
                "direct_dependents": formatted['direct_dependents'] == 2,
                "dependencies": formatted['dependencies'] == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
