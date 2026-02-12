"""
Unit tests for Delegation Convenience Methods.

Per DOC-SIZE-01-v1: Tests for agent/orchestrator/delegation_shortcuts.py module.
Tests: DelegationShortcutsMixin — delegate_research, delegate_implementation,
       delegate_validation, escalate; Factory functions — create_delegation_context,
       create_research_request, create_implementation_request.
"""

from unittest.mock import MagicMock, AsyncMock

import pytest

from agent.orchestrator.delegation_shortcuts import (
    DelegationShortcutsMixin,
    create_delegation_context,
    create_research_request,
    create_implementation_request,
)
from agent.orchestrator.delegation_models import (
    DelegationResult,
    DelegationType,
    DelegationPriority,
)
from agent.orchestrator.engine import AgentRole


class _TestDelegator(DelegationShortcutsMixin):
    """Concrete class for testing mixin methods."""

    def __init__(self):
        self.delegate = AsyncMock(return_value=DelegationResult(
            success=True,
            delegation_id="DEL-TEST",
            task_id="T-1",
            source_agent_id="agent-1",
            target_agent_id="agent-2",
            message="OK",
        ))


# ── delegate_research ──────────────────────────────────────────


class TestDelegateResearch:
    @pytest.mark.asyncio
    async def test_creates_research_request(self):
        d = _TestDelegator()
        result = await d.delegate_research("T-1", "agent-1", "Find docs")
        assert result.success is True
        d.delegate.assert_called_once()
        req = d.delegate.call_args[0][0]
        assert req.delegation_type == DelegationType.RESEARCH
        assert req.target_role == AgentRole.RESEARCH
        assert req.task_id == "T-1"

    @pytest.mark.asyncio
    async def test_with_context(self):
        d = _TestDelegator()
        ctx = {"key": "value"}
        await d.delegate_research("T-1", "agent-1", "Query", gathered_context=ctx)
        req = d.delegate.call_args[0][0]
        assert req.context.gathered_context == ctx

    @pytest.mark.asyncio
    async def test_default_empty_context(self):
        d = _TestDelegator()
        await d.delegate_research("T-1", "agent-1", "Query")
        req = d.delegate.call_args[0][0]
        assert req.context.gathered_context == {}


# ── delegate_implementation ────────────────────────────────────


class TestDelegateImplementation:
    @pytest.mark.asyncio
    async def test_creates_impl_request(self):
        d = _TestDelegator()
        result = await d.delegate_implementation("T-1", "agent-1", "Build it")
        assert result.success is True
        req = d.delegate.call_args[0][0]
        assert req.delegation_type == DelegationType.IMPLEMENTATION
        assert req.target_role == AgentRole.CODING

    @pytest.mark.asyncio
    async def test_with_constraints(self):
        d = _TestDelegator()
        await d.delegate_implementation(
            "T-1", "agent-1", "Build",
            constraints=["No ORM", "Use async"],
        )
        req = d.delegate.call_args[0][0]
        assert req.context.constraints == ["No ORM", "Use async"]


# ── delegate_validation ────────────────────────────────────────


class TestDelegateValidation:
    @pytest.mark.asyncio
    async def test_creates_validation_request(self):
        d = _TestDelegator()
        item = {"rule_id": "R-1", "content": "rule text"}
        result = await d.delegate_validation("T-1", "agent-1", item)
        assert result.success is True
        req = d.delegate.call_args[0][0]
        assert req.delegation_type == DelegationType.VALIDATION
        assert req.target_role == AgentRole.CURATOR
        assert req.context.gathered_context["item"] == item

    @pytest.mark.asyncio
    async def test_with_rules(self):
        d = _TestDelegator()
        await d.delegate_validation("T-1", "agent-1", {}, rules=["RULE-011"])
        req = d.delegate.call_args[0][0]
        assert req.context.constraints == ["RULE-011"]


# ── escalate ───────────────────────────────────────────────────


class TestEscalate:
    @pytest.mark.asyncio
    async def test_creates_escalation(self):
        d = _TestDelegator()
        result = await d.escalate("T-1", "agent-1", "Can't handle this")
        assert result.success is True
        req = d.delegate.call_args[0][0]
        assert req.delegation_type == DelegationType.ESCALATION
        assert req.target_role == AgentRole.ORCHESTRATOR
        assert "ESCALATION" in req.context.task_description

    @pytest.mark.asyncio
    async def test_escalation_high_priority(self):
        d = _TestDelegator()
        await d.escalate("T-1", "agent-1", "Critical issue")
        req = d.delegate.call_args[0][0]
        assert req.context.priority == DelegationPriority.HIGH


# ── create_delegation_context ──────────────────────────────────


class TestCreateDelegationContext:
    def test_auto_id(self):
        ctx = create_delegation_context("T-1", "agent-1", "Do stuff")
        assert ctx.delegation_id.startswith("DEL-")
        assert ctx.task_id == "T-1"
        assert ctx.source_agent_id == "agent-1"
        assert ctx.task_description == "Do stuff"

    def test_unique_ids(self):
        c1 = create_delegation_context("T-1", "a1", "d1")
        c2 = create_delegation_context("T-1", "a1", "d1")
        assert c1.delegation_id != c2.delegation_id


# ── create_research_request ────────────────────────────────────


class TestCreateResearchRequest:
    def test_creates_request(self):
        req = create_research_request("T-1", "agent-1", "Find info")
        assert req.delegation_type == DelegationType.RESEARCH
        assert req.target_role == AgentRole.RESEARCH
        assert req.task_id == "T-1"
        assert req.context.task_description == "Find info"


# ── create_implementation_request ──────────────────────────────


class TestCreateImplementationRequest:
    def test_creates_request(self):
        req = create_implementation_request("T-1", "agent-1", "Build feature")
        assert req.delegation_type == DelegationType.IMPLEMENTATION
        assert req.target_role == AgentRole.CODING

    def test_with_context(self):
        req = create_implementation_request(
            "T-1", "agent-1", "Build", context={"spec": "v2"},
        )
        assert req.context.gathered_context == {"spec": "v2"}
