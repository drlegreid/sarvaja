"""
Orchestrator Engine (ORCH-002).

Central task dispatch engine for multi-agent orchestration.

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing
Per DOC-SIZE-01-v1: Models in engine_models.py, dispatch in engine_dispatch.py.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .task_poller import TypeDBTaskPoller, PollableTask, TaskPriority
from .priority_queue import TaskPriorityQueue
from .engine_models import AgentRole, AgentInfo, DispatchResult  # noqa: F401
from .engine_dispatch import OrchestratorDispatchMixin  # noqa: F401 — re-export


class OrchestratorEngine(OrchestratorDispatchMixin):
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
        engine.register_agent(AgentInfo(...))
        await engine.start()
        result = await engine.dispatch_next()
        await engine.stop()
    """

    def __init__(
        self,
        client: Any,
        poll_interval: float = 5.0,
        max_queue_size: int = 100,
    ):
        """Initialize orchestrator."""
        self._client = client
        self._poller = TypeDBTaskPoller(client, poll_interval)
        self._queue = TaskPriorityQueue(max_queue_size)
        self._agents: Dict[str, AgentInfo] = {}
        self._running = False
        self._dispatch_count = 0
        self._started_at: Optional[datetime] = None
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
        """Register an agent for task dispatch."""
        if agent.agent_id in self._agents:
            return False
        self._agents[agent.agent_id] = agent
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_available_agents(self, role: AgentRole = None) -> List[AgentInfo]:
        """Get available agents, optionally filtered by role."""
        agents = [a for a in self._agents.values() if a.status == "AVAILABLE"]
        if role:
            agents = [a for a in agents if a.role == role]
        return agents

    def set_handler(self, role: AgentRole, handler: Callable) -> None:
        """Set task handler for a role."""
        self._handlers[role] = handler

    async def start(self) -> None:
        """Start orchestration loop."""
        if self._running:
            return
        self._running = True
        self._started_at = datetime.now()
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
        """Manually poll and queue tasks."""
        tasks = await self._poller.poll_once()
        return self._queue.push_many(tasks)


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

    engine.register_agent(AgentInfo(
        agent_id="AGENT-001",
        name="Claude Code R&D",
        role=AgentRole.CODING,
        trust_score=0.95,
    ))
    engine.register_agent(AgentInfo(
        agent_id="AGENT-002",
        name="Sync Agent",
        role=AgentRole.SYNC,
        trust_score=0.75,
    ))

    print("Agents registered:", len(engine._agents))

    queued = await engine.poll_and_queue()
    print(f"Tasks queued: {queued}")

    result = await engine.dispatch_next()
    print(f"Dispatch result: {result}")

    print("\nOrchestrator engine operational")


if __name__ == "__main__":
    asyncio.run(demo_orchestrator())
