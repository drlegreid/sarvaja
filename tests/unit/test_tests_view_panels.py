"""
Tests for test runner result panels.

Per DOC-SIZE-01-v1: Extracted from tests_view.py.
Batch 161: New coverage for views/tests_view_panels.py (0→10 tests).
"""
import inspect

import pytest


class TestPanelComponents:
    def test_build_current_run_callable(self):
        from agent.governance_ui.views.tests_view_panels import build_current_run_panel
        assert callable(build_current_run_panel)

    def test_build_recent_runs_callable(self):
        from agent.governance_ui.views.tests_view_panels import build_recent_runs_panel
        assert callable(build_recent_runs_panel)

    def test_build_robot_reports_callable(self):
        from agent.governance_ui.views.tests_view_panels import build_robot_reports_panel
        assert callable(build_robot_reports_panel)


class TestPanelContent:
    def test_has_current_run_testid(self):
        from agent.governance_ui.views import tests_view_panels
        source = inspect.getsource(tests_view_panels)
        assert "tests-current-run" in source

    def test_has_recent_runs_testid(self):
        from agent.governance_ui.views import tests_view_panels
        source = inspect.getsource(tests_view_panels)
        assert "tests-recent-runs" in source

    def test_has_robot_reports_testid(self):
        from agent.governance_ui.views import tests_view_panels
        source = inspect.getsource(tests_view_panels)
        assert "robot-reports-panel" in source

    def test_has_robot_view_report_link(self):
        from agent.governance_ui.views import tests_view_panels
        source = inspect.getsource(tests_view_panels)
        assert "robot-view-report" in source

    def test_has_evidence_file_display(self):
        from agent.governance_ui.views import tests_view_panels
        source = inspect.getsource(tests_view_panels)
        assert "evidence_file" in source

    def test_has_passed_failed_display(self):
        from agent.governance_ui.views import tests_view_panels
        source = inspect.getsource(tests_view_panels)
        assert "passed" in source
        assert "failed" in source

    def test_has_duration_display(self):
        from agent.governance_ui.views import tests_view_panels
        source = inspect.getsource(tests_view_panels)
        assert "duration_seconds" in source
