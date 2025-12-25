"""
Governance Dashboard UI Tests (P9.2)
Created: 2024-12-25
Updated: 2024-12-25 (Updated for DSP refactored architecture)

Tests for Trame-based governance dashboard.
Strategic Goal: View all task/session/evidence artifacts via UI.

Architecture (per DSP):
    agent/governance_ui/data_access.py - Pure MCP data functions (tested here)
    agent/governance_ui/state.py       - Immutable state, transforms (tested here)
    agent/governance_dashboard.py      - Trame view layer (GovernanceDashboard class)
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
AGENT_DIR = PROJECT_ROOT / "agent"

# Mock path for TypeDB client
TYPEDB_CLIENT_MOCK_PATH = 'governance.mcp_tools.common.get_typedb_client'


class TestGovernanceUIModuleExists:
    """Verify P9.2 governance UI module exists."""

    @pytest.mark.unit
    def test_governance_ui_package_exists(self):
        """Governance UI package must exist."""
        ui_dir = AGENT_DIR / "governance_ui"
        assert ui_dir.exists(), "agent/governance_ui/ package not found"
        assert (ui_dir / "__init__.py").exists(), "__init__.py not found"
        assert (ui_dir / "data_access.py").exists(), "data_access.py not found"
        assert (ui_dir / "state.py").exists(), "state.py not found"

    @pytest.mark.unit
    def test_governance_dashboard_exists(self):
        """Governance dashboard module must exist."""
        dashboard_file = AGENT_DIR / "governance_dashboard.py"
        assert dashboard_file.exists(), "agent/governance_dashboard.py not found"

    @pytest.mark.unit
    def test_governance_dashboard_class_importable(self):
        """GovernanceDashboard class must be importable."""
        from agent.governance_dashboard import GovernanceDashboard

        dashboard = GovernanceDashboard()
        assert dashboard is not None
        assert hasattr(dashboard, 'build_ui')
        assert hasattr(dashboard, 'run')


class TestDataAccessFunctions:
    """Tests for data access pure functions."""

    @pytest.mark.unit
    def test_get_rules_importable(self):
        """get_rules function must be importable."""
        from agent.governance_ui import get_rules
        assert callable(get_rules)

    @pytest.mark.unit
    def test_get_rules_by_category_importable(self):
        """get_rules_by_category function must be importable."""
        from agent.governance_ui import get_rules_by_category
        assert callable(get_rules_by_category)

    @pytest.mark.unit
    def test_get_decisions_importable(self):
        """get_decisions function must be importable."""
        from agent.governance_ui import get_decisions
        assert callable(get_decisions)

    @pytest.mark.unit
    def test_get_sessions_importable(self):
        """get_sessions function must be importable."""
        from agent.governance_ui import get_sessions
        assert callable(get_sessions)

    @pytest.mark.unit
    def test_get_tasks_importable(self):
        """get_tasks function must be importable."""
        from agent.governance_ui import get_tasks
        assert callable(get_tasks)

    @pytest.mark.unit
    def test_search_evidence_importable(self):
        """search_evidence function must be importable."""
        from agent.governance_ui import search_evidence
        assert callable(search_evidence)

    @pytest.mark.unit
    @patch(TYPEDB_CLIENT_MOCK_PATH)
    def test_get_rules_returns_list(self, mock_client):
        """get_rules should return a list."""
        from agent.governance_ui import get_rules

        mock_tx = MagicMock()
        mock_tx.query.fetch.return_value = iter([])
        mock_client.return_value.__enter__.return_value.transaction.return_value.__enter__.return_value = mock_tx

        result = get_rules()
        assert isinstance(result, list)

    @pytest.mark.unit
    @patch(TYPEDB_CLIENT_MOCK_PATH)
    def test_get_decisions_returns_list(self, mock_client):
        """get_decisions should return a list."""
        from agent.governance_ui import get_decisions

        mock_tx = MagicMock()
        mock_tx.query.fetch.return_value = iter([])
        mock_client.return_value.__enter__.return_value.transaction.return_value.__enter__.return_value = mock_tx

        result = get_decisions()
        assert isinstance(result, list)


class TestFilterFunctions:
    """Tests for rule filter pure functions."""

    @pytest.fixture
    def sample_rules(self):
        """Sample rules for filter testing."""
        return [
            {'rule_id': 'RULE-001', 'status': 'ACTIVE', 'category': 'governance', 'title': 'Session Evidence'},
            {'rule_id': 'RULE-002', 'status': 'ACTIVE', 'category': 'technical', 'title': 'Code Standards'},
            {'rule_id': 'RULE-003', 'status': 'DRAFT', 'category': 'governance', 'title': 'Gap Tracking'},
        ]

    @pytest.mark.unit
    def test_filter_rules_by_status(self, sample_rules):
        """Should filter rules by status."""
        from agent.governance_ui import filter_rules_by_status

        active = filter_rules_by_status(sample_rules, 'ACTIVE')
        assert len(active) == 2
        for rule in active:
            assert rule['status'] == 'ACTIVE'

    @pytest.mark.unit
    def test_filter_rules_by_category(self, sample_rules):
        """Should filter rules by category."""
        from agent.governance_ui import filter_rules_by_category

        governance = filter_rules_by_category(sample_rules, 'governance')
        assert len(governance) == 2
        for rule in governance:
            assert rule['category'] == 'governance'

    @pytest.mark.unit
    def test_filter_rules_by_search(self, sample_rules):
        """Should filter rules by search query."""
        from agent.governance_ui import filter_rules_by_search

        matches = filter_rules_by_search(sample_rules, 'Evidence')
        assert len(matches) == 1
        assert matches[0]['rule_id'] == 'RULE-001'

    @pytest.mark.unit
    def test_sort_rules(self, sample_rules):
        """Should sort rules by column."""
        from agent.governance_ui import sort_rules

        sorted_asc = sort_rules(sample_rules, 'rule_id', ascending=True)
        assert sorted_asc[0]['rule_id'] == 'RULE-001'
        assert sorted_asc[-1]['rule_id'] == 'RULE-003'

        sorted_desc = sort_rules(sample_rules, 'rule_id', ascending=False)
        assert sorted_desc[0]['rule_id'] == 'RULE-003'


class TestStateFunctions:
    """Tests for state management pure functions."""

    @pytest.mark.unit
    def test_get_initial_state_factory(self):
        """get_initial_state should return fresh state each call."""
        from agent.governance_ui import get_initial_state

        state1 = get_initial_state()
        state2 = get_initial_state()

        # Should be different objects
        assert state1 is not state2

        # Modify one, other unchanged
        state1['active_view'] = 'modified'
        assert state2['active_view'] == 'rules'

    @pytest.mark.unit
    def test_initial_state_has_required_keys(self):
        """Initial state should have all required keys."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()

        assert 'active_view' in state
        assert 'rules' in state
        assert 'decisions' in state
        assert 'sessions' in state
        assert 'selected_rule' in state
        assert 'search_query' in state

    @pytest.mark.unit
    def test_with_loading_transform(self):
        """with_loading should return new state with loading flag."""
        from agent.governance_ui import get_initial_state, with_loading

        state = get_initial_state()
        new_state = with_loading(state, True)

        assert state is not new_state
        assert new_state['is_loading'] is True
        assert state['is_loading'] is False

    @pytest.mark.unit
    def test_with_error_transform(self):
        """with_error should return new state with error set."""
        from agent.governance_ui import get_initial_state, with_error

        state = get_initial_state()
        new_state = with_error(state, "Test error")

        assert new_state['has_error'] is True
        assert new_state['error_message'] == "Test error"

    @pytest.mark.unit
    def test_clear_error_transform(self):
        """clear_error should return new state with error cleared."""
        from agent.governance_ui import get_initial_state, with_error, clear_error

        state = with_error(get_initial_state(), "Test error")
        new_state = clear_error(state)

        assert new_state['has_error'] is False
        assert new_state['error_message'] == ''


