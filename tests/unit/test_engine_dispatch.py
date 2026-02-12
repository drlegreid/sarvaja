"""
Unit tests for Orchestrator Dispatch Logic.

Per DOC-SIZE-01-v1: Tests for agent/orchestrator/engine_dispatch.py module.
Tests: OrchestratorDispatchMixin — dispatch_next, complete_task,
       _select_agent_for_task, _get_min_trust_for_priority, _validate_assignment.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from agent.orchestrator.task_poller import PollableTask, TaskPriority
from agent.orchestrator.engine_models import AgentInfo, AgentRole, DispatchResult
from agent.orchestrator.engine_dispatch import OrchestratorDispatchMixin


def _make_task(task_id: str, priority: TaskPriority = TaskPriority.MEDIUM) -> PollableTask:
    return PollableTask(
        task_id=task_id, name=f"Task {task_id}", phase="RD",
        status="pending", priority=priority, requires_evidence=False,
    )


def _make_agent(agent_id: str, trust: float = 0.8, status: str = "AVAILABLE") -> AgentInfo:
    return AgentInfo(
        agent_id=agent_id, name=f"Agent {agent_id}",
        role=AgentRole.CODING, trust_score=trust, status=status,
    )


class _TestOrchestrator(OrchestratorDispatchMixin):
    """Concrete class mixing in dispatch methods."""

    def __init__(self):
        from agent.orchestrator.priority_queue import TaskPriorityQueue
        self._queue = TaskPriorityQueue()
        self._poller = MagicMock()
        self._poller.claim_task = AsyncMock(return_value=True)
        self._poller.complete_task = AsyncMock(return_value=True)
        self._agents = {}
        self._dispatch_count = 0

    def get_available_agents(self, role=None):
        return [a for a in self._agents.values() if a.status == "AVAILABLE"]


# ── _get_min_trust_for_priority ────────────────────────────────


class TestGetMinTrustForPriority:
    def test_critical(self):
        o = _TestOrchestrator()
        assert o._get_min_trust_for_priority(TaskPriority.CRITICAL) == 0.7

    def test_high(self):
        o = _TestOrchestrator()
        assert o._get_min_trust_for_priority(TaskPriority.HIGH) == 0.5

    def test_medium(self):
        o = _TestOrchestrator()
        assert o._get_min_trust_for_priority(TaskPriority.MEDIUM) == 0.0

    def test_low(self):
        o = _TestOrchestrator()
        assert o._get_min_trust_for_priority(TaskPriority.LOW) == 0.0


# ── _select_agent_for_task ─────────────────────────────────────


class TestSelectAgentForTask:
    def test_no_agents(self):
        o = _TestOrchestrator()
        task = _make_task("T-1")
        assert o._select_agent_for_task(task) is None

    def test_selects_highest_trust(self):
        o = _TestOrchestrator()
        a1 = _make_agent("a1", trust=0.6)
        a2 = _make_agent("a2", trust=0.9)
        o._agents = {"a1": a1, "a2": a2}
        task = _make_task("T-1")
        selected = o._select_agent_for_task(task)
        assert selected.agent_id == "a2"

    def test_filters_by_trust_for_critical(self):
        o = _TestOrchestrator()
        a1 = _make_agent("a1", trust=0.3)  # below 0.7 threshold
        o._agents = {"a1": a1}
        task = _make_task("T-1", TaskPriority.CRITICAL)
        assert o._select_agent_for_task(task) is None

    def test_load_balancing(self):
        o = _TestOrchestrator()
        a1 = _make_agent("a1", trust=0.8)
        a1.tasks_completed = 10
        a2 = _make_agent("a2", trust=0.8)
        a2.tasks_completed = 2
        o._agents = {"a1": a1, "a2": a2}
        task = _make_task("T-1")
        selected = o._select_agent_for_task(task)
        assert selected.agent_id == "a2"  # fewer tasks

    def test_busy_agent_excluded(self):
        o = _TestOrchestrator()
        a1 = _make_agent("a1", trust=0.9, status="BUSY")
        a2 = _make_agent("a2", trust=0.5)
        o._agents = {"a1": a1, "a2": a2}
        task = _make_task("T-1")
        selected = o._select_agent_for_task(task)
        assert selected.agent_id == "a2"


# ── _validate_assignment ───────────────────────────────────────
# kanren_constraints is not installed, so ImportError fallback fires naturally.


class TestValidateAssignment:
    def test_fallback_valid(self):
        o = _TestOrchestrator()
        agent = _make_agent("a1", trust=0.8)
        task = _make_task("T-1")
        # Block kanren import to force fallback path
        with patch.dict(sys.modules, {"governance.kanren_constraints": None}):
            result = o._validate_assignment(agent, task)
        assert result["valid"] is True

    def test_fallback_invalid_low_trust(self):
        o = _TestOrchestrator()
        agent = _make_agent("a1", trust=0.3)
        task = _make_task("T-1", TaskPriority.CRITICAL)
        with patch.dict(sys.modules, {"governance.kanren_constraints": None}):
            result = o._validate_assignment(agent, task)
        assert result["valid"] is False
        assert "Trust" in result["reason"]

    def test_fallback_supervisor_needed(self):
        o = _TestOrchestrator()
        agent = _make_agent("a1", trust=0.5)
        task = _make_task("T-1")
        with patch.dict(sys.modules, {"governance.kanren_constraints": None}):
            result = o._validate_assignment(agent, task)
        assert result["requires_supervisor"] is True

    def test_kanren_available(self):
        o = _TestOrchestrator()
        agent = _make_agent("a1", trust=0.9)
        task = _make_task("T-1")
        # kanren_constraints IS installed — uses real validate_agent_for_task
        result = o._validate_assignment(agent, task)
        assert result["valid"] is True


# ── dispatch_next ──────────────────────────────────────────────


class TestDispatchNext:
    @pytest.mark.asyncio
    async def test_empty_queue(self):
        o = _TestOrchestrator()
        result = await o.dispatch_next()
        assert result.success is False
        assert "No tasks" in result.message

    @pytest.mark.asyncio
    async def test_no_agent_available(self):
        o = _TestOrchestrator()
        o._queue.push(_make_task("T-1"))
        result = await o.dispatch_next()
        assert result.success is False
        assert "No suitable agent" in result.message
        assert o._queue.size == 1

    @pytest.mark.asyncio
    async def test_successful_dispatch(self):
        o = _TestOrchestrator()
        o._queue.push(_make_task("T-1"))
        a1 = _make_agent("a1", trust=0.8)
        o._agents = {"a1": a1}
        result = await o.dispatch_next()
        assert result.success is True
        assert result.task_id == "T-1"
        assert result.agent_id == "a1"
        assert a1.status == "BUSY"
        assert o._dispatch_count == 1

    @pytest.mark.asyncio
    async def test_claim_failure(self):
        o = _TestOrchestrator()
        o._queue.push(_make_task("T-1"))
        a1 = _make_agent("a1", trust=0.8)
        o._agents = {"a1": a1}
        o._poller.claim_task = AsyncMock(return_value=False)
        result = await o.dispatch_next()
        assert result.success is False
        assert "Failed to claim" in result.message

    @pytest.mark.asyncio
    async def test_validation_failure_requeues(self):
        o = _TestOrchestrator()
        o._queue.push(_make_task("T-1", TaskPriority.CRITICAL))
        a1 = _make_agent("a1", trust=0.3)  # too low for CRITICAL
        o._agents = {"a1": a1}
        result = await o.dispatch_next()
        assert result.success is False


# ── complete_task ──────────────────────────────────────────────


class TestCompleteTask:
    @pytest.mark.asyncio
    async def test_success(self):
        o = _TestOrchestrator()
        a1 = _make_agent("a1", trust=0.8, status="BUSY")
        a1.current_task = "T-1"
        o._agents = {"a1": a1}
        result = await o.complete_task("T-1", "a1", evidence="Tests passed")
        assert result is True
        assert a1.status == "AVAILABLE"
        assert a1.current_task is None
        assert a1.tasks_completed == 1

    @pytest.mark.asyncio
    async def test_failure(self):
        o = _TestOrchestrator()
        o._poller.complete_task = AsyncMock(return_value=False)
        result = await o.complete_task("T-1", "a1")
        assert result is False

    @pytest.mark.asyncio
    async def test_unknown_agent(self):
        o = _TestOrchestrator()
        result = await o.complete_task("T-1", "unknown-agent")
        assert result is True  # poller succeeds but no agent to update
