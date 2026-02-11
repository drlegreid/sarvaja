"""
Unit tests for AG-UI Task Models & Store.

Per DOC-SIZE-01-v1: Tests for extracted task_ui_models.py.
Tests: AGUIEventType, TaskStatus, TaskSubmission, TaskStore, AGUIEvent.
"""

import asyncio
import json
import pytest

from agent.task_ui_models import (
    AGUIEventType,
    TaskStatus,
    TaskSubmission,
    TaskResponse,
    TaskResult,
    AGUIEvent,
    TaskStore,
)


class TestAGUIEventType:
    """Tests for AGUIEventType enum."""

    def test_all_event_types(self):
        assert AGUIEventType.RUN_STARTED == "RUN_STARTED"
        assert AGUIEventType.TEXT_MESSAGE == "TEXT_MESSAGE"
        assert AGUIEventType.RUN_FINISHED == "RUN_FINISHED"
        assert AGUIEventType.RUN_ERROR == "RUN_ERROR"

    def test_is_string_enum(self):
        assert isinstance(AGUIEventType.RUN_STARTED, str)


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_all_statuses(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"


class TestTaskSubmission:
    """Tests for TaskSubmission model."""

    def test_minimal(self):
        sub = TaskSubmission(prompt="Do something")
        assert sub.prompt == "Do something"
        assert sub.agent == "orchestrator"
        assert sub.dry_run is False

    def test_with_all_fields(self):
        sub = TaskSubmission(
            prompt="Research X",
            agent="research-agent",
            context={"key": "val"},
            dry_run=True,
        )
        assert sub.agent == "research-agent"
        assert sub.context == {"key": "val"}
        assert sub.dry_run is True


class TestAGUIEvent:
    """Tests for AGUIEvent dataclass."""

    def test_creation(self):
        event = AGUIEvent(
            type=AGUIEventType.RUN_STARTED,
            run_id="TASK-001",
        )
        assert event.type == AGUIEventType.RUN_STARTED
        assert event.run_id == "TASK-001"
        assert event.timestamp is not None

    def test_to_sse(self):
        event = AGUIEvent(
            type=AGUIEventType.TEXT_MESSAGE,
            run_id="TASK-001",
            data={"content": "Hello"},
        )
        sse = event.to_sse()
        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")
        payload = json.loads(sse[6:].strip())
        assert payload["type"] == "TEXT_MESSAGE"
        assert payload["runId"] == "TASK-001"
        assert payload["content"] == "Hello"


class TestTaskStore:
    """Tests for TaskStore."""

    def test_create_task(self):
        store = TaskStore()
        sub = TaskSubmission(prompt="Test task")
        task = store.create_task(sub)
        assert task.task_id.startswith("TASK-")
        assert task.status == TaskStatus.PENDING
        assert task.prompt == "Test task"

    def test_get_task(self):
        store = TaskStore()
        sub = TaskSubmission(prompt="Get test")
        created = store.create_task(sub)
        found = store.get_task(created.task_id)
        assert found is not None
        assert found.task_id == created.task_id

    def test_get_nonexistent(self):
        store = TaskStore()
        assert store.get_task("NOPE") is None

    def test_update_task(self):
        store = TaskStore()
        sub = TaskSubmission(prompt="Update test")
        created = store.create_task(sub)
        updated = store.update_task(created.task_id, status=TaskStatus.RUNNING)
        assert updated.status == TaskStatus.RUNNING

    def test_update_nonexistent(self):
        store = TaskStore()
        result = store.update_task("NOPE", status=TaskStatus.RUNNING)
        assert result is None

    def test_list_tasks(self):
        store = TaskStore()
        for i in range(5):
            store.create_task(TaskSubmission(prompt=f"Task {i}"))
        tasks = store.list_tasks()
        assert len(tasks) == 5

    def test_list_tasks_limit(self):
        store = TaskStore()
        for i in range(10):
            store.create_task(TaskSubmission(prompt=f"Task {i}"))
        tasks = store.list_tasks(limit=3)
        assert len(tasks) == 3

    @pytest.mark.asyncio
    async def test_emit_and_get_events(self):
        store = TaskStore()
        sub = TaskSubmission(prompt="Event test")
        task = store.create_task(sub)

        event = AGUIEvent(
            type=AGUIEventType.RUN_FINISHED,
            run_id=task.task_id,
        )
        await store.emit_event(task.task_id, event)

        events = []
        async for e in store.get_events(task.task_id):
            events.append(e)
        assert len(events) == 1
        assert events[0].type == AGUIEventType.RUN_FINISHED
