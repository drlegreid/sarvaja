"""
Agent Delegation Protocol (ORCH-004).

Handles context handoff between agents during task delegation.

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing
Per DOC-SIZE-01-v1: Models in delegation_models.py, shortcuts in delegation_shortcuts.py.

Delegation Flow:
    1. Source agent creates DelegationRequest with context
    2. DelegationProtocol validates and routes request
    3. Target agent receives DelegationContext
    4. Target agent returns DelegationResult
    5. Source agent receives result and continues or escalates
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .engine import AgentInfo
from .delegation_models import (  # noqa: F401 — re-export for backward compat
    DelegationContext,
    DelegationPriority,
    DelegationRequest,
    DelegationResult,
    DelegationType,
)
from .delegation_shortcuts import (  # noqa: F401 — re-export
    DelegationShortcutsMixin,
    create_delegation_context,
    create_implementation_request,
    create_research_request,
)


class DelegationProtocol(DelegationShortcutsMixin):
    """
    Protocol for handling agent-to-agent delegation.

    Features:
    - Context handoff between agents
    - Trust-based agent selection
    - Async delegation with callbacks
    - Delegation chain tracking

    Usage:
        protocol = DelegationProtocol(orchestrator_engine)
        request = DelegationRequest(
            task_id="TASK-001",
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=DelegationContext(
                delegation_id="DEL-001",
                task_id="TASK-001",
                source_agent_id="AGENT-001",
                task_description="Research authentication patterns",
            )
        )
        result = await protocol.delegate(request)
    """

    def __init__(self, engine: Any):
        self._engine = engine
        self._active_delegations: Dict[str, DelegationRequest] = {}
        self._delegation_history: List[DelegationResult] = []
        self._handlers: Dict[DelegationType, Callable] = {}

    @property
    def active_count(self) -> int:
        """Number of active delegations."""
        return len(self._active_delegations)

    @property
    def history(self) -> List[DelegationResult]:
        """Delegation history (read-only copy)."""
        return list(self._delegation_history)

    def register_handler(
        self,
        delegation_type: DelegationType,
        handler: Callable,
    ) -> None:
        """Register a handler for a delegation type."""
        self._handlers[delegation_type] = handler

    async def delegate(self, request: DelegationRequest) -> DelegationResult:
        """Execute a delegation request."""
        start_time = datetime.now()
        self._active_delegations[request.request_id] = request

        try:
            target_agent = self._select_target_agent(request)
            if not target_agent:
                return DelegationResult(
                    success=False,
                    delegation_id=request.context.delegation_id,
                    task_id=request.task_id,
                    source_agent_id=request.context.source_agent_id,
                    target_agent_id="",
                    message=f"No suitable agent found for role {request.target_role.value}",
                )

            if target_agent.trust_score < request.context.min_trust_score:
                return DelegationResult(
                    success=False,
                    delegation_id=request.context.delegation_id,
                    task_id=request.task_id,
                    source_agent_id=request.context.source_agent_id,
                    target_agent_id=target_agent.agent_id,
                    message=f"Agent trust {target_agent.trust_score} < required {request.context.min_trust_score}",
                )

            handler = self._handlers.get(request.delegation_type)
            if handler:
                result_data = await handler(request.context)
            else:
                result_data = {
                    "status": "pending_manual",
                    "context": request.context.to_dict(),
                }

            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            result = DelegationResult(
                success=True,
                delegation_id=request.context.delegation_id,
                task_id=request.task_id,
                source_agent_id=request.context.source_agent_id,
                target_agent_id=target_agent.agent_id,
                result_data=result_data,
                message="Delegation completed successfully",
                duration_ms=duration_ms,
            )

            self._delegation_history.append(result)

            if request.on_complete:
                try:
                    request.on_complete(result)
                except Exception:
                    pass

            return result

        finally:
            self._active_delegations.pop(request.request_id, None)

    def _select_target_agent(self, request: DelegationRequest) -> Optional[AgentInfo]:
        """Select target agent (specific or highest-trust by role)."""
        if request.target_agent_id:
            return self._engine.get_agent(request.target_agent_id)

        available = self._engine.get_available_agents(request.target_role)
        if not available:
            return None

        available.sort(key=lambda a: -a.trust_score)
        return available[0]

    def get_delegation_chain(self, task_id: str) -> List[DelegationResult]:
        """Get the chain of delegations for a task."""
        return [d for d in self._delegation_history if d.task_id == task_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get delegation statistics."""
        by_type: Dict[str, int] = {}
        for _result in self._delegation_history:
            dtype = "unknown"
            by_type[dtype] = by_type.get(dtype, 0) + 1

        success_count = sum(1 for r in self._delegation_history if r.success)
        total_count = len(self._delegation_history)

        return {
            "active_delegations": self.active_count,
            "total_delegations": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0.0,
            "by_type": by_type,
        }
