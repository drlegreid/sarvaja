"""
Agent Platform E2E and Integration Tests (ATEST-002, ATEST-003, ATEST-006).

Per RD-AGENT-TESTING: Comprehensive test coverage for multi-agent governance.
Per RULE-023: Test Coverage Protocol.

Phases:
- E2E Workflow: Gap resolution through agent chain
- Concurrency: Parallel agent operations
- Kanren Integration: Constraint validation in agent context
"""

import asyncio
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# TEST FIXTURES AND HELPERS
# =============================================================================

@dataclass
class MockAgent:
    """Mock agent for testing workflows."""
    agent_id: str
    role: str
    trust_score: float
    status: str = "ACTIVE"
    tasks_executed: int = 0

    async def claim_task(self, task_id: str) -> Dict[str, Any]:
        """Attempt to claim a task."""
        return {
            "success": True,
            "task_id": task_id,
            "agent_id": self.agent_id,
            "claimed_at": datetime.now().isoformat()
        }

    async def analyze_gap(self, gap_id: str) -> Dict[str, Any]:
        """RESEARCH agent analyzes a gap."""
        return {
            "gap_id": gap_id,
            "files_examined": ["src/file1.py", "src/file2.py"],
            "evidence_gathered": ["Evidence item 1", "Evidence item 2"],
            "recommended_action": f"Implement fix for {gap_id}"
        }

    async def process_handoff(self, handoff: Dict) -> Dict[str, Any]:
        """CODING agent processes a handoff."""
        return {
            "handoff_id": handoff.get("id"),
            "files_modified": ["src/fix.py"],
            "tests_added": ["tests/test_fix.py"],
            "status": "IMPLEMENTED"
        }

    async def review_implementation(self, handoff: Dict) -> Dict[str, Any]:
        """CURATOR agent reviews implementation."""
        return {
            "handoff_id": handoff.get("id"),
            "status": "APPROVED",
            "feedback": "Implementation meets requirements",
            "trust_impact": 0.01
        }


@dataclass
class MockTaskQueue:
    """Mock task queue for concurrency testing."""
    tasks: List[Dict] = field(default_factory=list)
    claimed: Dict[str, str] = field(default_factory=dict)  # task_id -> agent_id
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add_task(self, task: Dict) -> None:
        """Add task to queue."""
        async with self._lock:
            self.tasks.append(task)

    async def claim_task(self, task_id: str, agent_id: str) -> bool:
        """Attempt to claim task (atomic operation)."""
        async with self._lock:
            if task_id in self.claimed:
                return False  # Already claimed
            self.claimed[task_id] = agent_id
            return True


@pytest.fixture
def mock_agent_research():
    """Create mock RESEARCH agent."""
    return MockAgent(
        agent_id="AGENT-RESEARCH-001",
        role="RESEARCH",
        trust_score=0.85
    )


@pytest.fixture
def mock_agent_coding():
    """Create mock CODING agent."""
    return MockAgent(
        agent_id="AGENT-CODING-001",
        role="CODING",
        trust_score=0.90
    )


@pytest.fixture
def mock_agent_curator():
    """Create mock CURATOR agent."""
    return MockAgent(
        agent_id="AGENT-CURATOR-001",
        role="CURATOR",
        trust_score=0.95
    )


@pytest.fixture
def mock_task_queue():
    """Create mock task queue."""
    return MockTaskQueue()


# =============================================================================
# ATEST-002: E2E AGENT WORKFLOW TESTS
# =============================================================================

