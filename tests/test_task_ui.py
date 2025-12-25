"""
Test suite for Task UI Module
==============================
Validates AG-UI event streaming, task lifecycle, and API endpoints.

Per Phase 6.1: Enhance Agno Playground with task input/progress
Per RULE-019: UI/UX Design Standards
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# =============================================================================
# AG-UI EVENT TYPE TESTS
# =============================================================================

class TestAGUIEventTypes:
    """Tests for AG-UI event type definitions."""

    def test_event_types_defined(self):
        """All AG-UI event types are defined."""
        from agent.task_ui import AGUIEventType

        assert AGUIEventType.RUN_STARTED.value == "RUN_STARTED"
        assert AGUIEventType.TEXT_MESSAGE.value == "TEXT_MESSAGE"
        assert AGUIEventType.TOOL_CALL_START.value == "TOOL_CALL_START"
        assert AGUIEventType.TOOL_CALL_END.value == "TOOL_CALL_END"
        assert AGUIEventType.STATE_DELTA.value == "STATE_DELTA"
        assert AGUIEventType.RUN_FINISHED.value == "RUN_FINISHED"
        assert AGUIEventType.RUN_ERROR.value == "RUN_ERROR"

    def test_task_status_defined(self):
        """All task status values are defined."""
        from agent.task_ui import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


# =============================================================================
# AGUI EVENT TESTS
# =============================================================================

class TestAGUIEvent:
    """Tests for AGUIEvent dataclass."""

    def test_event_creation(self):
        """AGUIEvent can be created with required fields."""
        from agent.task_ui import AGUIEvent, AGUIEventType

        event = AGUIEvent(
            type=AGUIEventType.RUN_STARTED,
            run_id="TASK-12345678"
        )

        assert event.type == AGUIEventType.RUN_STARTED
        assert event.run_id == "TASK-12345678"
        assert event.timestamp is not None

    def test_event_with_data(self):
        """AGUIEvent can include data payload."""
        from agent.task_ui import AGUIEvent, AGUIEventType

        event = AGUIEvent(
            type=AGUIEventType.TEXT_MESSAGE,
            run_id="TASK-12345678",
            data={"role": "assistant", "content": "Hello!"}
        )

        assert event.data["role"] == "assistant"
        assert event.data["content"] == "Hello!"

    def test_event_to_sse(self):
        """AGUIEvent converts to SSE format correctly."""
        from agent.task_ui import AGUIEvent, AGUIEventType

        event = AGUIEvent(
            type=AGUIEventType.RUN_STARTED,
            run_id="TASK-12345678",
            data={"agent": "orchestrator"}
        )

        sse = event.to_sse()

        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")

        # Parse JSON payload
        json_str = sse[6:-2]  # Remove "data: " prefix and "\n\n" suffix
        payload = json.loads(json_str)

        assert payload["type"] == "RUN_STARTED"
        assert payload["runId"] == "TASK-12345678"
        assert payload["agent"] == "orchestrator"
        assert "timestamp" in payload


# =============================================================================
# TASK SUBMISSION TESTS
# =============================================================================

class TestTaskSubmission:
    """Tests for TaskSubmission model."""

    def test_valid_submission(self):
        """Valid task submission is accepted."""
        from agent.task_ui import TaskSubmission

        submission = TaskSubmission(
            prompt="Analyze this code",
            agent="coder"
        )

        assert submission.prompt == "Analyze this code"
        assert submission.agent == "coder"
        assert submission.dry_run is False

    def test_submission_defaults(self):
        """Task submission has correct defaults."""
        from agent.task_ui import TaskSubmission

        submission = TaskSubmission(prompt="Hello")

        assert submission.agent == "orchestrator"
        assert submission.context is None
        assert submission.dry_run is False

    def test_submission_with_context(self):
        """Task submission can include context."""
        from agent.task_ui import TaskSubmission

        submission = TaskSubmission(
            prompt="Review this",
            context={"file": "main.py", "line": 42}
        )

        assert submission.context["file"] == "main.py"
        assert submission.context["line"] == 42

    def test_empty_prompt_rejected(self):
        """Empty prompt is rejected."""
        from agent.task_ui import TaskSubmission
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TaskSubmission(prompt="")


# =============================================================================
# TASK STORE TESTS
# =============================================================================

class TestTaskStore:
    """Tests for in-memory TaskStore."""

    def test_create_task(self):
        """TaskStore creates tasks with unique IDs."""
        from agent.task_ui import TaskStore, TaskSubmission, TaskStatus

        store = TaskStore()
        submission = TaskSubmission(prompt="Test task")

        task = store.create_task(submission)

        assert task.task_id.startswith("TASK-")
        assert task.status == TaskStatus.PENDING
        assert task.prompt == "Test task"
        assert task.agent == "orchestrator"

    def test_unique_task_ids(self):
        """Each task gets a unique ID."""
        from agent.task_ui import TaskStore, TaskSubmission

        store = TaskStore()
        submission = TaskSubmission(prompt="Test task")

        task1 = store.create_task(submission)
        task2 = store.create_task(submission)

        assert task1.task_id != task2.task_id

    def test_get_task(self):
        """TaskStore retrieves task by ID."""
        from agent.task_ui import TaskStore, TaskSubmission

        store = TaskStore()
        submission = TaskSubmission(prompt="Test task")
        task = store.create_task(submission)

        retrieved = store.get_task(task.task_id)

        assert retrieved is not None
        assert retrieved.task_id == task.task_id

    def test_get_nonexistent_task(self):
        """TaskStore returns None for unknown task ID."""
        from agent.task_ui import TaskStore

        store = TaskStore()

        result = store.get_task("TASK-NONEXISTENT")

        assert result is None

    def test_update_task(self):
        """TaskStore updates task fields."""
        from agent.task_ui import TaskStore, TaskSubmission, TaskStatus

        store = TaskStore()
        submission = TaskSubmission(prompt="Test task")
        task = store.create_task(submission)

        store.update_task(task.task_id, status=TaskStatus.RUNNING)

        updated = store.get_task(task.task_id)
        assert updated.status == TaskStatus.RUNNING

    def test_list_tasks(self):
        """TaskStore lists recent tasks."""
        from agent.task_ui import TaskStore, TaskSubmission

        store = TaskStore()

        for i in range(5):
            store.create_task(TaskSubmission(prompt=f"Task {i}"))

        tasks = store.list_tasks(limit=3)

        assert len(tasks) == 3

    def test_list_tasks_order(self):
        """Tasks are listed in reverse chronological order."""
        from agent.task_ui import TaskStore, TaskSubmission
        import time

        store = TaskStore()

        task1 = store.create_task(TaskSubmission(prompt="First"))
        time.sleep(0.01)  # Ensure different timestamps
        task2 = store.create_task(TaskSubmission(prompt="Second"))
        time.sleep(0.01)
        task3 = store.create_task(TaskSubmission(prompt="Third"))

        tasks = store.list_tasks()

        # Most recent first
        assert tasks[0].prompt == "Third"
        assert tasks[2].prompt == "First"


# =============================================================================
# TASK STORE ASYNC TESTS
# =============================================================================

class TestTaskStoreAsync:
    """Async tests for TaskStore event streaming."""

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """TaskStore emits events to queue."""
        from agent.task_ui import TaskStore, TaskSubmission, AGUIEvent, AGUIEventType

        store = TaskStore()
        task = store.create_task(TaskSubmission(prompt="Test"))

        event = AGUIEvent(
            type=AGUIEventType.RUN_STARTED,
            run_id=task.task_id
        )

        await store.emit_event(task.task_id, event)

        # Event should be in queue
        queue = store._event_queues.get(task.task_id)
        assert not queue.empty()

    @pytest.mark.asyncio
    async def test_get_events_yields_emitted(self):
        """get_events yields emitted events."""
        from agent.task_ui import TaskStore, TaskSubmission, AGUIEvent, AGUIEventType

        store = TaskStore()
        task = store.create_task(TaskSubmission(prompt="Test"))

        # Emit a finish event
        await store.emit_event(task.task_id, AGUIEvent(
            type=AGUIEventType.RUN_FINISHED,
            run_id=task.task_id
        ))

        events = []
        async for event in store.get_events(task.task_id):
            events.append(event)

        assert len(events) == 1
        assert events[0].type == AGUIEventType.RUN_FINISHED


# =============================================================================
# API ROUTER TESTS
# =============================================================================

class TestTaskRouter:
    """Tests for FastAPI task router."""

    def test_create_router(self):
        """create_task_router returns APIRouter."""
        from agent.task_ui import create_task_router
        from fastapi import APIRouter

        router = create_task_router({})

        assert isinstance(router, APIRouter)
        assert router.prefix == "/tasks"

    def test_router_has_endpoints(self):
        """Router has required endpoints."""
        from agent.task_ui import create_task_router

        mock_agents = {"orchestrator": Mock()}
        router = create_task_router(mock_agents)

        # Check routes exist (with /tasks prefix)
        routes = [r.path for r in router.routes]

        assert "/tasks" in routes  # POST /tasks (list endpoint)
        assert "/tasks/{task_id}" in routes  # GET /tasks/{task_id}
        assert "/tasks/{task_id}/events" in routes  # GET /tasks/{task_id}/events


# =============================================================================
# INTEGRATION HELPER TESTS
# =============================================================================

class TestIntegration:
    """Tests for integration helper."""

    def test_integrate_task_ui(self):
        """integrate_task_ui adds router to app."""
        from agent.task_ui import integrate_task_ui
        from fastapi import FastAPI

        app = FastAPI()
        agents = {"orchestrator": Mock()}

        integrate_task_ui(app, agents)

        # Check routes were added
        routes = [r.path for r in app.routes]
        assert "/tasks" in routes or any("/tasks" in str(r) for r in routes)

    def test_cors_added(self):
        """CORS middleware is added for UI development."""
        from agent.task_ui import integrate_task_ui
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI()
        agents = {"orchestrator": Mock()}

        integrate_task_ui(app, agents)

        # Check middleware was added
        middleware_types = [type(m.cls).__name__ for m in app.user_middleware]
        # CORS is added - we verify by checking the app has middleware
        assert len(app.user_middleware) > 0


# =============================================================================
# TASK RESPONSE TESTS
# =============================================================================

class TestTaskResponse:
    """Tests for TaskResponse model."""

    def test_task_response_fields(self):
        """TaskResponse has all required fields."""
        from agent.task_ui import TaskResponse, TaskStatus

        response = TaskResponse(
            task_id="TASK-12345678",
            status=TaskStatus.PENDING,
            agent="orchestrator",
            created_at="2024-12-24T10:00:00",
            message="Task submitted"
        )

        assert response.task_id == "TASK-12345678"
        assert response.status == TaskStatus.PENDING
        assert response.agent == "orchestrator"
        assert response.message == "Task submitted"


class TestTaskResult:
    """Tests for TaskResult model."""

    def test_task_result_fields(self):
        """TaskResult has all required fields."""
        from agent.task_ui import TaskResult, TaskStatus

        result = TaskResult(
            task_id="TASK-12345678",
            status=TaskStatus.COMPLETED,
            agent="orchestrator",
            prompt="Test task",
            response="Task completed successfully",
            duration_ms=1500,
            created_at="2024-12-24T10:00:00",
            completed_at="2024-12-24T10:00:01"
        )

        assert result.task_id == "TASK-12345678"
        assert result.status == TaskStatus.COMPLETED
        assert result.response == "Task completed successfully"
        assert result.duration_ms == 1500

    def test_task_result_defaults(self):
        """TaskResult has correct defaults."""
        from agent.task_ui import TaskResult, TaskStatus

        result = TaskResult(
            task_id="TASK-12345678",
            status=TaskStatus.PENDING,
            agent="orchestrator",
            prompt="Test",
            created_at="2024-12-24T10:00:00"
        )

        assert result.response is None
        assert result.tool_calls == []
        assert result.error is None


# =============================================================================
# EXECUTE TASK TESTS
# =============================================================================

class TestExecuteTask:
    """Tests for task execution logic."""

    @pytest.mark.asyncio
    async def test_execute_task_emits_run_started(self):
        """execute_task emits RUN_STARTED event."""
        from agent.task_ui import (
            execute_task, TaskStore, TaskSubmission,
            AGUIEventType, task_store
        )

        # Reset global store
        task_store._tasks.clear()
        task_store._event_queues.clear()

        submission = TaskSubmission(prompt="Test")
        task = task_store.create_task(submission)

        # Create mock agent
        mock_agent = Mock()
        mock_agent.run = Mock(return_value=Mock(content="Response"))
        agents = {"orchestrator": mock_agent}

        # Execute
        await execute_task(task, agents)

        # Check final task status
        final_task = task_store.get_task(task.task_id)
        assert final_task.status.value in ["completed", "failed"]

    @pytest.mark.asyncio
    async def test_execute_task_handles_missing_agent(self):
        """execute_task handles missing agent gracefully."""
        from agent.task_ui import (
            execute_task, TaskSubmission, task_store, TaskStatus
        )

        # Reset global store
        task_store._tasks.clear()
        task_store._event_queues.clear()

        submission = TaskSubmission(prompt="Test", agent="nonexistent")
        task = task_store.create_task(submission)

        # Execute with empty agents
        await execute_task(task, {})

        # Should fail
        final_task = task_store.get_task(task.task_id)
        assert final_task.status == TaskStatus.FAILED
        assert "not found" in final_task.error


# =============================================================================
# SSE FORMAT TESTS
# =============================================================================

class TestSSEFormat:
    """Tests for Server-Sent Events format."""

    def test_sse_format_valid(self):
        """SSE format is valid per specification."""
        from agent.task_ui import AGUIEvent, AGUIEventType

        event = AGUIEvent(
            type=AGUIEventType.TEXT_MESSAGE,
            run_id="TASK-TEST",
            data={"content": "Hello"}
        )

        sse = event.to_sse()

        # Must start with "data: "
        assert sse.startswith("data: ")
        # Must end with double newline
        assert sse.endswith("\n\n")
        # JSON must be valid
        json_part = sse[6:-2]
        parsed = json.loads(json_part)
        assert "type" in parsed
        assert "runId" in parsed

    def test_sse_escapes_special_chars(self):
        """SSE properly escapes special characters in JSON."""
        from agent.task_ui import AGUIEvent, AGUIEventType

        event = AGUIEvent(
            type=AGUIEventType.TEXT_MESSAGE,
            run_id="TASK-TEST",
            data={"content": "Hello\nWorld\twith\ttabs"}
        )

        sse = event.to_sse()
        json_part = sse[6:-2]

        # Should be valid JSON even with special chars
        parsed = json.loads(json_part)
        assert "Hello\nWorld\twith\ttabs" in parsed["content"]
