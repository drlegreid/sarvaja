"""
Tests for tasks execution log view components.

Per ORCH-007: Task execution log timeline.
Batch 164: New coverage for views/tasks/execution.py (0->10 tests).
"""
import inspect

import pytest


class TestTasksExecutionComponents:
    def test_build_execution_timeline_callable(self):
        from agent.governance_ui.views.tasks.execution import build_execution_timeline
        assert callable(build_execution_timeline)

    def test_build_task_execution_log_callable(self):
        from agent.governance_ui.views.tasks.execution import build_task_execution_log
        assert callable(build_task_execution_log)


class TestExecutionTimelineContent:
    def test_has_timeline_testid(self):
        from agent.governance_ui.views.tasks import execution
        source = inspect.getsource(execution)
        assert "task-execution-timeline" in source

    def test_has_event_testid(self):
        from agent.governance_ui.views.tasks import execution
        source = inspect.getsource(execution)
        assert "task-execution-event" in source

    def test_has_event_type_icons(self):
        from agent.governance_ui.views.tasks import execution
        source = inspect.getsource(execution)
        assert "mdi-check-circle" in source
        assert "mdi-alert-circle" in source
        assert "mdi-progress-clock" in source

    def test_has_agent_id_chip(self):
        from agent.governance_ui.views.tasks import execution
        source = inspect.getsource(execution)
        assert "event.agent_id" in source


class TestTaskExecutionLogContent:
    def test_has_log_testid(self):
        from agent.governance_ui.views.tasks import execution
        source = inspect.getsource(execution)
        assert "task-execution-log" in source

    def test_has_refresh_btn(self):
        from agent.governance_ui.views.tasks import execution
        source = inspect.getsource(execution)
        assert "task-execution-refresh" in source

    def test_has_timeline_clock_icon(self):
        from agent.governance_ui.views.tasks import execution
        source = inspect.getsource(execution)
        assert "mdi-timeline-clock" in source

    def test_has_empty_state(self):
        from agent.governance_ui.views.tasks import execution
        source = inspect.getsource(execution)
        assert "No execution events recorded" in source