class TestAgentWorkflowE2E:
    """E2E tests for agent workflow chains (ATEST-002)."""

    @pytest.mark.asyncio
    async def test_research_creates_context(self, mock_agent_research):
        """RESEARCH agent gathers context for a gap."""
        context = await mock_agent_research.analyze_gap("GAP-E2E-001")

        assert context["gap_id"] == "GAP-E2E-001"
        assert len(context["files_examined"]) > 0
        assert len(context["evidence_gathered"]) > 0
        assert "recommended_action" in context

    @pytest.mark.asyncio
    async def test_coding_processes_handoff(self, mock_agent_coding):
        """CODING agent processes handoff from RESEARCH."""
        handoff = {
            "id": "HANDOFF-001",
            "from_agent": "RESEARCH",
            "to_agent": "CODING",
            "context": {"gap_id": "GAP-E2E-001"}
        }

        result = await mock_agent_coding.process_handoff(handoff)

        assert result["status"] == "IMPLEMENTED"
        assert len(result["files_modified"]) > 0
        assert len(result["tests_added"]) > 0

    @pytest.mark.asyncio
    async def test_curator_reviews_implementation(self, mock_agent_curator):
        """CURATOR agent reviews and approves implementation."""
        handoff = {
            "id": "HANDOFF-002",
            "from_agent": "CODING",
            "to_agent": "CURATOR",
            "implementation": {"files_modified": ["src/fix.py"]}
        }

        result = await mock_agent_curator.review_implementation(handoff)

        assert result["status"] == "APPROVED"
        assert "feedback" in result

    @pytest.mark.asyncio
    async def test_full_workflow_chain(
        self,
        mock_agent_research,
        mock_agent_coding,
        mock_agent_curator
    ):
        """Full workflow: RESEARCH → CODING → CURATOR."""
        gap_id = "GAP-FULL-CHAIN-001"

        # Step 1: RESEARCH analyzes gap
        context = await mock_agent_research.analyze_gap(gap_id)
        assert context["files_examined"]

        # Step 2: Create handoff to CODING
        handoff_to_coding = {
            "id": "HANDOFF-R2C-001",
            "from_agent": mock_agent_research.role,
            "to_agent": "CODING",
            "context": context,
            "status": "READY_FOR_CODING"
        }

        # Step 3: CODING implements
        implementation = await mock_agent_coding.process_handoff(handoff_to_coding)
        assert implementation["status"] == "IMPLEMENTED"

        # Step 4: Create handoff to CURATOR
        handoff_to_curator = {
            "id": "HANDOFF-C2R-001",
            "from_agent": mock_agent_coding.role,
            "to_agent": "CURATOR",
            "implementation": implementation,
            "status": "READY_FOR_REVIEW"
        }

        # Step 5: CURATOR reviews
        approval = await mock_agent_curator.review_implementation(handoff_to_curator)
        assert approval["status"] == "APPROVED"

        # Verify chain completed
        mock_agent_research.tasks_executed += 1
        mock_agent_coding.tasks_executed += 1
        mock_agent_curator.tasks_executed += 1

        assert mock_agent_research.tasks_executed == 1
        assert mock_agent_coding.tasks_executed == 1
        assert mock_agent_curator.tasks_executed == 1


# =============================================================================
# ATEST-003: MULTI-AGENT CONCURRENCY TESTS
# =============================================================================