class TestNavigationItems:
    """Tests for navigation configuration."""

    @pytest.mark.unit
    def test_navigation_items_exist(self):
        """NAVIGATION_ITEMS should be defined."""
        from agent.governance_ui import NAVIGATION_ITEMS

        assert isinstance(NAVIGATION_ITEMS, list)
        assert len(NAVIGATION_ITEMS) > 0

    @pytest.mark.unit
    def test_navigation_has_required_views(self):
        """Navigation should include required views."""
        from agent.governance_ui import NAVIGATION_ITEMS

        nav_values = [item['value'] for item in NAVIGATION_ITEMS]

        assert 'rules' in nav_values
        assert 'decisions' in nav_values
        assert 'sessions' in nav_values
        assert 'tasks' in nav_values
        assert 'impact' in nav_values
        assert 'trust' in nav_values

    @pytest.mark.unit
    def test_navigation_items_have_structure(self):
        """Navigation items should have title, icon, value."""
        from agent.governance_ui import NAVIGATION_ITEMS

        for item in NAVIGATION_ITEMS:
            assert 'title' in item
            assert 'icon' in item
            assert 'value' in item


class TestUIHelpers:
    """Tests for UI helper pure functions."""

    @pytest.mark.unit
    def test_get_status_color(self):
        """get_status_color should map status to colors."""
        from agent.governance_ui import get_status_color

        assert get_status_color('ACTIVE') == 'success'
        assert get_status_color('DRAFT') == 'grey'
        assert get_status_color('DEPRECATED') == 'warning'
        assert get_status_color('unknown') == 'grey'

    @pytest.mark.unit
    def test_get_priority_color(self):
        """get_priority_color should map priority to colors."""
        from agent.governance_ui import get_priority_color

        assert get_priority_color('CRITICAL') == 'error'
        assert get_priority_color('HIGH') == 'warning'
        assert get_priority_color('MEDIUM') == 'grey'
        assert get_priority_color('LOW') == 'grey-lighten-1'

    @pytest.mark.unit
    def test_get_category_icon(self):
        """get_category_icon should map category to icons."""
        from agent.governance_ui import get_category_icon

        assert 'mdi-' in get_category_icon('governance')
        assert 'mdi-' in get_category_icon('technical')
        assert 'mdi-' in get_category_icon('unknown')

    @pytest.mark.unit
    def test_format_rule_card(self):
        """format_rule_card should format rule for display."""
        from agent.governance_ui import format_rule_card

        rule = {
            'rule_id': 'RULE-001',
            'title': 'Test Rule',
            'status': 'ACTIVE',
            'category': 'governance',
        }

        card = format_rule_card(rule)

        assert 'title' in card
        assert 'subtitle' in card
        assert 'color' in card
        assert 'icon' in card


