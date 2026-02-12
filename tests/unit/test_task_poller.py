"""
Unit tests for TypeDB Task Poller.

Per DOC-SIZE-01-v1: Tests for agent/orchestrator/task_poller.py module.
Tests: TaskPriority, PollableTask, TypeDBTaskPoller (poll, claim, release,
       complete, start/stop polling, callbacks, stats).
"""

from unittest.mock import MagicMock, AsyncMock, patch

import pytest

_P = "agent.orchestrator.task_poller"


# ── TaskPriority ─────────────────────────────────────────────────


class TestTaskPriority:
    def test_ordering(self):
        from agent.orchestrator.task_poller import TaskPriority
        assert TaskPriority.CRITICAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.MEDIUM.value
        assert TaskPriority.MEDIUM.value < TaskPriority.LOW.value


# ── PollableTask ─────────────────────────────────────────────────


class TestPollableTask:
    def test_from_typedb_task_basic(self):
        from agent.orchestrator.task_poller import PollableTask, TaskPriority
        task = MagicMock()
        task.id = "T-1"
        task.name = "Test task"
        task.phase = "RD-001"
        task.status = "pending"
        del task.agent_id  # hasattr will be False
        del task.body
        del task.gap_id
        result = PollableTask.from_typedb_task(task)
        assert result.task_id == "T-1"
        assert result.priority == TaskPriority.MEDIUM

    def test_from_typedb_task_high_priority_phase(self):
        from agent.orchestrator.task_poller import PollableTask, TaskPriority
        task = MagicMock()
        task.id = "T-2"
        task.name = "High task"
        task.phase = "P10.1"
        task.status = "pending"
        result = PollableTask.from_typedb_task(task)
        assert result.priority == TaskPriority.HIGH
        assert result.requires_evidence is True

    def test_from_typedb_task_p11_phase(self):
        from agent.orchestrator.task_poller import PollableTask, TaskPriority
        task = MagicMock()
        task.id = "T-3"
        task.name = "P11 task"
        task.phase = "P11.2"
        task.status = "pending"
        result = PollableTask.from_typedb_task(task)
        assert result.priority == TaskPriority.HIGH

    def test_from_typedb_task_with_optional_fields(self):
        from agent.orchestrator.task_poller import PollableTask
        task = MagicMock()
        task.id = "T-4"
        task.name = "Full task"
        task.phase = "IMPLEMENT"
        task.status = "pending"
        task.agent_id = "code-agent"
        task.body = "Task body text"
        task.gap_id = "GAP-001"
        result = PollableTask.from_typedb_task(task)
        assert result.agent_id == "code-agent"
        assert result.body == "Task body text"
        assert result.gap_id == "GAP-001"

    def test_from_typedb_task_no_phase(self):
        from agent.orchestrator.task_poller import PollableTask, TaskPriority
        task = MagicMock(spec=[])
        task.id = "T-5"
        task.name = "No phase"
        task.phase = None
        task.status = "pending"
        result = PollableTask.from_typedb_task(task)
        assert result.priority == TaskPriority.MEDIUM

    def test_medium_priority_no_evidence_required(self):
        from agent.orchestrator.task_poller import PollableTask
        task = MagicMock()
        task.id = "T-6"
        task.name = "Med task"
        task.phase = "RD-005"
        task.status = "pending"
        result = PollableTask.from_typedb_task(task)
        assert result.requires_evidence is False


# ── TypeDBTaskPoller init / properties ───────────────────────────