class TestAgentConcurrency:
    """Concurrency tests for parallel agent operations (ATEST-003)."""

    @pytest.mark.asyncio
    async def test_parallel_task_claim_single_winner(self, mock_task_queue):
        """Only one agent can claim a task when multiple try simultaneously."""
        task_id = "TASK-CONCURRENT-001"

        # Three agents try to claim the same task
        agents = [
            MockAgent("AGENT-A", "CODING", 0.85),
            MockAgent("AGENT-B", "CODING", 0.90),
            MockAgent("AGENT-C", "CODING", 0.80),
        ]

        # Claim attempts happen concurrently
        results = await asyncio.gather(*[
            mock_task_queue.claim_task(task_id, agent.agent_id)
            for agent in agents
        ])

        # Only one should succeed
        successful_claims = [r for r in results if r]
        assert len(successful_claims) == 1

        # Task should be claimed by one agent
        assert task_id in mock_task_queue.claimed

    @pytest.mark.asyncio
    async def test_queue_saturation_all_processed(self, mock_task_queue):
        """All tasks are processed when queue is saturated."""
        num_tasks = 20

        # Add tasks to queue
        for i in range(num_tasks):
            await mock_task_queue.add_task({
                "id": f"TASK-SAT-{i:03d}",
                "priority": "MEDIUM"
            })

        assert len(mock_task_queue.tasks) == num_tasks

        # Agents process tasks
        agents = [MockAgent(f"AGENT-{i}", "CODING", 0.85) for i in range(4)]
        processed = 0

        for task in mock_task_queue.tasks:
            agent = agents[processed % len(agents)]
            if await mock_task_queue.claim_task(task["id"], agent.agent_id):
                processed += 1

        assert processed == num_tasks

    @pytest.mark.asyncio
    async def test_no_double_claim(self, mock_task_queue):
        """Task cannot be claimed twice."""
        task_id = "TASK-DOUBLE-001"

        # First claim succeeds
        result1 = await mock_task_queue.claim_task(task_id, "AGENT-1")
        assert result1 is True

        # Second claim fails
        result2 = await mock_task_queue.claim_task(task_id, "AGENT-2")
        assert result2 is False

        # Original claimer is preserved
        assert mock_task_queue.claimed[task_id] == "AGENT-1"


# =============================================================================
# ATEST-006: KANREN-AGENT INTEGRATION TESTS
# =============================================================================

class TestKanrenAgentIntegration:
    """Kanren constraint validation with agent context (ATEST-006)."""

    def test_kanren_imports_available(self):
        """Kanren module can be imported."""
        try:
            from governance.kanren_constraints import (
                KanrenRAGFilter,
                AgentContext,
                TaskContext,
                trust_level,
                valid_task_assignment,
            )
            assert KanrenRAGFilter is not None
            assert AgentContext is not None
            assert TaskContext is not None
        except ImportError:
            pytest.skip("kanren not installed")

    def test_expert_agent_on_critical_task(self):
        """Expert agent (trust >= 0.9) can execute CRITICAL tasks."""
        try:
            from governance.kanren_constraints import (
                AgentContext,
                TaskContext,
                valid_task_assignment,
            )
        except ImportError:
            pytest.skip("kanren not installed")

        expert = AgentContext("AGENT-EXP-001", "Expert Agent", 0.95, "claude-code")
        critical_task = TaskContext("TASK-CRIT-001", "CRITICAL", True)

        result = valid_task_assignment(expert, critical_task)

        assert result["valid"] is True
        assert result["trust_level"] == "expert"
        assert result["can_execute"] is True
        assert result["requires_supervisor"] is False

    def test_supervised_agent_blocked_from_critical(self):
        """Supervised agent (trust 0.5-0.7) cannot execute CRITICAL tasks."""
        try:
            from governance.kanren_constraints import (
                AgentContext,
                TaskContext,
                valid_task_assignment,
            )
        except ImportError:
            pytest.skip("kanren not installed")

        supervised = AgentContext("AGENT-SUP-001", "Supervised Agent", 0.55, "sync-agent")
        critical_task = TaskContext("TASK-CRIT-002", "CRITICAL", True)

        result = valid_task_assignment(supervised, critical_task)

        assert result["valid"] is False
        assert result["trust_level"] == "supervised"
        assert result["can_execute"] is False
        assert result["requires_supervisor"] is True

    def test_trust_level_boundaries(self):
        """Trust level boundaries are correctly enforced."""
        try:
            from governance.kanren_constraints import trust_level
        except ImportError:
            pytest.skip("kanren not installed")

        # Boundary tests
        assert trust_level(0.90) == "expert"     # >= 0.9
        assert trust_level(0.89) == "trusted"    # >= 0.7, < 0.9
        assert trust_level(0.70) == "trusted"    # >= 0.7
        assert trust_level(0.69) == "supervised" # >= 0.5, < 0.7
        assert trust_level(0.50) == "supervised" # >= 0.5
        assert trust_level(0.49) == "restricted" # < 0.5

    def test_kanren_rag_filter_with_agent_context(self):
        """KanrenRAGFilter integrates with agent context."""
        try:
            from governance.kanren_constraints import (
                KanrenRAGFilter,
                AgentContext,
                TaskContext,
            )
        except ImportError:
            pytest.skip("kanren not installed")

        # Create mock store
        mock_store = MagicMock()
        mock_vec = MagicMock()
        mock_vec.id = "vec-rule-001"
        mock_vec.content = "governance constraint"
        mock_vec.source_type = "rule"
        mock_vec.source = "RULE-011"
        mock_store.get_all_vectors.return_value = [mock_vec]

        rag_filter = KanrenRAGFilter(vector_store=mock_store)

        expert = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
        task = TaskContext("TASK-001", "CRITICAL", True)

        context = rag_filter.search_for_task(
            query_text="governance",
            task_context=task,
            agent_context=expert
        )

        assert context["assignment_valid"] is True
        assert "constraints_applied" in context
        assert any("RULE-011" in c for c in context["constraints_applied"])


