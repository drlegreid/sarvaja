"""
Robot Framework Library for Agent Platform Recovery Tests.

Per RD-AGENT-TESTING: ATEST-008 - Recovery Scenarios.
Split from test_agent_platform.py per DOC-SIZE-01-v1.
"""
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
from robot.api.deco import keyword


@dataclass
class MockTaskQueue:
    """Mock task queue for recovery testing."""
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


@dataclass
class MockAgent:
    """Mock agent for recovery testing."""
    agent_id: str
    role: str
    trust_score: float
    status: str = "ACTIVE"


class AgentPlatformRecoveryLibrary:
    """Library for agent recovery scenario tests (ATEST-008)."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    @keyword("Agent Crash Task Reassignment")
    def agent_crash_task_reassignment(self):
        """When agent crashes mid-task, task becomes reclaimable."""
        async def run_test():
            queue = MockTaskQueue()
            await queue.add_task({"id": "TASK-CRASH-001", "priority": "HIGH"})

            agent1 = MockAgent("AGENT-CRASH-1", "CODING", 0.85)
            agent2 = MockAgent("AGENT-CRASH-2", "CODING", 0.80)

            claim1 = await queue.claim_task("TASK-CRASH-001", agent1.agent_id)

            # Simulate crash: release claim
            async with queue._lock:
                if "TASK-CRASH-001" in queue.claimed:
                    del queue.claimed["TASK-CRASH-001"]

            claim2 = await queue.claim_task("TASK-CRASH-001", agent2.agent_id)

            return {
                "first_claimed": claim1 is True,
                "second_claimed": claim2 is True
            }

        return asyncio.run(run_test())

    @keyword("Task Timeout Releases Claim")
    def task_timeout_releases_claim(self):
        """Task times out and becomes available for other agents."""
        async def run_test():
            queue = MockTaskQueue()
            await queue.add_task({
                "id": "TASK-TIMEOUT-001",
                "priority": "MEDIUM",
                "timeout_ms": 1000
            })

            agent = MockAgent("AGENT-TIMEOUT-1", "CODING", 0.90)

            claimed = await queue.claim_task("TASK-TIMEOUT-001", agent.agent_id)

            # Simulate timeout
            async with queue._lock:
                queue.claimed.pop("TASK-TIMEOUT-001", None)

            reclaimed = await queue.claim_task("TASK-TIMEOUT-001", "AGENT-NEW")

            return {
                "initial_claimed": claimed is True,
                "reclaimed": reclaimed is True
            }

        return asyncio.run(run_test())

    @keyword("Agent Reconnect Resumes Task")
    def agent_reconnect_resumes_task(self):
        """Agent reconnects and can resume previously claimed task."""
        @dataclass
        class MockPersistentQueue:
            assignments: Dict[str, str] = field(default_factory=dict)

            def assign(self, task_id: str, agent_id: str):
                self.assignments[task_id] = agent_id

            def get_agent_tasks(self, agent_id: str) -> List[str]:
                return [t for t, a in self.assignments.items() if a == agent_id]

        queue = MockPersistentQueue()
        agent = MockAgent("AGENT-RECONNECT-1", "CODING", 0.85)

        queue.assign("TASK-RESUME-001", agent.agent_id)
        agent.status = "OFFLINE"
        agent.status = "ACTIVE"

        my_tasks = queue.get_agent_tasks(agent.agent_id)
        return {"task_preserved": "TASK-RESUME-001" in my_tasks}

    @keyword("Graceful Degradation On MCP Failure")
    def graceful_degradation_on_mcp_failure(self):
        """System continues with reduced capacity when MCP service fails."""
        @dataclass
        class MockMCPHealth:
            services: Dict[str, bool] = field(default_factory=dict)

            def check_health(self) -> Dict[str, Any]:
                healthy = sum(1 for ok in self.services.values() if ok)
                total = len(self.services)
                return {
                    "healthy_count": healthy,
                    "total_count": total,
                    "degraded": healthy < total,
                    "operational": healthy > 0
                }

        health = MockMCPHealth()
        health.services = {
            "typedb": True,
            "chromadb": True,
            "gov-core": False,
            "gov-tasks": True,
        }

        status = health.check_health()
        return {
            "degraded": status["degraded"] is True,
            "operational": status["operational"] is True,
            "healthy_count": status["healthy_count"] == 3
        }

    @keyword("Trust Decay On Repeated Failures")
    def trust_decay_on_repeated_failures(self):
        """Agent trust decays when tasks repeatedly fail."""
        @dataclass
        class MockTrustTracker:
            trust_scores: Dict[str, float] = field(default_factory=dict)

            def record_failure(self, agent_id: str, decay_factor: float = 0.95):
                current = self.trust_scores.get(agent_id, 1.0)
                self.trust_scores[agent_id] = max(0.0, current * decay_factor)

            def get_trust(self, agent_id: str) -> float:
                return self.trust_scores.get(agent_id, 1.0)

        tracker = MockTrustTracker()
        tracker.trust_scores["AGENT-FAIL-1"] = 0.90

        for _ in range(3):
            tracker.record_failure("AGENT-FAIL-1", decay_factor=0.95)

        final_trust = tracker.get_trust("AGENT-FAIL-1")
        return {
            "below_original": final_trust < 0.80,
            "not_too_low": final_trust > 0.70
        }

    @keyword("Circuit Breaker On Service Failures")
    def circuit_breaker_on_service_failures(self):
        """Circuit breaker opens after repeated service failures."""
        @dataclass
        class MockCircuitBreaker:
            failures: int = 0
            threshold: int = 3
            state: str = "CLOSED"

            def record_failure(self):
                self.failures += 1
                if self.failures >= self.threshold:
                    self.state = "OPEN"

            def can_proceed(self) -> bool:
                return self.state == "CLOSED"

            def reset(self):
                self.failures = 0
                self.state = "CLOSED"

        breaker = MockCircuitBreaker(threshold=3)

        initial_ok = breaker.can_proceed()

        breaker.record_failure()
        breaker.record_failure()
        two_failures_ok = breaker.can_proceed()

        breaker.record_failure()
        three_failures_blocked = not breaker.can_proceed()
        state_open = breaker.state == "OPEN"

        breaker.reset()
        reset_ok = breaker.can_proceed()

        return {
            "initial_ok": initial_ok,
            "two_failures_ok": two_failures_ok,
            "three_failures_blocked": three_failures_blocked,
            "state_open": state_open,
            "reset_ok": reset_ok
        }