class TestPollerInit:
    def test_default_init(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        client = MagicMock()
        poller = TypeDBTaskPoller(client)
        assert poller.is_running is False
        assert poller._poll_interval == 5.0

    def test_custom_interval(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        poller = TypeDBTaskPoller(MagicMock(), poll_interval=10.0)
        assert poller._poll_interval == 10.0

    def test_stats(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        poller = TypeDBTaskPoller(MagicMock())
        stats = poller.stats
        assert stats["running"] is False
        assert stats["poll_count"] == 0
        assert stats["last_poll"] is None


# ── poll_once ────────────────────────────────────────────────────


class TestPollOnce:
    @pytest.mark.asyncio
    async def test_returns_sorted_tasks(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        task_low = MagicMock()
        task_low.id = "T-L"
        task_low.name = "Low"
        task_low.phase = "RD"
        task_low.status = "pending"
        task_high = MagicMock()
        task_high.id = "T-H"
        task_high.name = "High"
        task_high.phase = "P10.1"
        task_high.status = "pending"
        client = MagicMock()
        client.get_available_tasks.return_value = [task_low, task_high]
        poller = TypeDBTaskPoller(client)
        tasks = await poller.poll_once()
        assert len(tasks) == 2
        assert tasks[0].task_id == "T-H"  # HIGH first

    @pytest.mark.asyncio
    async def test_increments_stats(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        client = MagicMock()
        client.get_available_tasks.return_value = []
        poller = TypeDBTaskPoller(client)
        await poller.poll_once()
        assert poller._poll_count == 1
        assert poller._last_poll is not None

    @pytest.mark.asyncio
    async def test_exception_returns_empty(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        client = MagicMock()
        client.get_available_tasks.side_effect = Exception("db error")
        poller = TypeDBTaskPoller(client)
        tasks = await poller.poll_once()
        assert tasks == []


# ── claim_task / release_task / complete_task ─────────────────────


class TestTaskOperations:
    @pytest.mark.asyncio
    async def test_claim_success(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        client = MagicMock()
        client.update_task_status.return_value = {"ok": True}
        poller = TypeDBTaskPoller(client)
        result = await poller.claim_task("T-1", "agent-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_claim_failure(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        client = MagicMock()
        client.update_task_status.return_value = None
        poller = TypeDBTaskPoller(client)
        result = await poller.claim_task("T-1", "agent-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_claim_exception(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        client = MagicMock()
        client.update_task_status.side_effect = Exception("fail")
        poller = TypeDBTaskPoller(client)
        result = await poller.claim_task("T-1", "agent-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_release_success(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        client = MagicMock()
        client.update_task_status.return_value = {"ok": True}
        poller = TypeDBTaskPoller(client)
        result = await poller.release_task("T-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_complete_with_evidence(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        client = MagicMock()
        client.update_task_status.return_value = {"ok": True}
        poller = TypeDBTaskPoller(client)
        result = await poller.complete_task("T-1", "agent-1", evidence="Tests passed")
        assert result is True
        client.update_task_status.assert_called_once_with(
            task_id="T-1", status="completed", agent_id="agent-1", evidence="Tests passed",
        )


# ── callbacks ────────────────────────────────────────────────────


class TestCallbacks:
    def test_add_callback(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        poller = TypeDBTaskPoller(MagicMock())
        cb = MagicMock()
        poller.add_callback(cb)
        assert cb in poller._callbacks

    def test_remove_callback(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        poller = TypeDBTaskPoller(MagicMock())
        cb = MagicMock()
        poller.add_callback(cb)
        poller.remove_callback(cb)
        assert cb not in poller._callbacks

    def test_remove_nonexistent_callback(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        poller = TypeDBTaskPoller(MagicMock())
        poller.remove_callback(MagicMock())  # should not raise


# ── start_polling / stop_polling ─────────────────────────────────


class TestPolling:
    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        poller = TypeDBTaskPoller(MagicMock())
        with patch.object(poller, '_poll_loop', new_callable=AsyncMock):
            await poller.start_polling(interval=1.0)
        assert poller._running is True

    @pytest.mark.asyncio
    async def test_start_already_running(self):
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        poller = TypeDBTaskPoller(MagicMock())
        poller._running = True
        await poller.start_polling()
        # Should not add another poll task

    @pytest.mark.asyncio
    async def test_stop_polling(self):
        import asyncio
        from agent.orchestrator.task_poller import TypeDBTaskPoller
        poller = TypeDBTaskPoller(MagicMock())
        poller._running = True
        # Create a real cancelled future
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        fut.cancel()
        poller._poll_task = fut
        await poller.stop_polling()
        assert poller._running is False
        assert poller._poll_task is None
