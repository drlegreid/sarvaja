"""
Tests for test runner dashboard view.

Per WORKFLOW-SHELL-01-v1: Self-assessment via containerized tests.
Batch 161: New coverage for views/tests_view.py (0→12 tests).
"""
import inspect

import pytest


class TestTestsViewComponents:
    def test_build_tests_view_callable(self):
        from agent.governance_ui.views.tests_view import build_tests_view
        assert callable(build_tests_view)

    def test_build_tests_header_callable(self):
        from agent.governance_ui.views.tests_view import build_tests_header
        assert callable(build_tests_header)

    def test_build_categories_grid_callable(self):
        from agent.governance_ui.views.tests_view import build_categories_grid
        assert callable(build_categories_grid)

    def test_build_regression_card_callable(self):
        from agent.governance_ui.views.tests_view import build_regression_card
        assert callable(build_regression_card)

    def test_build_test_category_card_callable(self):
        from agent.governance_ui.views.tests_view import build_test_category_card
        assert callable(build_test_category_card)

    def test_build_regression_phases_callable(self):
        from agent.governance_ui.views.tests_view import build_regression_phases_panel
        assert callable(build_regression_phases_panel)


class TestTestsViewContent:
    def test_has_tests_dashboard_testid(self):
        from agent.governance_ui.views import tests_view
        source = inspect.getsource(tests_view)
        assert "tests-dashboard" in source

    def test_has_refresh_button(self):
        from agent.governance_ui.views import tests_view
        source = inspect.getsource(tests_view)
        assert "tests-refresh-btn" in source

    def test_has_regression_card(self):
        from agent.governance_ui.views import tests_view
        source = inspect.getsource(tests_view)
        assert "tests-card-regression" in source

    def test_has_run_regression_button(self):
        from agent.governance_ui.views import tests_view
        source = inspect.getsource(tests_view)
        assert "tests-run-regression" in source

    def test_has_six_categories(self):
        from agent.governance_ui.views import tests_view
        source = inspect.getsource(tests_view)
        for cat in ["unit", "governance", "ui", "kanren", "api", "e2e"]:
            assert f'"{cat}"' in source

    def test_has_regression_phases(self):
        from agent.governance_ui.views import tests_view
        source = inspect.getsource(tests_view)
        assert "regression-phases-panel" in source
