"""
Tests for chat task execution components.

Per GAP-UI-CHAT-002: Task execution viewing.
Per ORCH-007: Task execution timeline.
Batch 164: New coverage for views/chat/execution.py (0->10 tests).
"""
import inspect

import pytest


class TestChatExecutionComponents:
    def test_build_task_execution_button_callable(self):
        from agent.governance_ui.views.chat.execution import build_task_execution_button
        assert callable(build_task_execution_button)

    def test_build_task_execution_viewer_callable(self):
        from agent.governance_ui.views.chat.execution import build_task_execution_viewer
        assert callable(build_task_execution_viewer)


class TestTaskExecutionButtonContent:
    def test_has_button_testid(self):
        from agent.governance_ui.views.chat import execution
        source = inspect.getsource(execution)
        assert "view-execution-btn" in source

    def test_has_timeline_clock_icon(self):
        from agent.governance_ui.views.chat import execution
        source = inspect.getsource(execution)
        assert "mdi-timeline-clock" in source


class TestTaskExecutionViewerContent:
    def test_has_dialog_testid(self):
        from agent.governance_ui.views.chat import execution
        source = inspect.getsource(execution)
        assert "task-execution-dialog" in source

    def test_has_close_btn(self):
        from agent.governance_ui.views.chat import execution
        source = inspect.getsource(execution)
        assert "execution-close-btn" in source

    def test_has_timeline_testid(self):
        from agent.governance_ui.views.chat import execution
        source = inspect.getsource(execution)
        assert "execution-timeline" in source

    def test_has_event_testid(self):
        from agent.governance_ui.views.chat import execution
        source = inspect.getsource(execution)
        assert "execution-event" in source

    def test_has_event_type_icons(self):
        from agent.governance_ui.views.chat import execution
        source = inspect.getsource(execution)
        assert "mdi-check-circle" in source
        assert "mdi-alert-circle" in source

    def test_has_loading_state(self):
        from agent.governance_ui.views.chat import execution
        source = inspect.getsource(execution)
        assert "task_execution_loading" in source