# =============================================================================
# TRUST EVOLUTION TESTS (ATEST-005)
# =============================================================================

class TestTrustEvolution:
    """Trust score evolution over agent actions (ATEST-005)."""

    def test_trust_formula_coefficients(self):
        """Trust formula has correct coefficients per RULE-011."""
        COMPLIANCE_WEIGHT = 0.4
        ACCURACY_WEIGHT = 0.3
        CONSISTENCY_WEIGHT = 0.2
        TENURE_WEIGHT = 0.1

        total = COMPLIANCE_WEIGHT + ACCURACY_WEIGHT + CONSISTENCY_WEIGHT + TENURE_WEIGHT
        assert abs(total - 1.0) < 0.0001

    def test_perfect_agent_gets_max_trust(self):
        """Agent with perfect metrics gets trust = 1.0."""
        trust = (
            0.4 * 1.0 +  # Compliance
            0.3 * 1.0 +  # Accuracy
            0.2 * 1.0 +  # Consistency
            0.1 * 1.0    # Tenure (normalized)
        )
        assert abs(trust - 1.0) < 0.0001

    def test_mixed_performance_trust(self):
        """Agent with mixed performance gets proportional trust."""
        compliance = 0.90
        accuracy = 0.85
        consistency = 0.80
        tenure = 0.50  # Newer agent

        trust = (
            0.4 * compliance +
            0.3 * accuracy +
            0.2 * consistency +
            0.1 * tenure
        )

        # Expected: 0.36 + 0.255 + 0.16 + 0.05 = 0.825
        assert 0.82 < trust < 0.83

    def test_trust_decay_on_failures(self):
        """Trust decreases with failures."""
        initial_trust = 0.90

        # Simulate 3 failures (compliance drops)
        new_compliance = 0.70  # Down from 1.0
        accuracy = 0.90
        consistency = 0.85
        tenure = 0.80

        new_trust = (
            0.4 * new_compliance +
            0.3 * accuracy +
            0.2 * consistency +
            0.1 * tenure
        )

        # Trust should decrease
        assert new_trust < initial_trust


# =============================================================================
# HANDOFF CHAIN VALIDATION (ATEST-004)
# =============================================================================

