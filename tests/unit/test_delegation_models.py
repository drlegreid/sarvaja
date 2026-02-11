"""
Unit tests for Delegation Protocol Models.

Per DOC-SIZE-01-v1: Tests for extracted delegation_models.py module.
Tests: DelegationType, DelegationPriority, DelegationContext,
       DelegationRequest, DelegationResult.
"""

import pytest

from agent.orchestrator.delegation_models import (
    DelegationType,
    DelegationPriority,
    DelegationContext,
    DelegationRequest,
    DelegationResult,
)
from agent.orchestrator.engine_models import AgentRole


class TestDelegationType:
    """Tests for DelegationType enum."""

    def test_values(self):
        assert DelegationType.RESEARCH.value == "research"
        assert DelegationType.IMPLEMENTATION.value == "impl"
        assert DelegationType.REVIEW.value == "review"
        assert DelegationType.ESCALATION.value == "escalation"
        assert DelegationType.VALIDATION.value == "validation"
        assert DelegationType.SYNC.value == "sync"

    def test_member_count(self):
        assert len(DelegationType) == 6


class TestDelegationPriority:
    """Tests for DelegationPriority enum."""

    def test_values(self):
        assert DelegationPriority.CRITICAL.value == 1
        assert DelegationPriority.HIGH.value == 2
        assert DelegationPriority.MEDIUM.value == 3
        assert DelegationPriority.LOW.value == 4

    def test_ordering(self):
        assert DelegationPriority.CRITICAL.value < DelegationPriority.HIGH.value
        assert DelegationPriority.HIGH.value < DelegationPriority.MEDIUM.value
        assert DelegationPriority.MEDIUM.value < DelegationPriority.LOW.value


class TestDelegationContext:
    """Tests for DelegationContext dataclass."""

    def _make_context(self, **overrides):
        defaults = {
            "delegation_id": "DEL-001",
            "task_id": "TASK-001",
            "source_agent_id": "code-agent",
            "task_description": "Research API patterns",
        }
        defaults.update(overrides)
        return DelegationContext(**defaults)

    def test_basic_creation(self):
        ctx = self._make_context()
        assert ctx.delegation_id == "DEL-001"
        assert ctx.task_id == "TASK-001"
        assert ctx.source_agent_id == "code-agent"
        assert ctx.task_description == "Research API patterns"
        assert ctx.gathered_context == {}
        assert ctx.constraints == []
        assert ctx.evidence == []
        assert ctx.deadline is None
        assert ctx.priority == DelegationPriority.MEDIUM
        assert ctx.min_trust_score == 0.5
        assert ctx.requires_supervisor is False

    def test_created_at_auto_populated(self):
        ctx = self._make_context()
        assert ctx.created_at is not None
        assert len(ctx.created_at) > 10  # ISO format

    def test_to_dict(self):
        ctx = self._make_context(
            gathered_context={"key": "value"},
            constraints=["trust >= 0.7"],
            priority=DelegationPriority.HIGH,
        )
        d = ctx.to_dict()
        assert d["delegation_id"] == "DEL-001"
        assert d["task_id"] == "TASK-001"
        assert d["gathered_context"] == {"key": "value"}
        assert d["constraints"] == ["trust >= 0.7"]
        assert d["priority"] == "HIGH"
        assert d["min_trust_score"] == 0.5

    def test_from_dict_basic(self):
        data = {
            "delegation_id": "DEL-002",
            "task_id": "TASK-002",
            "source_agent_id": "research-agent",
            "task_description": "Implement feature X",
        }
        ctx = DelegationContext.from_dict(data)
        assert ctx.delegation_id == "DEL-002"
        assert ctx.task_id == "TASK-002"
        assert ctx.priority == DelegationPriority.MEDIUM
        assert ctx.min_trust_score == 0.5

    def test_from_dict_with_priority_string(self):
        data = {
            "delegation_id": "DEL-003",
            "task_id": "TASK-003",
            "source_agent_id": "code-agent",
            "task_description": "Critical fix",
            "priority": "CRITICAL",
        }
        ctx = DelegationContext.from_dict(data)
        assert ctx.priority == DelegationPriority.CRITICAL

    def test_from_dict_with_all_fields(self):
        data = {
            "delegation_id": "DEL-004",
            "task_id": "TASK-004",
            "source_agent_id": "code-agent",
            "task_description": "Full delegation",
            "gathered_context": {"files": ["a.py"]},
            "constraints": ["no breaking changes"],
            "evidence": ["evidence/e1.md"],
            "deadline": "2026-02-12T00:00:00",
            "priority": "HIGH",
            "min_trust_score": 0.8,
            "requires_supervisor": True,
        }
        ctx = DelegationContext.from_dict(data)
        assert ctx.gathered_context == {"files": ["a.py"]}
        assert ctx.constraints == ["no breaking changes"]
        assert ctx.evidence == ["evidence/e1.md"]
        assert ctx.deadline == "2026-02-12T00:00:00"
        assert ctx.priority == DelegationPriority.HIGH
        assert ctx.min_trust_score == 0.8
        assert ctx.requires_supervisor is True

    def test_roundtrip(self):
        ctx = self._make_context(
            gathered_context={"refs": [1, 2]},
            constraints=["c1", "c2"],
            evidence=["e1"],
            priority=DelegationPriority.LOW,
            min_trust_score=0.3,
            requires_supervisor=True,
        )
        d = ctx.to_dict()
        restored = DelegationContext.from_dict(d)
        assert restored.delegation_id == ctx.delegation_id
        assert restored.task_id == ctx.task_id
        assert restored.source_agent_id == ctx.source_agent_id
        assert restored.priority == ctx.priority
        assert restored.min_trust_score == ctx.min_trust_score
        assert restored.requires_supervisor == ctx.requires_supervisor
        assert restored.gathered_context == ctx.gathered_context
        assert restored.constraints == ctx.constraints


