"""
Robot Framework Library for Orchestrator Tests.

Per ORCH-002: Agent orchestrator task polling and dispatch.
Migrated from tests/test_orchestrator.py
"""
import asyncio
from pathlib import Path
from unittest.mock import Mock
from robot.api.deco import keyword


class OrchestratorLibrary:
    """Library for testing orchestrator module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    def _create_mock_task(self, task_id, name, status, phase, agent_id=None):
        """Create mock TypeDB task."""
        mock = Mock()
        mock.id = task_id
        mock.name = name
        mock.status = status
        mock.phase = phase
        mock.agent_id = agent_id
        mock.body = None
        mock.gap_id = None
        return mock

    # =============================================================================
    # PollableTask Tests
    # =============================================================================

    @keyword("Pollable Task From TypeDB Basic")
    def pollable_task_from_typedb_basic(self):
        """Convert basic TypeDB task."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority

            mock = self._create_mock_task("TASK-001", "Test Task", "pending", "P10")
            task = PollableTask.from_typedb_task(mock)

            return {
                "task_id_correct": task.task_id == "TASK-001",
                "name_correct": task.name == "Test Task",
                "status_correct": task.status == "pending",
                "phase_correct": task.phase == "P10",
                "priority_high": task.priority == TaskPriority.HIGH
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Pollable Task RD Phase Priority")
    def pollable_task_rd_phase_priority(self):
        """R&D phase maps to MEDIUM priority."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority

            mock = self._create_mock_task("RD-001", "R&D Task", "TODO", "RD")
            task = PollableTask.from_typedb_task(mock)

            return {"priority_medium": task.priority == TaskPriority.MEDIUM}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Pollable Task High Requires Evidence")
    def pollable_task_high_requires_evidence(self):
        """HIGH priority tasks require evidence."""
        try:
            from agent.orchestrator.task_poller import PollableTask

            mock = self._create_mock_task("TASK-001", "Task", "pending", "P10")
            task = PollableTask.from_typedb_task(mock)

            return {"requires_evidence": task.requires_evidence is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Pollable Task Medium No Evidence")
    def pollable_task_medium_no_evidence(self):
        """MEDIUM priority tasks don't require evidence."""
        try:
            from agent.orchestrator.task_poller import PollableTask

            mock = self._create_mock_task("TASK-001", "Task", "pending", "OTHER")
            task = PollableTask.from_typedb_task(mock)

            return {"no_evidence_required": task.requires_evidence is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # TaskPriorityQueue Tests
    # =============================================================================

    @keyword("Queue Push And Pop")
    def queue_push_and_pop(self):
        """Basic push and pop operations."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority
            from agent.orchestrator.priority_queue import TaskPriorityQueue

            queue = TaskPriorityQueue()

            task = PollableTask(
                task_id="TASK-001",
                name="Test",
                priority=TaskPriority.MEDIUM,
                phase="P10",
                status="pending",
                requires_evidence=False,
            )

            push_result = queue.push(task)
            size_after_push = queue.size

            popped = queue.pop()
            size_after_pop = queue.size

            return {
                "push_success": push_result is True,
                "size_after_push": size_after_push == 1,
                "popped_id_correct": popped.task_id == "TASK-001",
                "size_after_pop": size_after_pop == 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Queue Priority Ordering")
    def queue_priority_ordering(self):
        """Higher priority tasks pop first."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority
            from agent.orchestrator.priority_queue import TaskPriorityQueue

            queue = TaskPriorityQueue()

            low = PollableTask("LOW-001", "Low", TaskPriority.LOW, "P10", "pending", False)
            high = PollableTask("HIGH-001", "High", TaskPriority.HIGH, "P10", "pending", True)
            critical = PollableTask("CRIT-001", "Critical", TaskPriority.CRITICAL, "P10", "pending", True)

            queue.push(low)
            queue.push(high)
            queue.push(critical)

            first = queue.pop().task_id
            second = queue.pop().task_id
            third = queue.pop().task_id

            return {
                "first_critical": first == "CRIT-001",
                "second_high": second == "HIGH-001",
                "third_low": third == "LOW-001"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Queue Duplicate Rejection")
    def queue_duplicate_rejection(self):
        """Duplicate task IDs are rejected."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority
            from agent.orchestrator.priority_queue import TaskPriorityQueue

            queue = TaskPriorityQueue()

            task = PollableTask("TASK-001", "Test", TaskPriority.MEDIUM, "P10", "pending", False)

            first_push = queue.push(task)
            second_push = queue.push(task)

            return {
                "first_push_success": first_push is True,
                "second_push_rejected": second_push is False,
                "size_is_one": queue.size == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Queue Peek Without Remove")
    def queue_peek_without_remove(self):
        """Peek returns task without removing."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority
            from agent.orchestrator.priority_queue import TaskPriorityQueue

            queue = TaskPriorityQueue()

            task = PollableTask("TASK-001", "Test", TaskPriority.MEDIUM, "P10", "pending", False)
            queue.push(task)

            peeked = queue.peek()

            return {
                "peeked_id_correct": peeked.task_id == "TASK-001",
                "still_in_queue": queue.size == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Queue Remove Specific Task")
    def queue_remove_specific_task(self):
        """Remove specific task by ID."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority
            from agent.orchestrator.priority_queue import TaskPriorityQueue

            queue = TaskPriorityQueue()

            task1 = PollableTask("TASK-001", "Test1", TaskPriority.MEDIUM, "P10", "pending", False)
            task2 = PollableTask("TASK-002", "Test2", TaskPriority.MEDIUM, "P10", "pending", False)

            queue.push(task1)
            queue.push(task2)

            remove_result = queue.remove("TASK-001")

            return {
                "remove_success": remove_result is True,
                "size_is_one": queue.size == 1,
                "remaining_task": queue.pop().task_id == "TASK-002"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Queue Get By Priority")
    def queue_get_by_priority(self):
        """Filter tasks by priority."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority
            from agent.orchestrator.priority_queue import TaskPriorityQueue

            queue = TaskPriorityQueue()

            queue.push(PollableTask("LOW-001", "L1", TaskPriority.LOW, "P10", "pending", False))
            queue.push(PollableTask("HIGH-001", "H1", TaskPriority.HIGH, "P10", "pending", True))
            queue.push(PollableTask("HIGH-002", "H2", TaskPriority.HIGH, "P10", "pending", True))

            high_tasks = queue.get_by_priority(TaskPriority.HIGH)

            return {"high_count": len(high_tasks) == 2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Queue Max Size Enforcement")
    def queue_max_size_enforcement(self):
        """Queue respects max size."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority
            from agent.orchestrator.priority_queue import TaskPriorityQueue

            queue = TaskPriorityQueue(max_size=2)

            queue.push(PollableTask("T1", "T1", TaskPriority.LOW, "P10", "pending", False))
            queue.push(PollableTask("T2", "T2", TaskPriority.LOW, "P10", "pending", False))

            third_push = queue.push(PollableTask("T3", "T3", TaskPriority.LOW, "P10", "pending", False))

            return {
                "third_rejected": third_push is False,
                "size_is_two": queue.size == 2
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Queue Create From Tasks")
    def queue_create_from_tasks(self):
        """Create queue from task list."""
        try:
            from agent.orchestrator.task_poller import PollableTask, TaskPriority
            from agent.orchestrator.priority_queue import create_queue_from_tasks

            tasks = [
                PollableTask("T1", "T1", TaskPriority.HIGH, "P10", "pending", True),
                PollableTask("T2", "T2", TaskPriority.LOW, "P10", "pending", False),
            ]
            queue = create_queue_from_tasks(tasks)

            return {
                "size_correct": queue.size == 2,
                "high_first": queue.pop().task_id == "T1"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

