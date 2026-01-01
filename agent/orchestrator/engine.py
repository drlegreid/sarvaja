"""
Orchestrator Engine (ORCH-002).

Central task dispatch engine for multi-agent orchestration.

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

from .task_poller import TypeDBTaskPoller, PollableTask, TaskPriority
from .priority_queue import TaskPriorityQueue


class AgentRole(Enum):
    """Agent role types for dispatch."""
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    CODING = "coding"
    CURATOR = "curator"
    SYNC = "sync"


@dataclass
class AgentInfo:
    """Agent registration info."""
    agent_id: str
    name: str
    role: AgentRole
    trust_score: float
    status: str = "AVAILABLE"
    current_task: Optional[str] = None
    tasks_completed: int = 0

    @property
    def trust_level(self) -> str:
        """Get trust level string per RULE-011."""
        if self.trust_score >= 0.9:
            return "expert"
        elif self.trust_score >= 0.7:
            return "trusted"
        elif self.trust_score >= 0.5:
            return "supervised"
        else:
            return "restricted"


@dataclass
class DispatchResult:
    """Result of task dispatch."""
    success: bool
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    message: str = ""
    requires_supervisor: bool = False
    constraints_checked: List[str] = None

    def __post_init__(self):
        if self.constraints_checked is None:
            self.constraints_checked = []


class OrchestratorEngine:
    """
    Central orchestrator for multi-agent task dispatch.

    Per ORCH-001 design from RD-AGENT-ORCHESTRATION.md.

    Features:
    - Task polling from TypeDB
    - Priority-based dispatch queue
    - Trust-weighted agent selection (RULE-011)
    - Kanren constraint validation

    Usage:
        engine = OrchestratorEngine(typedb_client)

        # Register agents
        engine.register_agent(AgentInfo(...))

        # Start orchestration
        await engine.start()

        # Manual dispatch
        result = await engine.dispatch_next()

        # Stop orchestration
        await engine.stop()
    """

    def __init__(
        self,
        client: Any,
        poll_interval: float = 5.0,
        max_queue_size: int = 100,
    ):
        """
        Initialize orchestrator.

        Args:
            client: TypeDB client instance
            poll_interval: Seconds between task polls
            max_queue_size: Maximum task queue size
        """
        self._client = client
        self._poller = TypeDBTaskPoller(client, poll_interval)
        self._queue = TaskPriorityQueue(max_queue_size)
        self._agents: Dict[str, AgentInfo] = {}
        self._running = False
        self._dispatch_count = 0
        self._started_at: Optional[datetime] = None

        # Task handlers by role
        self._handlers: Dict[AgentRole, Callable] = {}

    @property
    def is_running(self) -> bool:
        """Check if orchestrator is running."""
        return self._running

    @property
    def stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "running": self._running,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "dispatch_count": self._dispatch_count,
            "queue_stats": self._queue.stats,
            "poller_stats": self._poller.stats,
            "agents_registered": len(self._agents),
            "agents_available": len([a for a in self._agents.values() if a.status == "AVAILABLE"]),
        }

    def register_agent(self, agent: AgentInfo) -> bool:
        """
        Register an agent for task dispatch.

        Args:
            agent: Agent info

        Returns:
            True if registered, False if already exists
        """
        if agent.agent_id in self._agents:
            return False
        self._agents[agent.agent_id] = agent
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent.

        Args:
            agent_id: Agent to unregister

        Returns:
            True if removed, False if not found
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_available_agents(self, role: AgentRole = None) -> List[AgentInfo]:
        """
        Get available agents.

        Args:
            role: Optional role filter

        Returns:
            List of available agents
        """
        agents = [a for a in self._agents.values() if a.status == "AVAILABLE"]
        if role:
            agents = [a for a in agents if a.role == role]
        return agents

    def set_handler(self, role: AgentRole, handler: Callable) -> None:
        """
        Set task handler for a role.

        Args:
            role: Agent role
            handler: Async callable(task, agent) -> result
        """
        self._handlers[role] = handler

    async def start(self) -> None:
        """Start orchestration loop."""
        if self._running:
            return

        self._running = True
        self._started_at = datetime.now()

        # Start poller with queue callback
        self._poller.add_callback(self._on_task_available)
        await self._poller.start_polling()

    async def stop(self) -> None:
        """Stop orchestration."""
        self._running = False
        await self._poller.stop_polling()

    def _on_task_available(self, task: PollableTask) -> None:
        """Callback when task found by poller."""
        self._queue.push(task)

    async def poll_and_queue(self) -> int:
        """
        Manually poll and queue tasks.

        Returns:
            Number of tasks queued
        """
        tasks = await self._poller.poll_once()
        return self._queue.push_many(tasks)

    async def dispatch_next(self) -> DispatchResult:
        """
        Dispatch next task from queue.

        Selects appropriate agent based on:
        - Task priority
        - Agent trust level (RULE-011)
        - Agent availability

        Returns:
            Dispatch result with status
        """
        # Get next task
        task = self._queue.pop()
        if not task:
            return DispatchResult(
                success=False,
                message="No tasks in queue"
            )

        # Select agent
        agent = self._select_agent_for_task(task)
        if not agent:
            # Return task to queue
            self._queue.push(task)
            return DispatchResult(
                success=False,
                task_id=task.task_id,
                message="No suitable agent available"
            )

        # Validate with Kanren constraints
        validation = self._validate_assignment(agent, task)
        if not validation["valid"]:
            # Return task to queue
            self._queue.push(task)
            return DispatchResult(
                success=False,
                task_id=task.task_id,
                agent_id=agent.agent_id,
                message=f"Constraint validation failed: {validation.get('reason', 'Unknown')}",
                constraints_checked=validation.get("constraints_checked", [])
            )

        # Claim task
        claimed = await self._poller.claim_task(task.task_id, agent.agent_id)
        if not claimed:
            return DispatchResult(
                success=False,
                task_id=task.task_id,
                agent_id=agent.agent_id,
                message="Failed to claim task (already claimed?)"
            )

        # Update agent status
        agent.status = "BUSY"
        agent.current_task = task.task_id

        self._dispatch_count += 1

        return DispatchResult(
            success=True,
            task_id=task.task_id,
            agent_id=agent.agent_id,
            message="Task dispatched successfully",
            requires_supervisor=validation.get("requires_supervisor", False),
            constraints_checked=validation.get("constraints_checked", [])
        )

    async def complete_task(
        self,
        task_id: str,
        agent_id: str,
        evidence: str = None
    ) -> bool:
        """
        Mark task as completed.

        Args:
            task_id: Completed task
            agent_id: Agent that completed it
            evidence: Evidence for CRITICAL/HIGH tasks

        Returns:
            True if recorded successfully
        """
        result = await self._poller.complete_task(task_id, agent_id, evidence)

        if result and agent_id in self._agents:
            agent = self._agents[agent_id]
            agent.status = "AVAILABLE"
            agent.current_task = None
            agent.tasks_completed += 1

        return result

    def _select_agent_for_task(self, task: PollableTask) -> Optional[AgentInfo]:
        """
        Select best agent for task.

        Selection criteria:
        1. Agent must be available
        2. Trust level must match task priority (RULE-011)
        3. Prefer agent with matching role
        4. Prefer agent with fewer completed tasks (load balancing)
        """
        available = self.get_available_agents()
        if not available:
            return None

        # Filter by trust requirement
        min_trust = self._get_min_trust_for_priority(task.priority)
        candidates = [a for a in available if a.trust_score >= min_trust]

        if not candidates:
            return None

        # Sort by: trust (desc) → tasks_completed (asc)
        candidates.sort(key=lambda a: (-a.trust_score, a.tasks_completed))

        return candidates[0]

    def _get_min_trust_for_priority(self, priority: TaskPriority) -> float:
        """
        Get minimum trust required for task priority.

        Per RULE-011:
        - CRITICAL: 0.7 (trusted/expert)
        - HIGH: 0.5 (supervised and above)
        - MEDIUM/LOW: 0.0 (any)
        """
        trust_map = {
            TaskPriority.CRITICAL: 0.7,
            TaskPriority.HIGH: 0.5,
            TaskPriority.MEDIUM: 0.0,
            TaskPriority.LOW: 0.0,
        }
        return trust_map.get(priority, 0.0)

    def _validate_assignment(
        self,
        agent: AgentInfo,
        task: PollableTask
    ) -> Dict[str, Any]:
        """
        Validate task assignment using Kanren constraints.

        Imports and uses governance.kanren_constraints if available.
        """
        constraints_checked = []

        try:
            from governance.kanren_constraints import (
                validate_agent_for_task,
                trust_level,
                requires_supervisor,
            )

            # Use Kanren validation
            result = validate_agent_for_task(
                agent.agent_id,
                agent.trust_score,
                task.priority.name
            )

            return {
                "valid": result["valid"],
                "requires_supervisor": result.get("requires_supervisor", False),
                "constraints_checked": result.get("constraints_checked", []),
                "trust_level": result.get("trust_level"),
            }

        except ImportError:
            # Fallback to simple validation
            constraints_checked.append("RULE-011: Trust-based (fallback)")

            min_trust = self._get_min_trust_for_priority(task.priority)
            is_valid = agent.trust_score >= min_trust
            needs_supervisor = agent.trust_score < 0.7

            return {
                "valid": is_valid,
                "requires_supervisor": needs_supervisor,
                "constraints_checked": constraints_checked,
                "reason": None if is_valid else f"Trust {agent.trust_score} < required {min_trust}",
            }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_engine_from_env() -> OrchestratorEngine:
    """Create engine using environment configuration."""
    from governance.client import TypeDBClient

    client = TypeDBClient()
    if client.connect():
        return OrchestratorEngine(client)
    else:
        raise ConnectionError("Failed to connect to TypeDB")


async def demo_orchestrator():
    """Demonstrate orchestrator functionality."""
    print("=== Orchestrator Engine Demo ===\n")

    # Create mock client for demo
    class MockClient:
        def get_available_tasks(self):
            from governance.client import Task
            return [
                Task("TASK-001", "Fix bug", "pending", "P10"),
                Task("TASK-002", "Add feature", "pending", "P11"),
            ]

        def update_task_status(self, task_id, status, agent_id=None, evidence=None):
            return True

    engine = OrchestratorEngine(MockClient())

    # Register agents
    engine.register_agent(AgentInfo(
        agent_id="AGENT-001",
        name="Claude Code R&D",
        role=AgentRole.CODING,
        trust_score=0.95
    ))
    engine.register_agent(AgentInfo(
        agent_id="AGENT-002",
        name="Sync Agent",
        role=AgentRole.SYNC,
        trust_score=0.75
    ))

    print("Agents registered:", len(engine._agents))

    # Poll and queue
    queued = await engine.poll_and_queue()
    print(f"Tasks queued: {queued}")

    # Dispatch
    result = await engine.dispatch_next()
    print(f"Dispatch result: {result}")

    print("\n✅ Orchestrator engine operational")


if __name__ == "__main__":
    asyncio.run(demo_orchestrator())
