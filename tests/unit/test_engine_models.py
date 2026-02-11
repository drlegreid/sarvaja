"""
Unit tests for Orchestrator Engine Models.

Per DOC-SIZE-01-v1: Tests for extracted engine_models.py module.
Tests: AgentRole, AgentInfo, DispatchResult.
"""

import pytest

from agent.orchestrator.engine_models import (
    AgentRole,
    AgentInfo,
    DispatchResult,
)


class TestAgentRole:
    """Tests for AgentRole enum."""

    def test_values(self):
        assert AgentRole.ORCHESTRATOR.value == "orchestrator"
        assert AgentRole.RESEARCH.value == "research"
        assert AgentRole.CODING.value == "coding"
        assert AgentRole.CURATOR.value == "curator"
        assert AgentRole.SYNC.value == "sync"

    def test_member_count(self):
        assert len(AgentRole) == 5


class TestAgentInfo:
    """Tests for AgentInfo dataclass."""

    def test_basic_creation(self):
        agent = AgentInfo(
            agent_id="code-agent",
            name="Code Agent",
            role=AgentRole.CODING,
            trust_score=0.85,
        )
        assert agent.agent_id == "code-agent"
        assert agent.name == "Code Agent"
        assert agent.role == AgentRole.CODING
        assert agent.trust_score == 0.85
        assert agent.status == "AVAILABLE"
        assert agent.current_task is None
        assert agent.tasks_completed == 0

    def test_trust_level_expert(self):
        agent = AgentInfo("a", "A", AgentRole.CODING, trust_score=0.95)
        assert agent.trust_level == "expert"

    def test_trust_level_expert_boundary(self):
        agent = AgentInfo("a", "A", AgentRole.CODING, trust_score=0.9)
        assert agent.trust_level == "expert"

    def test_trust_level_trusted(self):
        agent = AgentInfo("a", "A", AgentRole.RESEARCH, trust_score=0.75)
        assert agent.trust_level == "trusted"

    def test_trust_level_trusted_boundary(self):
        agent = AgentInfo("a", "A", AgentRole.RESEARCH, trust_score=0.7)
        assert agent.trust_level == "trusted"

    def test_trust_level_supervised(self):
        agent = AgentInfo("a", "A", AgentRole.SYNC, trust_score=0.6)
        assert agent.trust_level == "supervised"

    def test_trust_level_supervised_boundary(self):
        agent = AgentInfo("a", "A", AgentRole.SYNC, trust_score=0.5)
        assert agent.trust_level == "supervised"

    def test_trust_level_restricted(self):
        agent = AgentInfo("a", "A", AgentRole.CURATOR, trust_score=0.3)
        assert agent.trust_level == "restricted"

    def test_trust_level_zero(self):
        agent = AgentInfo("a", "A", AgentRole.CURATOR, trust_score=0.0)
        assert agent.trust_level == "restricted"

    def test_with_current_task(self):
        agent = AgentInfo(
            agent_id="research-agent",
            name="Research Agent",
            role=AgentRole.RESEARCH,
            trust_score=0.92,
            status="BUSY",
            current_task="TASK-abc123",
            tasks_completed=15,
        )
        assert agent.status == "BUSY"
        assert agent.current_task == "TASK-abc123"
        assert agent.tasks_completed == 15


class TestDispatchResult:
    """Tests for DispatchResult dataclass."""

    def test_success_result(self):
        result = DispatchResult(
            success=True,
            task_id="TASK-001",
            agent_id="code-agent",
            message="Dispatched successfully",
        )
        assert result.success is True
        assert result.task_id == "TASK-001"
        assert result.agent_id == "code-agent"
        assert result.requires_supervisor is False
        assert result.constraints_checked == []

    def test_failed_result(self):
        result = DispatchResult(
            success=False,
            message="No suitable agent",
        )
        assert result.success is False
        assert result.task_id is None
        assert result.agent_id is None

    def test_requires_supervisor(self):
        result = DispatchResult(
            success=True,
            task_id="TASK-002",
            agent_id="new-agent",
            requires_supervisor=True,
            constraints_checked=["trust_score >= 0.5", "role == CODING"],
        )
        assert result.requires_supervisor is True
        assert len(result.constraints_checked) == 2

    def test_constraints_default_not_shared(self):
        """Verify mutable default is not shared between instances."""
        r1 = DispatchResult(success=True)
        r2 = DispatchResult(success=True)
        r1.constraints_checked.append("test")
        assert r2.constraints_checked == []
