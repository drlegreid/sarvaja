"""
Tests for Agent Orchestrator (ORCH-002).

Per RULE-023: Test Coverage Protocol
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from agent.orchestrator.task_poller import (
    TypeDBTaskPoller,
    PollableTask,
    TaskPriority,
)
from agent.orchestrator.priority_queue import (
    TaskPriorityQueue,
    QueuedTask,
    create_queue_from_tasks,
)
from agent.orchestrator.engine import (
    OrchestratorEngine,
    AgentInfo,
    AgentRole,
    DispatchResult,
)


# =============================================================================
# Mock TypeDB Task
# =============================================================================

class MockTask:
    """Mock TypeDB Task for testing."""
    def __init__(self, task_id, name, status, phase, agent_id=None, body=None, gap_id=None):
        self.id = task_id
        self.name = name
        self.status = status
        self.phase = phase
        self.agent_id = agent_id
        self.body = body
        self.gap_id = gap_id


# =============================================================================
# PollableTask Tests
# =============================================================================

class TestPollableTask:
    """Test PollableTask dataclass."""

    def test_from_typedb_task_basic(self):
        """Convert basic TypeDB task."""
        mock = MockTask("TASK-001", "Test Task", "pending", "P10")
        task = PollableTask.from_typedb_task(mock)

        assert task.task_id == "TASK-001"
        assert task.name == "Test Task"
        assert task.status == "pending"
        assert task.phase == "P10"
        assert task.priority == TaskPriority.HIGH  # P10/P11 = HIGH

    def test_from_typedb_task_rd_phase(self):
        """R&D phase maps to MEDIUM priority."""
        mock = MockTask("RD-001", "R&D Task", "TODO", "RD")
        task = PollableTask.from_typedb_task(mock)

        assert task.priority == TaskPriority.MEDIUM

    def test_evidence_required_for_high(self):
        """HIGH priority tasks require evidence."""
        mock = MockTask("TASK-001", "Task", "pending", "P10")
        task = PollableTask.from_typedb_task(mock)

        assert task.requires_evidence is True

    def test_evidence_not_required_for_medium(self):
        """MEDIUM priority tasks don't require evidence."""
        mock = MockTask("TASK-001", "Task", "pending", "OTHER")
        task = PollableTask.from_typedb_task(mock)

        # Non-P10/P11/RD defaults to MEDIUM
        assert task.requires_evidence is False


# =============================================================================
# TaskPriorityQueue Tests
# =============================================================================

class TestTaskPriorityQueue:
    """Test priority queue functionality."""

    def test_push_and_pop(self):
        """Basic push and pop operations."""
        queue = TaskPriorityQueue()

        task = PollableTask(
            task_id="TASK-001",
            name="Test",
            priority=TaskPriority.MEDIUM,
            phase="P10",
            status="pending",
            requires_evidence=False,
        )

        assert queue.push(task) is True
        assert queue.size == 1

        popped = queue.pop()
        assert popped.task_id == "TASK-001"
        assert queue.size == 0

    def test_priority_ordering(self):
        """Higher priority tasks pop first."""
        queue = TaskPriorityQueue()

        low = PollableTask("LOW-001", "Low", TaskPriority.LOW, "P10", "pending", False)
        high = PollableTask("HIGH-001", "High", TaskPriority.HIGH, "P10", "pending", True)
        critical = PollableTask("CRIT-001", "Critical", TaskPriority.CRITICAL, "P10", "pending", True)

        queue.push(low)
        queue.push(high)
        queue.push(critical)

        assert queue.pop().task_id == "CRIT-001"
        assert queue.pop().task_id == "HIGH-001"
        assert queue.pop().task_id == "LOW-001"

    def test_duplicate_rejection(self):
        """Duplicate task IDs are rejected."""
        queue = TaskPriorityQueue()

        task = PollableTask("TASK-001", "Test", TaskPriority.MEDIUM, "P10", "pending", False)

        assert queue.push(task) is True
        assert queue.push(task) is False  # Duplicate
        assert queue.size == 1

    def test_peek_without_remove(self):
        """Peek returns task without removing."""
        queue = TaskPriorityQueue()

        task = PollableTask("TASK-001", "Test", TaskPriority.MEDIUM, "P10", "pending", False)
        queue.push(task)

        peeked = queue.peek()
        assert peeked.task_id == "TASK-001"
        assert queue.size == 1  # Still in queue

    def test_remove_specific_task(self):
        """Remove specific task by ID."""
        queue = TaskPriorityQueue()

        task1 = PollableTask("TASK-001", "Test1", TaskPriority.MEDIUM, "P10", "pending", False)
        task2 = PollableTask("TASK-002", "Test2", TaskPriority.MEDIUM, "P10", "pending", False)

        queue.push(task1)
        queue.push(task2)

        assert queue.remove("TASK-001") is True
        assert queue.size == 1
        assert queue.pop().task_id == "TASK-002"

    def test_get_by_priority(self):
        """Filter tasks by priority."""
        queue = TaskPriorityQueue()

        queue.push(PollableTask("LOW-001", "L1", TaskPriority.LOW, "P10", "pending", False))
        queue.push(PollableTask("HIGH-001", "H1", TaskPriority.HIGH, "P10", "pending", True))
        queue.push(PollableTask("HIGH-002", "H2", TaskPriority.HIGH, "P10", "pending", True))

        high_tasks = queue.get_by_priority(TaskPriority.HIGH)
        assert len(high_tasks) == 2

    def test_max_size_enforcement(self):
        """Queue respects max size."""
        queue = TaskPriorityQueue(max_size=2)

        queue.push(PollableTask("T1", "T1", TaskPriority.LOW, "P10", "pending", False))
        queue.push(PollableTask("T2", "T2", TaskPriority.LOW, "P10", "pending", False))

        # Adding third with same priority should fail
        result = queue.push(PollableTask("T3", "T3", TaskPriority.LOW, "P10", "pending", False))
        assert result is False
        assert queue.size == 2

    def test_create_from_tasks(self):
        """Create queue from task list."""
        tasks = [
            PollableTask("T1", "T1", TaskPriority.HIGH, "P10", "pending", True),
            PollableTask("T2", "T2", TaskPriority.LOW, "P10", "pending", False),
        ]
        queue = create_queue_from_tasks(tasks)

        assert queue.size == 2
        assert queue.pop().task_id == "T1"  # HIGH first


