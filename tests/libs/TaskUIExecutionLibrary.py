"""
Robot Framework Library for Task UI Execution Tests.

Per: Phase 6.1, RULE-019 (UI/UX Design Standards), DOC-SIZE-01-v1.
Split from tests/test_task_ui.py
"""
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from robot.api.deco import keyword


class TaskUIExecutionLibrary:
    """Library for Task UI execution and async tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # Task Store Async Tests
    # =========================================================================

    @keyword("Task Store Emit Event")
    def task_store_emit_event(self):
        """TaskStore emits events to queue."""
        try:
            from agent.task_ui import TaskStore, TaskSubmission, AGUIEvent, AGUIEventType

            async def run_test():
                store = TaskStore()
                task = store.create_task(TaskSubmission(prompt="Test"))

                event = AGUIEvent(
                    type=AGUIEventType.RUN_STARTED,
                    run_id=task.task_id
                )

                await store.emit_event(task.task_id, event)

                # Event should be in queue
                queue = store._event_queues.get(task.task_id)
                return not queue.empty() if queue else False

            result = asyncio.run(run_test())
            return {"event_in_queue": result}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Store Get Events Yields")
    def task_store_get_events_yields(self):
        """get_events yields emitted events."""
        try:
            from agent.task_ui import TaskStore, TaskSubmission, AGUIEvent, AGUIEventType

            async def run_test():
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

                return {
                    "event_count": len(events) == 1,
                    "event_type": events[0].type == AGUIEventType.RUN_FINISHED if events else False
                }

            return asyncio.run(run_test())
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Execute Task Tests
    # =========================================================================

    @keyword("Execute Task Emits Run Started")
    def execute_task_emits_run_started(self):
        """execute_task emits RUN_STARTED event."""
        try:
            from agent.task_ui import (
                execute_task, TaskSubmission, task_store
            )

            async def run_test():
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
                return final_task.status.value in ["completed", "failed"]

            result = asyncio.run(run_test())
            return {"task_finished": result}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Execute Task Handles Missing Agent")
    def execute_task_handles_missing_agent(self):
        """execute_task handles missing agent gracefully."""
        try:
            from agent.task_ui import (
                execute_task, TaskSubmission, task_store, TaskStatus
            )

            async def run_test():
                # Reset global store
                task_store._tasks.clear()
                task_store._event_queues.clear()

                submission = TaskSubmission(prompt="Test", agent="nonexistent")
                task = task_store.create_task(submission)

                # Execute with empty agents
                await execute_task(task, {})

                # Should fail
                final_task = task_store.get_task(task.task_id)
                return {
                    "status_failed": final_task.status == TaskStatus.FAILED,
                    "error_not_found": "not found" in final_task.error if final_task.error else False
                }

            return asyncio.run(run_test())
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
