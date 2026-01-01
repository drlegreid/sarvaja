"""
Task Priority Queue (ORCH-002).

Priority-based task queue for agent dispatch.

Per RULE-011: Multi-Agent Governance (trust-weighted dispatch)
Per RULE-014: Autonomous Task Sequencing (priority ordering)
"""

import heapq
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .task_poller import PollableTask, TaskPriority


@dataclass(order=True)
class QueuedTask:
    """
    Task entry in priority queue.

    Ordering: priority (asc) → queued_at (asc)
    Lower priority value = higher urgency (CRITICAL=0, LOW=3)
    """
    priority: int
    queued_at: datetime = field(compare=True)
    task: PollableTask = field(compare=False)

    @classmethod
    def from_pollable(cls, task: PollableTask) -> "QueuedTask":
        """Create queue entry from PollableTask."""
        return cls(
            priority=task.priority.value,
            queued_at=datetime.now(),
            task=task,
        )


class TaskPriorityQueue:
    """
    Priority queue for task dispatch.

    Features:
    - Priority ordering (CRITICAL → HIGH → MEDIUM → LOW)
    - FIFO within same priority
    - Duplicate detection
    - Trust-based filtering

    Usage:
        queue = TaskPriorityQueue()

        # Add tasks
        queue.push(task1)
        queue.push(task2)

        # Get highest priority task
        task = queue.pop()

        # Peek without removing
        next_task = queue.peek()

        # Filter by minimum trust
        queue.set_min_trust(0.7)
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize queue.

        Args:
            max_size: Maximum queue size (default 100)
        """
        self._heap: List[QueuedTask] = []
        self._task_ids: set = set()
        self._max_size = max_size
        self._push_count = 0
        self._pop_count = 0
        self._min_trust: float = 0.0

    @property
    def size(self) -> int:
        """Current queue size."""
        return len(self._heap)

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._heap) == 0

    @property
    def is_full(self) -> bool:
        """Check if queue is at max capacity."""
        return len(self._heap) >= self._max_size

    @property
    def stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        priority_counts = {p.name: 0 for p in TaskPriority}
        for entry in self._heap:
            priority = TaskPriority(entry.priority)
            priority_counts[priority.name] += 1

        return {
            "size": self.size,
            "max_size": self._max_size,
            "push_count": self._push_count,
            "pop_count": self._pop_count,
            "min_trust": self._min_trust,
            "priority_distribution": priority_counts,
        }

    def set_min_trust(self, trust: float) -> None:
        """
        Set minimum trust level for task dispatch.

        Tasks requiring higher trust will be skipped.

        Args:
            trust: Minimum trust score (0.0 to 1.0)
        """
        self._min_trust = max(0.0, min(1.0, trust))

    def push(self, task: PollableTask) -> bool:
        """
        Add task to queue.

        Args:
            task: Task to queue

        Returns:
            True if added, False if duplicate or full
        """
        if task.task_id in self._task_ids:
            return False  # Duplicate

        if self.is_full:
            # If full, only add if higher priority than lowest
            if self._heap and task.priority.value >= self._heap[-1].priority:
                return False
            # Remove lowest priority to make room
            self._remove_lowest()

        entry = QueuedTask.from_pollable(task)
        heapq.heappush(self._heap, entry)
        self._task_ids.add(task.task_id)
        self._push_count += 1
        return True

    def push_many(self, tasks: List[PollableTask]) -> int:
        """
        Add multiple tasks to queue.

        Args:
            tasks: Tasks to queue

        Returns:
            Count of tasks added
        """
        added = 0
        for task in tasks:
            if self.push(task):
                added += 1
        return added

    def pop(self) -> Optional[PollableTask]:
        """
        Remove and return highest priority task.

        Returns:
            Highest priority task, or None if empty
        """
        while self._heap:
            entry = heapq.heappop(self._heap)
            self._task_ids.discard(entry.task.task_id)
            self._pop_count += 1
            return entry.task
        return None

    def peek(self) -> Optional[PollableTask]:
        """
        Return highest priority task without removing.

        Returns:
            Highest priority task, or None if empty
        """
        if self._heap:
            return self._heap[0].task
        return None

    def remove(self, task_id: str) -> bool:
        """
        Remove a specific task from queue.

        Args:
            task_id: Task ID to remove

        Returns:
            True if removed, False if not found
        """
        if task_id not in self._task_ids:
            return False

        # Filter out the task and rebuild heap
        self._heap = [e for e in self._heap if e.task.task_id != task_id]
        heapq.heapify(self._heap)
        self._task_ids.discard(task_id)
        return True

    def clear(self) -> int:
        """
        Clear all tasks from queue.

        Returns:
            Count of tasks cleared
        """
        count = len(self._heap)
        self._heap.clear()
        self._task_ids.clear()
        return count

    def get_by_priority(self, priority: TaskPriority) -> List[PollableTask]:
        """
        Get all tasks of a specific priority.

        Args:
            priority: Priority level to filter

        Returns:
            List of tasks with matching priority
        """
        return [
            e.task for e in self._heap
            if e.priority == priority.value
        ]

    def get_critical_tasks(self) -> List[PollableTask]:
        """Get all CRITICAL priority tasks."""
        return self.get_by_priority(TaskPriority.CRITICAL)

    def _remove_lowest(self) -> Optional[PollableTask]:
        """Remove lowest priority (highest value) task."""
        if not self._heap:
            return None

        # Find entry with highest priority value (lowest urgency)
        max_idx = 0
        max_priority = self._heap[0].priority
        for i, entry in enumerate(self._heap):
            if entry.priority > max_priority:
                max_priority = entry.priority
                max_idx = i

        removed = self._heap.pop(max_idx)
        heapq.heapify(self._heap)
        self._task_ids.discard(removed.task.task_id)
        return removed.task


# =============================================================================
# Convenience Functions
# =============================================================================

def create_queue_from_tasks(tasks: List[PollableTask]) -> TaskPriorityQueue:
    """Create and populate queue from task list."""
    queue = TaskPriorityQueue()
    queue.push_many(tasks)
    return queue
