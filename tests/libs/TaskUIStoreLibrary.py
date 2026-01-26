"""
Robot Framework Library for Task UI Store Tests.

Per: Phase 6.1, RULE-019 (UI/UX Design Standards), DOC-SIZE-01-v1.
Split from tests/test_task_ui.py
"""
import time
from pathlib import Path
from robot.api.deco import keyword


class TaskUIStoreLibrary:
    """Library for Task UI store and submission tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # Task Submission Tests
    # =========================================================================

    @keyword("Valid Task Submission")
    def valid_task_submission(self):
        """Valid task submission is accepted."""
        try:
            from agent.task_ui import TaskSubmission

            submission = TaskSubmission(
                prompt="Analyze this code",
                agent="coder"
            )

            return {
                "prompt_correct": submission.prompt == "Analyze this code",
                "agent_correct": submission.agent == "coder",
                "dry_run_false": submission.dry_run is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Submission Defaults")
    def task_submission_defaults(self):
        """Task submission has correct defaults."""
        try:
            from agent.task_ui import TaskSubmission

            submission = TaskSubmission(prompt="Hello")

            return {
                "agent_orchestrator": submission.agent == "orchestrator",
                "context_none": submission.context is None,
                "dry_run_false": submission.dry_run is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Submission With Context")
    def task_submission_with_context(self):
        """Task submission can include context."""
        try:
            from agent.task_ui import TaskSubmission

            submission = TaskSubmission(
                prompt="Review this",
                context={"file": "main.py", "line": 42}
            )

            return {
                "context_file": submission.context["file"] == "main.py",
                "context_line": submission.context["line"] == 42
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Empty Prompt Rejected")
    def empty_prompt_rejected(self):
        """Empty prompt is rejected."""
        try:
            from agent.task_ui import TaskSubmission
            from pydantic import ValidationError

            try:
                TaskSubmission(prompt="")
                return {"raises_error": False}
            except ValidationError:
                return {"raises_error": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Task Store Tests
    # =========================================================================

    @keyword("Task Store Create Task")
    def task_store_create_task(self):
        """TaskStore creates tasks with unique IDs."""
        try:
            from agent.task_ui import TaskStore, TaskSubmission, TaskStatus

            store = TaskStore()
            submission = TaskSubmission(prompt="Test task")
            task = store.create_task(submission)

            return {
                "task_id_prefix": task.task_id.startswith("TASK-"),
                "status_pending": task.status == TaskStatus.PENDING,
                "prompt_correct": task.prompt == "Test task",
                "agent_orchestrator": task.agent == "orchestrator"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Store Unique IDs")
    def task_store_unique_ids(self):
        """Each task gets a unique ID."""
        try:
            from agent.task_ui import TaskStore, TaskSubmission

            store = TaskStore()
            submission = TaskSubmission(prompt="Test task")

            task1 = store.create_task(submission)
            task2 = store.create_task(submission)

            return {
                "ids_different": task1.task_id != task2.task_id
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Store Get Task")
    def task_store_get_task(self):
        """TaskStore retrieves task by ID."""
        try:
            from agent.task_ui import TaskStore, TaskSubmission

            store = TaskStore()
            submission = TaskSubmission(prompt="Test task")
            task = store.create_task(submission)

            retrieved = store.get_task(task.task_id)

            return {
                "task_found": retrieved is not None,
                "id_matches": retrieved.task_id == task.task_id if retrieved else False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Store Get Nonexistent")
    def task_store_get_nonexistent(self):
        """TaskStore returns None for unknown task ID."""
        try:
            from agent.task_ui import TaskStore

            store = TaskStore()
            result = store.get_task("TASK-NONEXISTENT")

            return {
                "returns_none": result is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Store Update Task")
    def task_store_update_task(self):
        """TaskStore updates task fields."""
        try:
            from agent.task_ui import TaskStore, TaskSubmission, TaskStatus

            store = TaskStore()
            submission = TaskSubmission(prompt="Test task")
            task = store.create_task(submission)

            store.update_task(task.task_id, status=TaskStatus.RUNNING)

            updated = store.get_task(task.task_id)
            return {
                "status_updated": updated.status == TaskStatus.RUNNING
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Store List Tasks")
    def task_store_list_tasks(self):
        """TaskStore lists recent tasks."""
        try:
            from agent.task_ui import TaskStore, TaskSubmission

            store = TaskStore()

            for i in range(5):
                store.create_task(TaskSubmission(prompt=f"Task {i}"))

            tasks = store.list_tasks(limit=3)

            return {
                "limit_respected": len(tasks) == 3
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Store List Order")
    def task_store_list_order(self):
        """Tasks are listed in reverse chronological order."""
        try:
            from agent.task_ui import TaskStore, TaskSubmission

            store = TaskStore()

            store.create_task(TaskSubmission(prompt="First"))
            time.sleep(0.01)  # Ensure different timestamps
            store.create_task(TaskSubmission(prompt="Second"))
            time.sleep(0.01)
            store.create_task(TaskSubmission(prompt="Third"))

            tasks = store.list_tasks()

            # Most recent first
            return {
                "first_is_third": tasks[0].prompt == "Third",
                "last_is_first": tasks[2].prompt == "First"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