# =============================================================================
# TypeDBTaskPoller Tests
# =============================================================================

class TestTypeDBTaskPoller:
    """Test task poller functionality."""

    def test_poll_once_returns_sorted_tasks(self):
        """Poll returns tasks sorted by priority."""
        mock_client = Mock()
        mock_client.get_available_tasks.return_value = [
            MockTask("LOW-001", "Low", "pending", "OTHER"),
            MockTask("HIGH-001", "High", "pending", "P10"),
        ]

        poller = TypeDBTaskPoller(mock_client)

        # Run poll
        tasks = asyncio.run(poller.poll_once())

        assert len(tasks) == 2
        assert tasks[0].task_id == "HIGH-001"  # Higher priority first

    def test_poll_stats(self):
        """Poller tracks statistics."""
        mock_client = Mock()
        mock_client.get_available_tasks.return_value = []

        poller = TypeDBTaskPoller(mock_client)

        assert poller.stats["poll_count"] == 0

        asyncio.run(poller.poll_once())

        assert poller.stats["poll_count"] == 1
        assert poller.stats["last_poll"] is not None

    def test_claim_task(self):
        """Claim task updates status."""
        mock_client = Mock()
        mock_client.update_task_status.return_value = MockTask("T1", "T", "in_progress", "P10")

        poller = TypeDBTaskPoller(mock_client)
        result = asyncio.run(poller.claim_task("T1", "AGENT-001"))

        assert result is True
        mock_client.update_task_status.assert_called_once()

    def test_complete_task_with_evidence(self):
        """Complete task with evidence."""
        mock_client = Mock()
        mock_client.update_task_status.return_value = MockTask("T1", "T", "completed", "P10")

        poller = TypeDBTaskPoller(mock_client)
        result = asyncio.run(poller.complete_task("T1", "AGENT-001", evidence="test evidence"))

        assert result is True
        mock_client.update_task_status.assert_called_with(
            task_id="T1",
            status="completed",
            agent_id="AGENT-001",
            evidence="test evidence"
        )


# =============================================================================
# AgentInfo Tests
# =============================================================================

class TestAgentInfo:
    """Test agent info dataclass."""

    def test_trust_level_expert(self):
        """Expert trust level for score >= 0.9."""
        agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.95)
        assert agent.trust_level == "expert"

    def test_trust_level_trusted(self):
        """Trusted level for score >= 0.7."""
        agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.75)
        assert agent.trust_level == "trusted"

    def test_trust_level_supervised(self):
        """Supervised level for score >= 0.5."""
        agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.55)
        assert agent.trust_level == "supervised"

    def test_trust_level_restricted(self):
        """Restricted level for score < 0.5."""
        agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.35)
        assert agent.trust_level == "restricted"


# =============================================================================
# OrchestratorEngine Tests
# =============================================================================

