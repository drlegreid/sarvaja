"""
Tests for Agent Delegation Protocol (ORCH-004).

Per RULE-023: Test Coverage Protocol
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from agent.orchestrator.delegation import (
    DelegationType,
    DelegationPriority,
    DelegationContext,
    DelegationRequest,
    DelegationResult,
    DelegationProtocol,
    create_delegation_context,
    create_research_request,
    create_implementation_request,
)
from agent.orchestrator.engine import AgentInfo, AgentRole


# =============================================================================
# DelegationType Tests
# =============================================================================

class TestDelegationType:
    """Test DelegationType enum."""

    def test_research_type(self):
        """RESEARCH type for context gathering."""
        assert DelegationType.RESEARCH.value == "research"

    def test_implementation_type(self):
        """IMPLEMENTATION type for coding tasks."""
        assert DelegationType.IMPLEMENTATION.value == "impl"

    def test_validation_type(self):
        """VALIDATION type for rule checking."""
        assert DelegationType.VALIDATION.value == "validation"

    def test_escalation_type(self):
        """ESCALATION type for authority escalation."""
        assert DelegationType.ESCALATION.value == "escalation"


# =============================================================================
# DelegationPriority Tests
# =============================================================================

class TestDelegationPriority:
    """Test DelegationPriority enum."""

    def test_priority_ordering(self):
        """CRITICAL < HIGH < MEDIUM < LOW."""
        assert DelegationPriority.CRITICAL.value < DelegationPriority.HIGH.value
        assert DelegationPriority.HIGH.value < DelegationPriority.MEDIUM.value
        assert DelegationPriority.MEDIUM.value < DelegationPriority.LOW.value

    def test_critical_is_1(self):
        """CRITICAL has value 1."""
        assert DelegationPriority.CRITICAL.value == 1


# =============================================================================
# DelegationContext Tests
# =============================================================================

class TestDelegationContext:
    """Test DelegationContext dataclass."""

    def test_basic_creation(self):
        """Create basic delegation context."""
        ctx = DelegationContext(
            delegation_id="DEL-001",
            task_id="TASK-001",
            source_agent_id="AGENT-001",
            task_description="Research authentication patterns",
        )

        assert ctx.delegation_id == "DEL-001"
        assert ctx.task_id == "TASK-001"
        assert ctx.source_agent_id == "AGENT-001"
        assert ctx.priority == DelegationPriority.MEDIUM  # Default

    def test_context_with_constraints(self):
        """Create context with constraints."""
        ctx = DelegationContext(
            delegation_id="DEL-002",
            task_id="TASK-002",
            source_agent_id="AGENT-001",
            task_description="Implement feature",
            constraints=["No external deps", "Must be async"],
        )

        assert len(ctx.constraints) == 2
        assert "No external deps" in ctx.constraints

    def test_context_with_evidence(self):
        """Create context with evidence."""
        ctx = DelegationContext(
            delegation_id="DEL-003",
            task_id="TASK-003",
            source_agent_id="AGENT-001",
            task_description="Review code",
            evidence=["tests/test_auth.py passed", "No lint errors"],
        )

        assert len(ctx.evidence) == 2

    def test_to_dict(self):
        """Convert context to dictionary."""
        ctx = DelegationContext(
            delegation_id="DEL-004",
            task_id="TASK-004",
            source_agent_id="AGENT-001",
            task_description="Test task",
            priority=DelegationPriority.HIGH,
        )

        d = ctx.to_dict()
        assert d["delegation_id"] == "DEL-004"
        assert d["priority"] == "HIGH"
        assert "created_at" in d

    def test_from_dict(self):
        """Create context from dictionary."""
        data = {
            "delegation_id": "DEL-005",
            "task_id": "TASK-005",
            "source_agent_id": "AGENT-002",
            "task_description": "From dict",
            "priority": "CRITICAL",
            "min_trust_score": 0.8,
        }

        ctx = DelegationContext.from_dict(data)
        assert ctx.delegation_id == "DEL-005"
        assert ctx.priority == DelegationPriority.CRITICAL
        assert ctx.min_trust_score == 0.8

    def test_min_trust_default(self):
        """Default min_trust_score is 0.5."""
        ctx = DelegationContext(
            delegation_id="DEL-006",
            task_id="TASK-006",
            source_agent_id="AGENT-001",
            task_description="Test",
        )
        assert ctx.min_trust_score == 0.5


# =============================================================================
# DelegationRequest Tests
# =============================================================================

class TestDelegationRequest:
    """Test DelegationRequest dataclass."""

    def test_basic_request(self):
        """Create basic delegation request."""
        ctx = DelegationContext(
            delegation_id="DEL-010",
            task_id="TASK-010",
            source_agent_id="AGENT-001",
            task_description="Research task",
        )

        request = DelegationRequest(
            task_id="TASK-010",
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=ctx,
        )

        assert request.task_id == "TASK-010"
        assert request.delegation_type == DelegationType.RESEARCH
        assert request.target_agent_id is None  # Auto-select

    def test_request_with_specific_agent(self):
        """Request targeting specific agent."""
        ctx = DelegationContext(
            delegation_id="DEL-011",
            task_id="TASK-011",
            source_agent_id="AGENT-001",
            task_description="Specific agent task",
        )

        request = DelegationRequest(
            task_id="TASK-011",
            delegation_type=DelegationType.IMPLEMENTATION,
            target_role=AgentRole.CODING,
            context=ctx,
            target_agent_id="AGENT-SPECIFIC",
        )

        assert request.target_agent_id == "AGENT-SPECIFIC"

    def test_request_id_auto_generated(self):
        """Request ID is auto-generated."""
        ctx = DelegationContext(
            delegation_id="DEL-012",
            task_id="TASK-012",
            source_agent_id="AGENT-001",
            task_description="Test",
        )

        request = DelegationRequest(
            task_id="TASK-012",
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=ctx,
        )

        assert request.request_id.startswith("DEL-")


# =============================================================================
# DelegationResult Tests
# =============================================================================

class TestDelegationResult:
    """Test DelegationResult dataclass."""

    def test_success_result(self):
        """Create successful delegation result."""
        result = DelegationResult(
            success=True,
            delegation_id="DEL-020",
            task_id="TASK-020",
            source_agent_id="AGENT-001",
            target_agent_id="AGENT-002",
            result_data={"status": "completed"},
            message="Task completed successfully",
        )

        assert result.success is True
        assert result.result_data["status"] == "completed"

    def test_failure_result(self):
        """Create failed delegation result."""
        result = DelegationResult(
            success=False,
            delegation_id="DEL-021",
            task_id="TASK-021",
            source_agent_id="AGENT-001",
            target_agent_id="",
            message="No suitable agent found",
        )

        assert result.success is False
        assert "No suitable agent" in result.message

    def test_result_with_followup(self):
        """Result indicating followup needed."""
        result = DelegationResult(
            success=True,
            delegation_id="DEL-022",
            task_id="TASK-022",
            source_agent_id="AGENT-001",
            target_agent_id="AGENT-002",
            needs_followup=True,
            followup_type=DelegationType.VALIDATION,
            followup_context={"item": "code_changes"},
        )

        assert result.needs_followup is True
        assert result.followup_type == DelegationType.VALIDATION


# =============================================================================
# DelegationProtocol Tests
# =============================================================================

class TestDelegationProtocol:
    """Test DelegationProtocol class."""

    def _create_mock_engine(self):
        """Create mock orchestrator engine."""
        engine = Mock()
        engine.get_agent = Mock(return_value=None)
        engine.get_available_agents = Mock(return_value=[])
        return engine

    def test_init(self):
        """Initialize delegation protocol."""
        engine = self._create_mock_engine()
        protocol = DelegationProtocol(engine)

        assert protocol.active_count == 0
        assert len(protocol.history) == 0

    def test_register_handler(self):
        """Register delegation handler."""
        engine = self._create_mock_engine()
        protocol = DelegationProtocol(engine)

        async def research_handler(ctx):
            return {"findings": ["result1", "result2"]}

        protocol.register_handler(DelegationType.RESEARCH, research_handler)
        assert DelegationType.RESEARCH in protocol._handlers

    def test_delegate_no_agent(self):
        """Delegate fails when no suitable agent."""
        engine = self._create_mock_engine()
        engine.get_available_agents.return_value = []

        protocol = DelegationProtocol(engine)

        ctx = DelegationContext(
            delegation_id="DEL-030",
            task_id="TASK-030",
            source_agent_id="AGENT-001",
            task_description="Research task",
        )

        request = DelegationRequest(
            task_id="TASK-030",
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=ctx,
        )

        result = asyncio.run(protocol.delegate(request))

        assert result.success is False
        assert "No suitable agent" in result.message

    def test_delegate_trust_too_low(self):
        """Delegate fails when agent trust below threshold."""
        engine = self._create_mock_engine()

        # Agent with low trust
        low_trust_agent = AgentInfo(
            agent_id="AGENT-LOW",
            name="Low Trust Agent",
            role=AgentRole.RESEARCH,
            trust_score=0.3,
        )
        engine.get_available_agents.return_value = [low_trust_agent]

        protocol = DelegationProtocol(engine)

        ctx = DelegationContext(
            delegation_id="DEL-031",
            task_id="TASK-031",
            source_agent_id="AGENT-001",
            task_description="Critical task",
            min_trust_score=0.7,  # Requires higher trust
        )

        request = DelegationRequest(
            task_id="TASK-031",
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=ctx,
        )

        result = asyncio.run(protocol.delegate(request))

        assert result.success is False
        assert "trust" in result.message.lower()

    def test_delegate_success_with_handler(self):
        """Successful delegation with registered handler."""
        engine = self._create_mock_engine()

        agent = AgentInfo(
            agent_id="AGENT-RES",
            name="Research Agent",
            role=AgentRole.RESEARCH,
            trust_score=0.85,
        )
        engine.get_available_agents.return_value = [agent]

        protocol = DelegationProtocol(engine)

        # Register handler
        async def research_handler(ctx):
            return {"findings": ["Pattern A", "Pattern B"]}

        protocol.register_handler(DelegationType.RESEARCH, research_handler)

        ctx = DelegationContext(
            delegation_id="DEL-032",
            task_id="TASK-032",
            source_agent_id="AGENT-001",
            task_description="Research patterns",
        )

        request = DelegationRequest(
            task_id="TASK-032",
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=ctx,
        )

        result = asyncio.run(protocol.delegate(request))

        assert result.success is True
        assert result.target_agent_id == "AGENT-RES"
        assert result.result_data["findings"] == ["Pattern A", "Pattern B"]

    def test_delegate_default_handler(self):
        """Delegation without handler returns pending status."""
        engine = self._create_mock_engine()

        agent = AgentInfo(
            agent_id="AGENT-CODE",
            name="Coding Agent",
            role=AgentRole.CODING,
            trust_score=0.9,
        )
        engine.get_available_agents.return_value = [agent]

        protocol = DelegationProtocol(engine)

        ctx = DelegationContext(
            delegation_id="DEL-033",
            task_id="TASK-033",
            source_agent_id="AGENT-001",
            task_description="Implement feature",
        )

        request = DelegationRequest(
            task_id="TASK-033",
            delegation_type=DelegationType.IMPLEMENTATION,
            target_role=AgentRole.CODING,
            context=ctx,
        )

        result = asyncio.run(protocol.delegate(request))

        assert result.success is True
        assert result.result_data["status"] == "pending_manual"

    def test_delegate_specific_agent(self):
        """Delegate to specific agent by ID."""
        engine = self._create_mock_engine()

        agent = AgentInfo(
            agent_id="AGENT-SPECIFIC",
            name="Specific Agent",
            role=AgentRole.CODING,
            trust_score=0.9,
        )
        engine.get_agent.return_value = agent

        protocol = DelegationProtocol(engine)

        ctx = DelegationContext(
            delegation_id="DEL-034",
            task_id="TASK-034",
            source_agent_id="AGENT-001",
            task_description="Task for specific agent",
        )

        request = DelegationRequest(
            task_id="TASK-034",
            delegation_type=DelegationType.IMPLEMENTATION,
            target_role=AgentRole.CODING,
            context=ctx,
            target_agent_id="AGENT-SPECIFIC",
        )

        result = asyncio.run(protocol.delegate(request))

        assert result.success is True
        assert result.target_agent_id == "AGENT-SPECIFIC"
        engine.get_agent.assert_called_with("AGENT-SPECIFIC")

    def test_history_tracking(self):
        """Delegation history is tracked."""
        engine = self._create_mock_engine()

        agent = AgentInfo("A1", "Test", AgentRole.RESEARCH, 0.9)
        engine.get_available_agents.return_value = [agent]

        protocol = DelegationProtocol(engine)

        ctx = DelegationContext(
            delegation_id="DEL-035",
            task_id="TASK-035",
            source_agent_id="AGENT-001",
            task_description="Test",
        )

        request = DelegationRequest(
            task_id="TASK-035",
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=ctx,
        )

        asyncio.run(protocol.delegate(request))

        assert len(protocol.history) == 1
        assert protocol.history[0].task_id == "TASK-035"

    def test_delegation_chain(self):
        """Get delegation chain for a task."""
        engine = self._create_mock_engine()

        agent = AgentInfo("A1", "Test", AgentRole.RESEARCH, 0.9)
        engine.get_available_agents.return_value = [agent]

        protocol = DelegationProtocol(engine)

        # Two delegations for same task
        for i in range(2):
            ctx = DelegationContext(
                delegation_id=f"DEL-{i}",
                task_id="TASK-CHAIN",
                source_agent_id="AGENT-001",
                task_description=f"Step {i}",
            )
            request = DelegationRequest(
                task_id="TASK-CHAIN",
                delegation_type=DelegationType.RESEARCH,
                target_role=AgentRole.RESEARCH,
                context=ctx,
            )
            asyncio.run(protocol.delegate(request))

        chain = protocol.get_delegation_chain("TASK-CHAIN")
        assert len(chain) == 2

    def test_stats(self):
        """Get delegation statistics."""
        engine = self._create_mock_engine()
        protocol = DelegationProtocol(engine)

        stats = protocol.get_stats()

        assert "active_delegations" in stats
        assert "total_delegations" in stats
        assert "success_rate" in stats


# =============================================================================
# Convenience Method Tests
# =============================================================================

class TestConvenienceMethods:
    """Test convenience delegation methods."""

    def _create_mock_engine(self):
        """Create mock orchestrator engine."""
        engine = Mock()
        engine.get_agent = Mock(return_value=None)
        engine.get_available_agents = Mock(return_value=[])
        return engine

    def test_delegate_research(self):
        """Convenience method for research delegation."""
        engine = self._create_mock_engine()
        agent = AgentInfo("RES-001", "Research", AgentRole.RESEARCH, 0.9)
        engine.get_available_agents.return_value = [agent]

        protocol = DelegationProtocol(engine)

        result = asyncio.run(protocol.delegate_research(
            task_id="TASK-040",
            source_agent_id="AGENT-001",
            query="Find authentication patterns",
        ))

        assert result.success is True

    def test_delegate_implementation(self):
        """Convenience method for implementation delegation."""
        engine = self._create_mock_engine()
        agent = AgentInfo("CODE-001", "Coder", AgentRole.CODING, 0.9)
        engine.get_available_agents.return_value = [agent]

        protocol = DelegationProtocol(engine)

        result = asyncio.run(protocol.delegate_implementation(
            task_id="TASK-041",
            source_agent_id="AGENT-001",
            spec="Implement login endpoint",
            constraints=["Use JWT", "No external deps"],
        ))

        assert result.success is True

    def test_delegate_validation(self):
        """Convenience method for validation delegation."""
        engine = self._create_mock_engine()
        agent = AgentInfo("CUR-001", "Curator", AgentRole.CURATOR, 0.9)
        engine.get_available_agents.return_value = [agent]

        protocol = DelegationProtocol(engine)

        result = asyncio.run(protocol.delegate_validation(
            task_id="TASK-042",
            source_agent_id="AGENT-001",
            item_to_validate={"code": "def foo(): pass"},
            rules=["RULE-023"],
        ))

        assert result.success is True

    def test_escalate(self):
        """Convenience method for escalation."""
        engine = self._create_mock_engine()
        agent = AgentInfo("ORCH-001", "Orchestrator", AgentRole.ORCHESTRATOR, 0.95)
        engine.get_available_agents.return_value = [agent]

        protocol = DelegationProtocol(engine)

        result = asyncio.run(protocol.escalate(
            task_id="TASK-043",
            source_agent_id="AGENT-001",
            reason="Cannot determine task type",
        ))

        assert result.success is True


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_create_delegation_context(self):
        """Create delegation context with auto-ID."""
        ctx = create_delegation_context(
            task_id="TASK-050",
            source_agent_id="AGENT-001",
            description="Test context",
            gathered_context={"key": "value"},
        )

        assert ctx.task_id == "TASK-050"
        assert ctx.delegation_id.startswith("DEL-")
        assert ctx.gathered_context["key"] == "value"

    def test_create_research_request(self):
        """Create research delegation request."""
        request = create_research_request(
            task_id="TASK-051",
            source_agent_id="AGENT-001",
            query="Research API patterns",
        )

        assert request.delegation_type == DelegationType.RESEARCH
        assert request.target_role == AgentRole.RESEARCH

    def test_create_implementation_request(self):
        """Create implementation delegation request."""
        request = create_implementation_request(
            task_id="TASK-052",
            source_agent_id="AGENT-001",
            spec="Implement caching layer",
            context={"existing_cache": "redis"},
        )

        assert request.delegation_type == DelegationType.IMPLEMENTATION
        assert request.target_role == AgentRole.CODING
        assert request.context.gathered_context["existing_cache"] == "redis"
