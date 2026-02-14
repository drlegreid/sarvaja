"""
Tests for impact view main entry point.

Per GAP-FILE-001: Modularization of governance_dashboard.py.
Batch 165: New coverage for views/impact_view.py (0->8 tests).
"""
import inspect

import pytest


class TestImpactViewMainComponents:
    def test_build_impact_view_callable(self):
        from agent.governance_ui.views.impact_view import build_impact_view
        assert callable(build_impact_view)


class TestImpactViewMainImports:
    def test_imports_header(self):
        from agent.governance_ui.views import impact_view
        source = inspect.getsource(impact_view)
        assert "build_impact_header" in source

    def test_imports_rule_selector(self):
        from agent.governance_ui.views import impact_view
        source = inspect.getsource(impact_view)
        assert "build_rule_selector" in source

    def test_imports_analysis_results(self):
        from agent.governance_ui.views import impact_view
        source = inspect.getsource(impact_view)
        assert "build_analysis_results" in source

    def test_imports_graph_view(self):
        from agent.governance_ui.views import impact_view
        source = inspect.getsource(impact_view)
        assert "build_graph_view" in source

    def test_imports_empty_state(self):
        from agent.governance_ui.views import impact_view
        source = inspect.getsource(impact_view)
        assert "build_empty_state" in source

    def test_has_analyzer_testid(self):
        from agent.governance_ui.views import impact_view
        source = inspect.getsource(impact_view)
        assert "impact-analyzer" in source

    def test_imports_global_overview(self):
        from agent.governance_ui.views import impact_view
        source = inspect.getsource(impact_view)
        assert "build_global_overview" in source