class TestOrchestratorEngine:
    """Test orchestrator engine."""

    def test_register_agent(self):
        """Register agent successfully."""
        mock_client = Mock()
        engine = OrchestratorEngine(mock_client)

        agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.9)
        assert engine.register_agent(agent) is True
        assert engine.get_agent("A1") is not None

    def test_register_duplicate_fails(self):
        """Duplicate agent registration fails."""
        mock_client = Mock()
        engine = OrchestratorEngine(mock_client)

        agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.9)
        engine.register_agent(agent)

        assert engine.register_agent(agent) is False

    def test_unregister_agent(self):
        """Unregister agent successfully."""
        mock_client = Mock()
        engine = OrchestratorEngine(mock_client)

        agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.9)
        engine.register_agent(agent)

        assert engine.unregister_agent("A1") is True
        assert engine.get_agent("A1") is None

    def test_get_available_agents(self):
        """Get available agents."""
        mock_client = Mock()
        engine = OrchestratorEngine(mock_client)

        engine.register_agent(AgentInfo("A1", "T1", AgentRole.CODING, 0.9))
        engine.register_agent(AgentInfo("A2", "T2", AgentRole.SYNC, 0.8))

        available = engine.get_available_agents()
        assert len(available) == 2

        # Filter by role
        coding_agents = engine.get_available_agents(AgentRole.CODING)
        assert len(coding_agents) == 1

    def test_poll_and_queue(self):
        """Poll tasks and add to queue."""
        mock_client = Mock()
        mock_client.get_available_tasks.return_value = [
            MockTask("T1", "Task1", "pending", "P10"),
            MockTask("T2", "Task2", "pending", "P10"),
        ]

        engine = OrchestratorEngine(mock_client)
        queued = asyncio.run(engine.poll_and_queue())

        assert queued == 2
        assert engine._queue.size == 2

    def test_dispatch_no_tasks(self):
        """Dispatch with empty queue."""
        mock_client = Mock()
        engine = OrchestratorEngine(mock_client)

        result = asyncio.run(engine.dispatch_next())

        assert result.success is False
        assert "No tasks" in result.message

    def test_dispatch_no_agents(self):
        """Dispatch with no available agents."""
        mock_client = Mock()
        mock_client.get_available_tasks.return_value = [
            MockTask("T1", "Task1", "pending", "P10"),
        ]

        engine = OrchestratorEngine(mock_client)
        asyncio.run(engine.poll_and_queue())

        result = asyncio.run(engine.dispatch_next())

        assert result.success is False
        assert "No suitable agent" in result.message

    def test_dispatch_success(self):
        """Successful task dispatch."""
        mock_client = Mock()
        mock_client.get_available_tasks.return_value = [
            MockTask("T1", "Task1", "pending", "P10"),
        ]
        mock_client.update_task_status.return_value = MockTask("T1", "T1", "in_progress", "P10")

        engine = OrchestratorEngine(mock_client)
        engine.register_agent(AgentInfo("A1", "Test", AgentRole.CODING, 0.9))

        asyncio.run(engine.poll_and_queue())
        result = asyncio.run(engine.dispatch_next())

        assert result.success is True
        assert result.task_id == "T1"
        assert result.agent_id == "A1"

    def test_dispatch_trust_constraint(self):
        """Trust constraint blocks low-trust agent from CRITICAL."""
        mock_client = Mock()
        mock_client.get_available_tasks.return_value = []

        engine = OrchestratorEngine(mock_client)

        # Register low-trust agent
        engine.register_agent(AgentInfo("A1", "LowTrust", AgentRole.CODING, 0.4))

        # Manually add CRITICAL task
        critical_task = PollableTask(
            task_id="CRIT-001",
            name="Critical",
            priority=TaskPriority.CRITICAL,
            phase="P10",
            status="pending",
            requires_evidence=True,
        )
        engine._queue.push(critical_task)

        result = asyncio.run(engine.dispatch_next())

        # Should fail - no agent with sufficient trust
        assert result.success is False

    def test_complete_task_updates_agent(self):
        """Completing task updates agent status."""
        mock_client = Mock()
        mock_client.update_task_status.return_value = MockTask("T1", "T1", "completed", "P10")

        engine = OrchestratorEngine(mock_client)
        agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.9, status="BUSY", current_task="T1")
        engine.register_agent(agent)

        result = asyncio.run(engine.complete_task("T1", "A1", evidence="Done"))

        assert result is True
        assert agent.status == "AVAILABLE"
        assert agent.current_task is None
        assert agent.tasks_completed == 1

    def test_stats(self):
        """Engine reports statistics."""
        mock_client = Mock()
        engine = OrchestratorEngine(mock_client)

        stats = engine.stats

        assert "running" in stats
        assert "dispatch_count" in stats
        assert "queue_stats" in stats
        assert "agents_registered" in stats
