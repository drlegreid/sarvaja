"""
UI Helper Function Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Tests for UI helper pure functions.
"""
import pytest


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
