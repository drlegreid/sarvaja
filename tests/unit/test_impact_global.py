"""
Tests for impact analyzer global overview.

Per PLAN-UI-OVERHAUL-001 Task 4.3: Global overview before rule selection.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestImpactGlobalOverview:
    """Verify global overview exists in impact view."""

    def test_impact_view_has_global_overview(self):
        """Impact view should show global overview when no rule selected."""
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views)
        assert 'build_global_overview' in source, (
            "Impact view should have build_global_overview function"
        )

    def test_global_overview_shows_orphaned_rules(self):
        """Global overview should mention orphaned rules."""
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views.build_global_overview)
        assert 'orphan' in source.lower(), (
            "Global overview should show orphaned rules"
        )

    def test_global_overview_shows_dependency_stats(self):
        """Global overview should show dependency statistics."""
        from agent.governance_ui.views.impact import views
        source = inspect.getsource(views.build_global_overview)
        assert 'total' in source.lower() or 'dependencies' in source.lower(), (
            "Global overview should show dependency stats"
        )

    def test_impact_api_has_overview_endpoint(self):
        """API should have /rules/dependencies/overview endpoint."""
        from governance.routes.rules import crud
        source = inspect.getsource(crud)
        assert 'dependencies/overview' in source or 'dependency_overview' in source, (
            "Rules API should have dependencies overview endpoint"
        )
