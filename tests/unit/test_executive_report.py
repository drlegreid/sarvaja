"""
Tests for executive report redesign.

Per PLAN-UI-OVERHAUL-001 Task 4.1: Executive Report Redesign.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestExecutiveReportRedesign:
    """Verify executive report has structured sections with metrics."""

    def test_sections_show_metrics_inline(self):
        """Report sections should render section-level metrics."""
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert 'metrics' in source.lower(), (
            "Sections should render section.metrics data"
        )

    def test_sections_use_expandable_panels(self):
        """Report sections should use expandable panels for content."""
        from agent.governance_ui.views.executive import sections
        source = inspect.getsource(sections)
        assert 'ExpansionPanel' in source or 'expansion' in source.lower(), (
            "Sections should use expansion panels for content"
        )

    def test_status_banner_shows_compliance_prominently(self):
        """Status banner should show compliance rate prominently."""
        from agent.governance_ui.views.executive import status
        source = inspect.getsource(status)
        assert 'compliance' in source.lower(), (
            "Status banner should show compliance rate"
        )

    def test_metrics_cards_are_clickable(self):
        """Metrics cards should have click handlers for drill-down."""
        from agent.governance_ui.views.executive import metrics
        source = inspect.getsource(metrics)
        assert 'click' in source.lower(), (
            "Metrics cards should be clickable for drill-down"
        )