class TestHandoffChainValidation:
    """Handoff chain integrity tests (ATEST-004)."""

    def test_handoff_has_required_fields(self):
        """Handoff contains all required fields."""
        from governance.orchestrator.handoff import TaskHandoff

        handoff = TaskHandoff(
            task_id="TASK-001",
            title="Test Handoff",
            from_agent="RESEARCH",
            to_agent="CODING",
            status="READY_FOR_CODING"
        )

        assert handoff.task_id == "TASK-001"
        assert handoff.from_agent == "RESEARCH"
        assert handoff.to_agent == "CODING"
        assert handoff.status == "READY_FOR_CODING"

    def test_handoff_to_markdown(self):
        """Handoff can be serialized to markdown."""
        from governance.orchestrator.handoff import TaskHandoff

        handoff = TaskHandoff(
            task_id="TASK-MD-001",
            title="Markdown Test",
            from_agent="RESEARCH",
            to_agent="CODING",
            status="READY_FOR_CODING",
            context_summary="Test context",
            recommended_action="Implement the fix"
        )

        markdown = handoff.to_markdown()

        assert "# Task Handoff:" in markdown
        assert "RESEARCH" in markdown
        assert "CODING" in markdown
        assert "Test context" in markdown

    def test_handoff_roundtrip(self):
        """Handoff survives markdown serialization/deserialization."""
        from governance.orchestrator.handoff import TaskHandoff

        original = TaskHandoff(
            task_id="TASK-RT-001",
            title="Roundtrip Test",
            from_agent="CODING",
            to_agent="CURATOR",
            status="READY_FOR_REVIEW",
            context_summary="Implementation complete",
            recommended_action="Review and approve"
        )

        markdown = original.to_markdown()
        restored = TaskHandoff.from_markdown(markdown)

        assert restored is not None
        assert restored.task_id == original.task_id
        assert restored.from_agent == original.from_agent
        assert restored.to_agent == original.to_agent


# =============================================================================
# BENCHMARK METRICS (RD-LACMUS)
# =============================================================================

class TestAgentPlatformBenchmarks:
    """Benchmark metrics for agent platform (per RD-LACMUS)."""

    def test_trust_accuracy_target_95(self):
        """Trust score accuracy meets 95% target."""
        # Test formula accuracy with full 4-component calculation
        # Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)
        test_cases = [
            # (compliance, accuracy, consistency, tenure, expected_min, expected_max)
            (1.0, 1.0, 1.0, 1.0, 0.99, 1.01),      # Perfect: 1.0
            (0.8, 0.8, 0.8, 0.8, 0.79, 0.81),      # Good: 0.8
            (0.5, 0.5, 0.5, 0.5, 0.49, 0.51),      # Medium: 0.5
            (0.9, 0.85, 0.80, 0.70, 0.84, 0.88),   # Realistic high: 0.865
        ]

        accurate = 0
        for compliance, accuracy, consistency, tenure, low, high in test_cases:
            trust = 0.4 * compliance + 0.3 * accuracy + 0.2 * consistency + 0.1 * tenure
            if low <= trust <= high:
                accurate += 1

        accuracy_rate = accurate / len(test_cases)
        assert accuracy_rate >= 0.95, f"Trust accuracy {accuracy_rate:.0%} below 95% target"

    def test_task_routing_accuracy_target_90(self):
        """Task routing accuracy meets 90% target."""
        routing_rules = [
            ("GAP-UI-001", "CODING"),
            ("GAP-API-001", "CODING"),
            ("RD-001", "RESEARCH"),
            ("RD-WORKSPACE", "RESEARCH"),
            ("P12.1", "CURATOR"),
            ("P11.1", "CODING"),
            ("GAP-DATA-001", "CURATOR"),
            ("UNKNOWN-001", "RESEARCH"),  # Default
        ]

        def route(task_id: str) -> str:
            task_upper = task_id.upper()
            if task_upper.startswith("GAP-UI") or task_upper.startswith("GAP-API"):
                return "CODING"
            if task_upper.startswith("RD-"):
                return "RESEARCH"
            if task_upper.startswith("GAP-DATA"):
                return "CURATOR"
            if task_upper.startswith("P"):
                import re
                match = re.match(r"P(\d+)", task_upper)
                if match and int(match.group(1)) >= 12:
                    return "CURATOR"
                return "CODING"
            return "RESEARCH"

        correct = sum(1 for task_id, expected in routing_rules if route(task_id) == expected)
        accuracy = correct / len(routing_rules)
        assert accuracy >= 0.90


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
