"""
UI Filter Function Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Tests for rule filter pure functions.
"""
import pytest


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
