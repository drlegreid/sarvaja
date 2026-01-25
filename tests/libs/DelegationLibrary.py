"""
Robot Framework Library for Delegation Protocol Tests.

Per ORCH-004: Agent delegation protocol.
Migrated from tests/test_delegation.py
"""
import asyncio
from pathlib import Path
from robot.api.deco import keyword


class DelegationLibrary:
    """Library for testing delegation protocol."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    def _create_mock_engine(self):
        """Create mock orchestrator engine."""
        from unittest.mock import Mock
        engine = Mock()
        engine.get_agent = Mock(return_value=None)
        engine.get_available_agents = Mock(return_value=[])
        return engine

    # =============================================================================
    # DelegationType Tests
    # =============================================================================

    @keyword("Delegation Type Research")
    def delegation_type_research(self):
        """RESEARCH type for context gathering."""
        try:
            from agent.orchestrator.delegation import DelegationType
            return {"value_correct": DelegationType.RESEARCH.value == "research"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Delegation Type Implementation")
    def delegation_type_implementation(self):
        """IMPLEMENTATION type for coding tasks."""
        try:
            from agent.orchestrator.delegation import DelegationType
            return {"value_correct": DelegationType.IMPLEMENTATION.value == "impl"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Delegation Type Validation")
    def delegation_type_validation(self):
        """VALIDATION type for rule checking."""
        try:
            from agent.orchestrator.delegation import DelegationType
            return {"value_correct": DelegationType.VALIDATION.value == "validation"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Delegation Type Escalation")
    def delegation_type_escalation(self):
        """ESCALATION type for authority escalation."""
        try:
            from agent.orchestrator.delegation import DelegationType
            return {"value_correct": DelegationType.ESCALATION.value == "escalation"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # DelegationPriority Tests
    # =============================================================================

    @keyword("Priority Ordering Works")
    def priority_ordering_works(self):
        """CRITICAL < HIGH < MEDIUM < LOW."""
        try:
            from agent.orchestrator.delegation import DelegationPriority
            return {
                "crit_lt_high": DelegationPriority.CRITICAL.value < DelegationPriority.HIGH.value,
                "high_lt_med": DelegationPriority.HIGH.value < DelegationPriority.MEDIUM.value,
                "med_lt_low": DelegationPriority.MEDIUM.value < DelegationPriority.LOW.value
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Critical Priority Value")
    def critical_priority_value(self):
        """CRITICAL has value 1."""
        try:
            from agent.orchestrator.delegation import DelegationPriority
            return {"is_1": DelegationPriority.CRITICAL.value == 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # DelegationContext Tests
    # =============================================================================

    @keyword("Context Basic Creation")
    def context_basic_creation(self):
        """Create basic delegation context."""
        try:
            from agent.orchestrator.delegation import DelegationContext, DelegationPriority

            ctx = DelegationContext(
                delegation_id="DEL-001",
                task_id="TASK-001",
                source_agent_id="AGENT-001",
                task_description="Research authentication patterns",
            )

            return {
                "id_correct": ctx.delegation_id == "DEL-001",
                "task_correct": ctx.task_id == "TASK-001",
                "source_correct": ctx.source_agent_id == "AGENT-001",
                "priority_default": ctx.priority == DelegationPriority.MEDIUM
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context With Constraints")
    def context_with_constraints(self):
        """Create context with constraints."""
        try:
            from agent.orchestrator.delegation import DelegationContext

            ctx = DelegationContext(
                delegation_id="DEL-002",
                task_id="TASK-002",
                source_agent_id="AGENT-001",
                task_description="Implement feature",
                constraints=["No external deps", "Must be async"],
            )

            return {
                "has_constraints": len(ctx.constraints) == 2,
                "constraint_present": "No external deps" in ctx.constraints
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context With Evidence")
    def context_with_evidence(self):
        """Create context with evidence."""
        try:
            from agent.orchestrator.delegation import DelegationContext

            ctx = DelegationContext(
                delegation_id="DEL-003",
                task_id="TASK-003",
                source_agent_id="AGENT-001",
                task_description="Review code",
                evidence=["tests/test_auth.py passed", "No lint errors"],
            )

            return {"has_evidence": len(ctx.evidence) == 2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context To Dict")
    def context_to_dict(self):
        """Convert context to dictionary."""
        try:
            from agent.orchestrator.delegation import DelegationContext, DelegationPriority

            ctx = DelegationContext(
                delegation_id="DEL-004",
                task_id="TASK-004",
                source_agent_id="AGENT-001",
                task_description="Test task",
                priority=DelegationPriority.HIGH,
            )

            d = ctx.to_dict()
            return {
                "id_correct": d.get("delegation_id") == "DEL-004",
                "priority_correct": d.get("priority") == "HIGH",
                "has_created_at": "created_at" in d
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context From Dict")
    def context_from_dict(self):
        """Create context from dictionary."""
        try:
            from agent.orchestrator.delegation import DelegationContext, DelegationPriority

            data = {
                "delegation_id": "DEL-005",
                "task_id": "TASK-005",
                "source_agent_id": "AGENT-002",
                "task_description": "From dict",
                "priority": "CRITICAL",
                "min_trust_score": 0.8,
            }

            ctx = DelegationContext.from_dict(data)
            return {
                "id_correct": ctx.delegation_id == "DEL-005",
                "priority_correct": ctx.priority == DelegationPriority.CRITICAL,
                "trust_correct": ctx.min_trust_score == 0.8
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Min Trust Default")
    def context_min_trust_default(self):
        """Default min_trust_score is 0.5."""
        try:
            from agent.orchestrator.delegation import DelegationContext

            ctx = DelegationContext(
                delegation_id="DEL-006",
                task_id="TASK-006",
                source_agent_id="AGENT-001",
                task_description="Test",
            )
            return {"default_trust": ctx.min_trust_score == 0.5}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # DelegationRequest Tests
    # =============================================================================

    @keyword("Request Basic Creation")
    def request_basic_creation(self):
        """Create basic delegation request."""
        try:
            from agent.orchestrator.delegation import (
                DelegationContext, DelegationRequest, DelegationType
            )
            from agent.orchestrator.engine import AgentRole

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

            return {
                "task_correct": request.task_id == "TASK-010",
                "type_correct": request.delegation_type == DelegationType.RESEARCH,
                "target_none": request.target_agent_id is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Request With Specific Agent")
    def request_with_specific_agent(self):
        """Request targeting specific agent."""
        try:
            from agent.orchestrator.delegation import (
                DelegationContext, DelegationRequest, DelegationType
            )
            from agent.orchestrator.engine import AgentRole

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

            return {"has_target": request.target_agent_id == "AGENT-SPECIFIC"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Request ID Auto Generated")
    def request_id_auto_generated(self):
        """Request ID is auto-generated."""
        try:
            from agent.orchestrator.delegation import (
                DelegationContext, DelegationRequest, DelegationType
            )
            from agent.orchestrator.engine import AgentRole

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

            return {"starts_with_del": request.request_id.startswith("DEL-")}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # DelegationResult Tests
    # =============================================================================

    @keyword("Result Success")
    def result_success(self):
        """Create successful delegation result."""
        try:
            from agent.orchestrator.delegation import DelegationResult

            result = DelegationResult(
                success=True,
                delegation_id="DEL-020",
                task_id="TASK-020",
                source_agent_id="AGENT-001",
                target_agent_id="AGENT-002",
                result_data={"status": "completed"},
                message="Task completed successfully",
            )

            return {
                "is_success": result.success is True,
                "status_correct": result.result_data.get("status") == "completed"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Result Failure")
    def result_failure(self):
        """Create failed delegation result."""
        try:
            from agent.orchestrator.delegation import DelegationResult

            result = DelegationResult(
                success=False,
                delegation_id="DEL-021",
                task_id="TASK-021",
                source_agent_id="AGENT-001",
                target_agent_id="",
                message="No suitable agent found",
            )

            return {
                "is_failure": result.success is False,
                "has_message": "No suitable agent" in result.message
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Result With Followup")
    def result_with_followup(self):
        """Result indicating followup needed."""
        try:
            from agent.orchestrator.delegation import DelegationResult, DelegationType

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

            return {
                "needs_followup": result.needs_followup is True,
                "followup_type": result.followup_type == DelegationType.VALIDATION
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # DelegationProtocol Tests
    # =============================================================================

    @keyword("Protocol Init")
    def protocol_init(self):
        """Initialize delegation protocol."""
        try:
            from agent.orchestrator.delegation import DelegationProtocol

            engine = self._create_mock_engine()
            protocol = DelegationProtocol(engine)

            return {
                "active_zero": protocol.active_count == 0,
                "history_empty": len(protocol.history) == 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Protocol Register Handler")
    def protocol_register_handler(self):
        """Register delegation handler."""
        try:
            from agent.orchestrator.delegation import DelegationProtocol, DelegationType

            engine = self._create_mock_engine()
            protocol = DelegationProtocol(engine)

            async def research_handler(ctx):
                return {"findings": ["result1", "result2"]}

            protocol.register_handler(DelegationType.RESEARCH, research_handler)
            return {"handler_registered": DelegationType.RESEARCH in protocol._handlers}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Protocol Delegate No Agent")
    def protocol_delegate_no_agent(self):
        """Delegate fails when no suitable agent."""
        try:
            from agent.orchestrator.delegation import (
                DelegationProtocol, DelegationType, DelegationContext, DelegationRequest
            )
            from agent.orchestrator.engine import AgentRole

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

            return {
                "is_failure": result.success is False,
                "has_message": "No suitable agent" in result.message
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Protocol Get Stats")
    def protocol_get_stats(self):
        """Get delegation statistics."""
        try:
            from agent.orchestrator.delegation import DelegationProtocol

            engine = self._create_mock_engine()
            protocol = DelegationProtocol(engine)

            stats = protocol.get_stats()

            return {
                "has_active": "active_delegations" in stats,
                "has_total": "total_delegations" in stats,
                "has_success_rate": "success_rate" in stats
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Convenience Function Tests
    # =============================================================================

    @keyword("Create Delegation Context Works")
    def create_delegation_context_works(self):
        """Create delegation context with auto-ID."""
        try:
            from agent.orchestrator.delegation import create_delegation_context

            ctx = create_delegation_context(
                task_id="TASK-050",
                source_agent_id="AGENT-001",
                description="Test context",
                gathered_context={"key": "value"},
            )

            return {
                "task_correct": ctx.task_id == "TASK-050",
                "id_starts_with": ctx.delegation_id.startswith("DEL-"),
                "context_correct": ctx.gathered_context.get("key") == "value"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Research Request Works")
    def create_research_request_works(self):
        """Create research delegation request."""
        try:
            from agent.orchestrator.delegation import (
                create_research_request, DelegationType
            )
            from agent.orchestrator.engine import AgentRole

            request = create_research_request(
                task_id="TASK-051",
                source_agent_id="AGENT-001",
                query="Research API patterns",
            )

            return {
                "type_correct": request.delegation_type == DelegationType.RESEARCH,
                "role_correct": request.target_role == AgentRole.RESEARCH
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Implementation Request Works")
    def create_implementation_request_works(self):
        """Create implementation delegation request."""
        try:
            from agent.orchestrator.delegation import (
                create_implementation_request, DelegationType
            )
            from agent.orchestrator.engine import AgentRole

            request = create_implementation_request(
                task_id="TASK-052",
                source_agent_id="AGENT-001",
                spec="Implement caching layer",
                context={"existing_cache": "redis"},
            )

            return {
                "type_correct": request.delegation_type == DelegationType.IMPLEMENTATION,
                "role_correct": request.target_role == AgentRole.CODING,
                "context_correct": request.context.gathered_context.get("existing_cache") == "redis"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
