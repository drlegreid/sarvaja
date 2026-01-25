"""
Robot Framework Library for Delegation - Request & Result Tests.

Per ORCH-004: Agent delegation protocol.
Split from DelegationLibrary.py per DOC-SIZE-01-v1.

Covers: DelegationRequest, DelegationResult.
"""
from pathlib import Path
from robot.api.deco import keyword


class DelegationRequestLibrary:
    """Library for testing delegation requests and results."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # DelegationRequest Tests
    # =========================================================================

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

    # =========================================================================
    # DelegationResult Tests
    # =========================================================================

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
