"""
Tests for impact view components (graph and list).

Per GAP-FILE-001: Modularization of governance_dashboard.py.
Batch 162: New coverage for views/impact/views.py (0→10 tests).
"""
import inspect

import pytest


class TestImpactViewComponents:
    def test_build_graph_view_callable(self):
        from agent.governance_ui.views.impact.views import build_graph_view
        assert callable(build_graph_view)

    def test_build_list_view_callable(self):
        from agent.governance_ui.views.impact.views import build_list_view
        assert callable(build_list_view)

    def test_build_global_overview_callable(self):
        from agent.governance_ui.views.impact.views import build_global_overview
        assert callable(build_global_overview)

    def test_build_empty_state_callable(self):
        from agent.governance_ui.views.impact.views import build_empty_state
        assert callable(build_empty_state)


class TestImpactViewContent:
    def test_has_graph_card_testid(self):
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views)
        assert "impact-graph-card" in source

    def test_has_dependents_list(self):
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views)
        assert "impact-dependents-list" in source

    def test_has_dependencies_list(self):
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views)
        assert "impact-dependencies-list" in source

    def test_has_overview_stats(self):
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views)
        assert "overview-total-stats" in source

    def test_has_orphan_rules(self):
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views)
        assert "overview-orphan-rules" in source

    def test_has_empty_state(self):
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views)
        assert "impact-empty-state" in source
