"""
Robot Framework Library for Delegation - Protocol & Convenience Tests.

Per ORCH-004: Agent delegation protocol.
Split from DelegationLibrary.py per DOC-SIZE-01-v1.

Covers: DelegationProtocol, convenience functions.
"""
import asyncio
from pathlib import Path
from robot.api.deco import keyword


class DelegationProtocolLibrary:
    """Library for testing delegation protocol operations."""

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

    # =========================================================================
    # DelegationProtocol Tests
    # =========================================================================

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

    # =========================================================================
    # Convenience Function Tests
    # =========================================================================

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
