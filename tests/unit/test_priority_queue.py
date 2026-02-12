"""
Unit tests for Task Priority Queue.

Per DOC-SIZE-01-v1: Tests for agent/orchestrator/priority_queue.py module.
Tests: QueuedTask, TaskPriorityQueue (push, pop, peek, remove, clear,
       get_by_priority, stats, push_many, capacity), create_queue_from_tasks.
"""

from unittest.mock import MagicMock

import pytest

from agent.orchestrator.task_poller import PollableTask, TaskPriority


def _make_task(task_id: str, priority: TaskPriority = TaskPriority.MEDIUM) -> PollableTask:
    return PollableTask(
        task_id=task_id,
        name=f"Task {task_id}",
        phase="RD",
        status="pending",
        priority=priority,
        requires_evidence=False,
    )


# ── QueuedTask ─────────────────────────────────────────────────


class TestQueuedTask:
    def test_from_pollable(self):
        from agent.orchestrator.priority_queue import QueuedTask
        task = _make_task("T-1", TaskPriority.HIGH)
        entry = QueuedTask.from_pollable(task)
        assert entry.priority == TaskPriority.HIGH.value
        assert entry.task.task_id == "T-1"
        assert entry.queued_at is not None

    def test_ordering(self):
        from agent.orchestrator.priority_queue import QueuedTask
        t_crit = QueuedTask.from_pollable(_make_task("T-C", TaskPriority.CRITICAL))
        t_low = QueuedTask.from_pollable(_make_task("T-L", TaskPriority.LOW))
        assert t_crit < t_low


# ── TaskPriorityQueue init / properties ────────────────────────


class TestQueueInit:
    def test_defaults(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        assert q.size == 0
        assert q.is_empty is True
        assert q.is_full is False
        assert q._max_size == 100

    def test_custom_max_size(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue(max_size=5)
        assert q._max_size == 5

    def test_stats(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        s = q.stats
        assert s["size"] == 0
        assert s["push_count"] == 0
        assert s["pop_count"] == 0
        assert "CRITICAL" in s["priority_distribution"]


# ── push / pop / peek ──────────────────────────────────────────


class TestPushPopPeek:
    def test_push_and_pop(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        assert q.push(_make_task("T-1")) is True
        assert q.size == 1
        task = q.pop()
        assert task.task_id == "T-1"
        assert q.is_empty is True

    def test_priority_ordering(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-LOW", TaskPriority.LOW))
        q.push(_make_task("T-CRIT", TaskPriority.CRITICAL))
        q.push(_make_task("T-HIGH", TaskPriority.HIGH))
        first = q.pop()
        assert first.task_id == "T-CRIT"
        second = q.pop()
        assert second.task_id == "T-HIGH"

    def test_peek_does_not_remove(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-1"))
        peeked = q.peek()
        assert peeked.task_id == "T-1"
        assert q.size == 1

    def test_pop_empty(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        assert q.pop() is None

    def test_peek_empty(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        assert q.peek() is None

    def test_duplicate_rejected(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        assert q.push(_make_task("T-1")) is True
        assert q.push(_make_task("T-1")) is False
        assert q.size == 1

    def test_push_increments_stats(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-1"))
        q.push(_make_task("T-2"))
        assert q.stats["push_count"] == 2

    def test_pop_increments_stats(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-1"))
        q.pop()
        assert q.stats["pop_count"] == 1


# ── capacity ───────────────────────────────────────────────────


class TestCapacity:
    def test_full_rejects_low_priority(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue(max_size=2)
        q.push(_make_task("T-1", TaskPriority.HIGH))
        q.push(_make_task("T-2", TaskPriority.HIGH))
        assert q.is_full is True
        # LOW can't displace HIGH
        assert q.push(_make_task("T-3", TaskPriority.LOW)) is False

    def test_full_accepts_higher_priority(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue(max_size=2)
        q.push(_make_task("T-LOW", TaskPriority.LOW))
        q.push(_make_task("T-MED", TaskPriority.MEDIUM))
        assert q.is_full is True
        # CRITICAL displaces lowest
        result = q.push(_make_task("T-CRIT", TaskPriority.CRITICAL))
        assert result is True
        assert q.size == 2


# ── remove / clear ─────────────────────────────────────────────


class TestRemoveClear:
    def test_remove_existing(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-1"))
        q.push(_make_task("T-2"))
        assert q.remove("T-1") is True
        assert q.size == 1

    def test_remove_nonexistent(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        assert q.remove("T-MISS") is False

    def test_clear(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-1"))
        q.push(_make_task("T-2"))
        count = q.clear()
        assert count == 2
        assert q.is_empty is True


# ── get_by_priority / get_critical_tasks ───────────────────────


class TestFilterByPriority:
    def test_get_by_priority(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-H1", TaskPriority.HIGH))
        q.push(_make_task("T-L1", TaskPriority.LOW))
        q.push(_make_task("T-H2", TaskPriority.HIGH))
        high_tasks = q.get_by_priority(TaskPriority.HIGH)
        assert len(high_tasks) == 2

    def test_get_critical_tasks(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-C1", TaskPriority.CRITICAL))
        q.push(_make_task("T-M1", TaskPriority.MEDIUM))
        crit = q.get_critical_tasks()
        assert len(crit) == 1
        assert crit[0].task_id == "T-C1"


# ── push_many ──────────────────────────────────────────────────


class TestPushMany:
    def test_push_many(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        tasks = [_make_task(f"T-{i}") for i in range(5)]
        added = q.push_many(tasks)
        assert added == 5
        assert q.size == 5

    def test_push_many_with_duplicates(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        tasks = [_make_task("T-1"), _make_task("T-1"), _make_task("T-2")]
        added = q.push_many(tasks)
        assert added == 2


# ── set_min_trust ──────────────────────────────────────────────


class TestSetMinTrust:
    def test_clamps_trust(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.set_min_trust(1.5)
        assert q._min_trust == 1.0
        q.set_min_trust(-0.5)
        assert q._min_trust == 0.0
        q.set_min_trust(0.7)
        assert q._min_trust == 0.7


# ── create_queue_from_tasks ────────────────────────────────────


class TestCreateQueueFromTasks:
    def test_factory(self):
        from agent.orchestrator.priority_queue import create_queue_from_tasks
        tasks = [_make_task(f"T-{i}") for i in range(3)]
        q = create_queue_from_tasks(tasks)
        assert q.size == 3


# ── _remove_lowest ─────────────────────────────────────────────


class TestRemoveLowest:
    def test_removes_lowest_priority(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        q.push(_make_task("T-H", TaskPriority.HIGH))
        q.push(_make_task("T-L", TaskPriority.LOW))
        removed = q._remove_lowest()
        assert removed.task_id == "T-L"
        assert q.size == 1

    def test_empty_returns_none(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        q = TaskPriorityQueue()
        assert q._remove_lowest() is None