class TestDelegationRequest:
    """Tests for DelegationRequest dataclass."""

    def test_basic_creation(self):
        ctx = DelegationContext(
            delegation_id="DEL-010",
            task_id="TASK-010",
            source_agent_id="code-agent",
            task_description="Test",
        )
        req = DelegationRequest(
            task_id="TASK-010",
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=ctx,
        )
        assert req.task_id == "TASK-010"
        assert req.delegation_type == DelegationType.RESEARCH
        assert req.target_role == AgentRole.RESEARCH
        assert req.target_agent_id is None
        assert req.on_complete is None

    def test_request_id_auto_generated(self):
        ctx = DelegationContext("D", "T", "A", "desc")
        req = DelegationRequest("T", DelegationType.REVIEW, AgentRole.CURATOR, ctx)
        assert req.request_id.startswith("DEL-")
        assert len(req.request_id) == 12  # DEL- + 8 hex chars

    def test_requested_at_auto_populated(self):
        ctx = DelegationContext("D", "T", "A", "desc")
        req = DelegationRequest("T", DelegationType.SYNC, AgentRole.SYNC, ctx)
        assert req.requested_at is not None

    def test_with_target_agent(self):
        ctx = DelegationContext("D", "T", "A", "desc")
        req = DelegationRequest(
            task_id="T",
            delegation_type=DelegationType.IMPLEMENTATION,
            target_role=AgentRole.CODING,
            context=ctx,
            target_agent_id="code-agent",
        )
        assert req.target_agent_id == "code-agent"


class TestDelegationResult:
    """Tests for DelegationResult dataclass."""

    def test_success_result(self):
        result = DelegationResult(
            success=True,
            delegation_id="DEL-020",
            task_id="TASK-020",
            source_agent_id="code-agent",
            target_agent_id="research-agent",
            result_data={"findings": ["f1"]},
            message="Completed research",
            duration_ms=150,
        )
        assert result.success is True
        assert result.delegation_id == "DEL-020"
        assert result.result_data == {"findings": ["f1"]}
        assert result.duration_ms == 150
        assert result.needs_followup is False
        assert result.followup_type is None

    def test_result_with_followup(self):
        result = DelegationResult(
            success=True,
            delegation_id="DEL-021",
            task_id="TASK-021",
            source_agent_id="code-agent",
            target_agent_id="research-agent",
            needs_followup=True,
            followup_type=DelegationType.IMPLEMENTATION,
            followup_context={"implement": "feature_x"},
        )
        assert result.needs_followup is True
        assert result.followup_type == DelegationType.IMPLEMENTATION
        assert result.followup_context["implement"] == "feature_x"

    def test_defaults(self):
        result = DelegationResult(
            success=False,
            delegation_id="D",
            task_id="T",
            source_agent_id="A",
            target_agent_id="B",
        )
        assert result.result_data == {}
        assert result.evidence == []
        assert result.message == ""
        assert result.duration_ms == 0
        assert result.needs_followup is False

    def test_completed_at_auto_populated(self):
        result = DelegationResult(
            success=True, delegation_id="D", task_id="T",
            source_agent_id="A", target_agent_id="B",
        )
        assert result.completed_at is not None
