"""
Unit tests for Task Backlog Agent.

Per DOC-SIZE-01-v1: Tests for agent/sync_agent/backlog.py.
Tests: TaskBacklogAgent — init, _default_handler, get_available_tasks,
       claim_task, claim_next_task, complete_task, execute_task,
       process_one_task, run_loop, stop, get_stats.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.sync_agent.backlog import TaskBacklogAgent
from agent.sync_agent.models import TaskExecution


# ── Init / defaults ──────────────────────────────────────


class TestInit:
    def test_defaults(self):
        agent = TaskBacklogAgent(agent_id="test-agent")
        assert agent.agent_id == "test-agent"
        assert agent.api_base_url == "http://localhost:8082"
        assert agent.poll_interval == 30
        assert agent.running is False
        assert agent.tasks_completed == 0
        assert agent.tasks_failed == 0

    def test_custom_params(self):
        handler = MagicMock()
        agent = TaskBacklogAgent("a1", "http://custom:9000", handler, 10)
        assert agent.api_base_url == "http://custom:9000"
        assert agent.task_handler is handler
        assert agent.poll_interval == 10


# ── _default_handler ─────────────────────────────────────


class TestDefaultHandler:
    def test_returns_task_execution(self):
        agent = TaskBacklogAgent("test-agent")
        task = {"task_id": "T-001", "description": "Do stuff", "phase": "P1"}
        result = agent._default_handler(task)
        assert isinstance(result, TaskExecution)
        assert result.task_id == "T-001"
        assert result.success is True
        assert "Do stuff" in result.evidence

    def test_includes_linked_rules(self):
        agent = TaskBacklogAgent("test-agent")
        task = {"task_id": "T-002", "linked_rules": ["R-1", "R-2"]}
        result = agent._default_handler(task)
        assert result.rules_applied == ["R-1", "R-2"]
        assert "R-1" in result.evidence

    def test_uses_id_fallback(self):
        agent = TaskBacklogAgent("test-agent")
        task = {"id": "T-003"}
        result = agent._default_handler(task)
        assert result.task_id == "T-003"


# ── get_available_tasks ──────────────────────────────────


class TestGetAvailableTasks:
    @pytest.mark.asyncio
    async def test_success(self):
        agent = TaskBacklogAgent("test-agent")
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = [{"task_id": "T-1"}]

        with patch("agent.sync_agent.backlog.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await agent.get_available_tasks()
        assert result == [{"task_id": "T-1"}]

    @pytest.mark.asyncio
    async def test_api_error_returns_empty(self):
        agent = TaskBacklogAgent("test-agent")
        mock_resp = MagicMock(status_code=500)

        with patch("agent.sync_agent.backlog.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await agent.get_available_tasks()
        assert result == []

    @pytest.mark.asyncio
    async def test_exception_returns_empty(self):
        agent = TaskBacklogAgent("test-agent")
        with patch("agent.sync_agent.backlog.httpx.AsyncClient", side_effect=Exception("err")):
            result = await agent.get_available_tasks()
        assert result == []


# ── claim_task ───────────────────────────────────────────


class TestClaimTask:
    @pytest.mark.asyncio
    async def test_success(self):
        agent = TaskBacklogAgent("test-agent")
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"task_id": "T-1", "status": "IN_PROGRESS"}

        with patch("agent.sync_agent.backlog.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.put.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await agent.claim_task("T-1")
        assert result is not None
        assert agent.current_task["task_id"] == "T-1"

    @pytest.mark.asyncio
    async def test_claim_failure(self):
        agent = TaskBacklogAgent("test-agent")
        mock_resp = MagicMock(status_code=409, text="already claimed")

        with patch("agent.sync_agent.backlog.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.put.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await agent.claim_task("T-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_exception(self):
        agent = TaskBacklogAgent("test-agent")
        with patch("agent.sync_agent.backlog.httpx.AsyncClient", side_effect=Exception("err")):
            result = await agent.claim_task("T-1")
        assert result is None


# ── complete_task ────────────────────────────────────────


class TestCompleteTask:
    @pytest.mark.asyncio
    async def test_success(self):
        agent = TaskBacklogAgent("test-agent")
        agent.current_task = {"task_id": "T-1"}
        execution = TaskExecution("T-1", True, "done", 1.0)

        mock_resp = MagicMock(status_code=200)
        with patch("agent.sync_agent.backlog.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.put.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await agent.complete_task(execution)
        assert result is True
        assert agent.current_task is None
        assert agent.tasks_completed == 1

    @pytest.mark.asyncio
    async def test_failure(self):
        agent = TaskBacklogAgent("test-agent")
        execution = TaskExecution("T-1", True, "done", 1.0)
        mock_resp = MagicMock(status_code=400, text="bad request")

        with patch("agent.sync_agent.backlog.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.put.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await agent.complete_task(execution)
        assert result is False


# ── execute_task ─────────────────────────────────────────


class TestExecuteTask:
    @pytest.mark.asyncio
    async def test_success(self):
        agent = TaskBacklogAgent("test-agent")
        task = {"task_id": "T-1"}
        result = await agent.execute_task(task)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_handler_exception(self):
        def bad_handler(task):
            raise ValueError("boom")

        agent = TaskBacklogAgent("test-agent", task_handler=bad_handler)
        result = await agent.execute_task({"task_id": "T-1"})
        assert result.success is False
        assert "boom" in result.error
        assert agent.tasks_failed == 1


# ── stop / get_stats ─────────────────────────────────────


class TestStopAndStats:
    def test_stop(self):
        agent = TaskBacklogAgent("test-agent")
        agent.running = True
        agent.stop()
        assert agent.running is False

    def test_get_stats(self):
        agent = TaskBacklogAgent("test-agent")
        agent.tasks_completed = 5
        agent.tasks_failed = 1
        stats = agent.get_stats()
        assert stats["agent_id"] == "test-agent"
        assert stats["tasks_completed"] == 5
        assert stats["tasks_failed"] == 1
        assert stats["current_task"] is None
        assert stats["running"] is False

    def test_stats_with_current_task(self):
        agent = TaskBacklogAgent("test-agent")
        agent.current_task = {"task_id": "T-1"}
        stats = agent.get_stats()
        assert stats["current_task"] == "T-1"


# ── run_loop ─────────────────────────────────────────────


class TestRunLoop:
    @pytest.mark.asyncio
    async def test_max_tasks_limit(self):
        agent = TaskBacklogAgent("test-agent")
        agent.process_one_task = AsyncMock(return_value=True)

        await agent.run_loop(max_tasks=3)
        assert agent.process_one_task.call_count == 3

    @pytest.mark.asyncio
    async def test_no_tasks_available(self):
        agent = TaskBacklogAgent("test-agent", poll_interval=0)
        call_count = 0

        async def mock_process():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                agent.running = False
            return False

        agent.process_one_task = mock_process
        await agent.run_loop()
        assert call_count >= 2
