"""
Robot Framework Library for Task UI Router Tests.

Per: Phase 6.1, RULE-019 (UI/UX Design Standards), DOC-SIZE-01-v1.
Split from tests/test_task_ui.py
"""
from pathlib import Path
from unittest.mock import Mock
from robot.api.deco import keyword


class TaskUIRouterLibrary:
    """Library for Task UI router and integration tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # API Router Tests
    # =========================================================================

    @keyword("Create Task Router")
    def create_task_router(self):
        """create_task_router returns APIRouter."""
        try:
            from agent.task_ui import create_task_router
            from fastapi import APIRouter

            router = create_task_router({})

            return {
                "is_api_router": isinstance(router, APIRouter),
                "prefix_correct": router.prefix == "/tasks"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Router Has Endpoints")
    def router_has_endpoints(self):
        """Router has required endpoints."""
        try:
            from agent.task_ui import create_task_router

            mock_agents = {"orchestrator": Mock()}
            router = create_task_router(mock_agents)

            routes = [r.path for r in router.routes]

            return {
                "has_tasks": "/tasks" in routes,
                "has_task_id": "/tasks/{task_id}" in routes,
                "has_events": "/tasks/{task_id}/events" in routes
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Integration Helper Tests
    # =========================================================================

    @keyword("Integrate Task UI")
    def integrate_task_ui_test(self):
        """integrate_task_ui adds router to app."""
        try:
            from agent.task_ui import integrate_task_ui
            from fastapi import FastAPI

            app = FastAPI()
            agents = {"orchestrator": Mock()}

            integrate_task_ui(app, agents)

            # Check routes were added
            routes = [r.path for r in app.routes]
            has_tasks = "/tasks" in routes or any("/tasks" in str(r) for r in routes)

            return {
                "routes_added": has_tasks
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("CORS Middleware Added")
    def cors_middleware_added(self):
        """CORS middleware is added for UI development."""
        try:
            from agent.task_ui import integrate_task_ui
            from fastapi import FastAPI

            app = FastAPI()
            agents = {"orchestrator": Mock()}

            integrate_task_ui(app, agents)

            return {
                "middleware_added": len(app.user_middleware) > 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Task Response Tests
    # =========================================================================

    @keyword("Task Response Fields")
    def task_response_fields(self):
        """TaskResponse has all required fields."""
        try:
            from agent.task_ui import TaskResponse, TaskStatus

            response = TaskResponse(
                task_id="TASK-12345678",
                status=TaskStatus.PENDING,
                agent="orchestrator",
                created_at="2024-12-24T10:00:00",
                message="Task submitted"
            )

            return {
                "task_id_correct": response.task_id == "TASK-12345678",
                "status_pending": response.status == TaskStatus.PENDING,
                "agent_correct": response.agent == "orchestrator",
                "message_correct": response.message == "Task submitted"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Task Result Tests
    # =========================================================================

    @keyword("Task Result Fields")
    def task_result_fields(self):
        """TaskResult has all required fields."""
        try:
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

            return {
                "task_id_correct": result.task_id == "TASK-12345678",
                "status_completed": result.status == TaskStatus.COMPLETED,
                "response_correct": result.response == "Task completed successfully",
                "duration_correct": result.duration_ms == 1500
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Result Defaults")
    def task_result_defaults(self):
        """TaskResult has correct defaults."""
        try:
            from agent.task_ui import TaskResult, TaskStatus

            result = TaskResult(
                task_id="TASK-12345678",
                status=TaskStatus.PENDING,
                agent="orchestrator",
                prompt="Test",
                created_at="2024-12-24T10:00:00"
            )

            return {
                "response_none": result.response is None,
                "tool_calls_empty": result.tool_calls == [],
                "error_none": result.error is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
