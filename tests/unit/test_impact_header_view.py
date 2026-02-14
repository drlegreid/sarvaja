"""
Tests for impact header view components.

Per GAP-FILE-001: Modularization of governance_dashboard.py.
Batch 165: New coverage for views/impact/header.py (0->8 tests).
"""
import inspect

import pytest


class TestImpactHeaderComponents:
    def test_build_impact_header_callable(self):
        from agent.governance_ui.views.impact.header import build_impact_header
        assert callable(build_impact_header)

    def test_build_rule_selector_callable(self):
        from agent.governance_ui.views.impact.header import build_rule_selector
        assert callable(build_rule_selector)


class TestImpactHeaderContent:
    def test_has_view_toggle_testid(self):
        from agent.governance_ui.views.impact import header
        source = inspect.getsource(header)
        assert "impact-view-toggle" in source

    def test_has_graph_btn(self):
        from agent.governance_ui.views.impact import header
        source = inspect.getsource(header)
        assert "impact-graph-btn" in source

    def test_has_list_btn(self):
        from agent.governance_ui.views.impact import header
        source = inspect.getsource(header)
        assert "impact-list-btn" in source

    def test_has_graph_icon(self):
        from agent.governance_ui.views.impact import header
        source = inspect.getsource(header)
        assert "mdi-graph" in source


class TestRuleSelectorContent:
    def test_has_rule_select_testid(self):
        from agent.governance_ui.views.impact import header
        source = inspect.getsource(header)
        assert "impact-rule-select" in source

    def test_has_clearable(self):
        from agent.governance_ui.views.impact import header
        source = inspect.getsource(header)
        assert "clearable" in source
