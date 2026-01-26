"""
Robot Framework Library for Agent Platform Concurrency Tests.

Per RD-AGENT-TESTING: ATEST-003 - Multi-Agent Concurrency.
Split from test_agent_platform.py per DOC-SIZE-01-v1.
"""
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from robot.api.deco import keyword


@dataclass
class MockAgent:
    """Mock agent for concurrency testing."""
    agent_id: str
    role: str
    trust_score: float


@dataclass
class MockTaskQueue:
    """Mock task queue for concurrency testing."""
    tasks: List[Dict] = field(default_factory=list)
    claimed: Dict[str, str] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add_task(self, task: Dict) -> None:
        async with self._lock:
            self.tasks.append(task)

    async def claim_task(self, task_id: str, agent_id: str) -> bool:
        async with self._lock:
            if task_id in self.claimed:
                return False
            self.claimed[task_id] = agent_id
            return True


class AgentPlatformConcurrencyLibrary:
    """Library for agent concurrency tests (ATEST-003)."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    @keyword("Parallel Task Claim Single Winner")
    def parallel_task_claim_single_winner(self):
        """Only one agent can claim a task when multiple try."""
        async def run_test():
            queue = MockTaskQueue()
            task_id = "TASK-CONCURRENT-001"

            agents = [
                MockAgent("AGENT-A", "CODING", 0.85),
                MockAgent("AGENT-B", "CODING", 0.90),
                MockAgent("AGENT-C", "CODING", 0.80),
            ]

            results = await asyncio.gather(*[
                queue.claim_task(task_id, agent.agent_id)
                for agent in agents
            ])

            successful_claims = [r for r in results if r]
            return {
                "single_winner": len(successful_claims) == 1,
                "task_claimed": task_id in queue.claimed
            }

        return asyncio.run(run_test())

    @keyword("Queue Saturation All Processed")
    def queue_saturation_all_processed(self):
        """All tasks are processed when queue is saturated."""
        async def run_test():
            queue = MockTaskQueue()
            num_tasks = 20

            for i in range(num_tasks):
                await queue.add_task({
                    "id": f"TASK-SAT-{i:03d}",
                    "priority": "MEDIUM"
                })

            agents = [MockAgent(f"AGENT-{i}", "CODING", 0.85) for i in range(4)]
            processed = 0

            for task in queue.tasks:
                agent = agents[processed % len(agents)]
                if await queue.claim_task(task["id"], agent.agent_id):
                    processed += 1

            return {
                "tasks_added": len(queue.tasks) == num_tasks,
                "all_processed": processed == num_tasks
            }

        return asyncio.run(run_test())

    @keyword("No Double Claim")
    def no_double_claim(self):
        """Task cannot be claimed twice."""
        async def run_test():
            queue = MockTaskQueue()
            task_id = "TASK-DOUBLE-001"

            result1 = await queue.claim_task(task_id, "AGENT-1")
            result2 = await queue.claim_task(task_id, "AGENT-2")

            return {
                "first_success": result1 is True,
                "second_fails": result2 is False,
                "original_preserved": queue.claimed[task_id] == "AGENT-1"
            }

        return asyncio.run(run_test())