class TestFactoryFunction:
    """Tests for UI factory function."""

    @pytest.mark.unit
    def test_create_governance_dashboard(self):
        """Factory function should create dashboard."""
        from agent.governance_dashboard import create_governance_dashboard

        dashboard = create_governance_dashboard()
        assert dashboard is not None

    @pytest.mark.unit
    def test_factory_with_custom_port(self):
        """Factory should accept port parameter."""
        from agent.governance_dashboard import create_governance_dashboard

        dashboard = create_governance_dashboard(port=9090)
        assert dashboard.port == 9090

    @pytest.mark.unit
    def test_default_port(self):
        """Default port should be 8081."""
        from agent.governance_dashboard import create_governance_dashboard

        dashboard = create_governance_dashboard()
        assert dashboard.port == 8081


class TestConstantsExport:
    """Tests that constants are properly exported."""

    @pytest.mark.unit
    def test_status_colors_exported(self):
        """STATUS_COLORS should be exported."""
        from agent.governance_ui import STATUS_COLORS
        assert isinstance(STATUS_COLORS, dict)

    @pytest.mark.unit
    def test_priority_colors_exported(self):
        """PRIORITY_COLORS should be exported."""
        from agent.governance_ui import PRIORITY_COLORS
        assert isinstance(PRIORITY_COLORS, dict)

    @pytest.mark.unit
    def test_category_icons_exported(self):
        """CATEGORY_ICONS should be exported."""
        from agent.governance_ui import CATEGORY_ICONS
        assert isinstance(CATEGORY_ICONS, dict)

    @pytest.mark.unit
    def test_rule_categories_exported(self):
        """RULE_CATEGORIES should be exported."""
        from agent.governance_ui import RULE_CATEGORIES
        assert isinstance(RULE_CATEGORIES, list)

    @pytest.mark.unit
    def test_rule_priorities_exported(self):
        """RULE_PRIORITIES should be exported."""
        from agent.governance_ui import RULE_PRIORITIES
        assert isinstance(RULE_PRIORITIES, list)

    @pytest.mark.unit
    def test_rule_statuses_exported(self):
        """RULE_STATUSES should be exported."""
        from agent.governance_ui import RULE_STATUSES
        assert isinstance(RULE_STATUSES, list)
