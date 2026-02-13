"""
Tests for backlog view component.

Per RULE-014: Autonomous Task Sequencing.
Batch 161: New coverage for views/backlog_view.py (0→12 tests).
"""
import inspect

import pytest


class TestBacklogViewComponents:
    def test_build_backlog_view_callable(self):
        from agent.governance_ui.views.backlog_view import build_backlog_view
        assert callable(build_backlog_view)

    def test_build_backlog_header_callable(self):
        from agent.governance_ui.views.backlog_view import build_backlog_header
        assert callable(build_backlog_header)

    def test_build_available_tasks_callable(self):
        from agent.governance_ui.views.backlog_view import build_available_tasks_column
        assert callable(build_available_tasks_column)

    def test_build_claimed_tasks_callable(self):
        from agent.governance_ui.views.backlog_view import build_claimed_tasks_column
        assert callable(build_claimed_tasks_column)


class TestBacklogViewContent:
    def test_has_backlog_view_testid(self):
        from agent.governance_ui.views import backlog_view
        source = inspect.getsource(backlog_view)
        assert "backlog-view" in source

    def test_has_agent_id_input(self):
        from agent.governance_ui.views import backlog_view
        source = inspect.getsource(backlog_view)
        assert "backlog-agent-id-input" in source

    def test_has_auto_refresh_button(self):
        from agent.governance_ui.views import backlog_view
        source = inspect.getsource(backlog_view)
        assert "backlog-auto-refresh-btn" in source

    def test_has_refresh_button(self):
        from agent.governance_ui.views import backlog_view
        source = inspect.getsource(backlog_view)
        assert "backlog-refresh-btn" in source

    def test_has_claim_button(self):
        from agent.governance_ui.views import backlog_view
        source = inspect.getsource(backlog_view)
        assert "backlog-claim-btn" in source

    def test_has_complete_button(self):
        from agent.governance_ui.views import backlog_view
        source = inspect.getsource(backlog_view)
        assert "backlog-complete-btn" in source

    def test_has_pagination(self):
        from agent.governance_ui.views import backlog_view
        source = inspect.getsource(backlog_view)
        assert "backlog-pagination" in source

    def test_has_available_task_testid(self):
        from agent.governance_ui.views import backlog_view
        source = inspect.getsource(backlog_view)
        assert "backlog-available-task" in source
