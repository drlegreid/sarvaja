"""
Agent Delegation Protocol (ORCH-004).

Handles context handoff between agents during task delegation.

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing

Delegation Flow:
    1. Source agent creates DelegationRequest with context
    2. DelegationProtocol validates and routes request
    3. Target agent receives DelegationContext
    4. Target agent returns DelegationResult
    5. Source agent receives result and continues or escalates
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import uuid

from .engine import AgentInfo, AgentRole


class DelegationType(Enum):
    """Types of delegation between agents."""
    RESEARCH = "research"       # Gather context/information
    IMPLEMENTATION = "impl"     # Write code/implement feature
    REVIEW = "review"          # Review code/decision
    ESCALATION = "escalation"  # Escalate to higher authority
    VALIDATION = "validation"  # Validate against rules
    SYNC = "sync"              # Synchronize data


class DelegationPriority(Enum):
    """Priority levels for delegations."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class DelegationContext:
    """
    Context passed to target agent during delegation.

    Contains all information the target agent needs to complete the delegated work.
    """
    # Identifiers
    delegation_id: str
    task_id: str
    source_agent_id: str

    # Context data
    task_description: str
    gathered_context: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: Optional[str] = None
    priority: DelegationPriority = DelegationPriority.MEDIUM

    # Trust requirements
    min_trust_score: float = 0.5
    requires_supervisor: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "delegation_id": self.delegation_id,
            "task_id": self.task_id,
            "source_agent_id": self.source_agent_id,
            "task_description": self.task_description,
            "gathered_context": self.gathered_context,
            "constraints": self.constraints,
            "evidence": self.evidence,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "priority": self.priority.name,
            "min_trust_score": self.min_trust_score,
            "requires_supervisor": self.requires_supervisor,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DelegationContext":
        """Create from dictionary."""
        priority = data.get("priority", "MEDIUM")
        if isinstance(priority, str):
            priority = DelegationPriority[priority]
        return cls(
            delegation_id=data["delegation_id"],
            task_id=data["task_id"],
            source_agent_id=data["source_agent_id"],
            task_description=data["task_description"],
            gathered_context=data.get("gathered_context", {}),
            constraints=data.get("constraints", []),
            evidence=data.get("evidence", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            deadline=data.get("deadline"),
            priority=priority,
            min_trust_score=data.get("min_trust_score", 0.5),
            requires_supervisor=data.get("requires_supervisor", False),
        )


@dataclass
class DelegationRequest:
    """
    Request to delegate work to another agent.
    """
    # Required fields
    task_id: str
    delegation_type: DelegationType
    target_role: AgentRole
    context: DelegationContext

    # Optional targeting
    target_agent_id: Optional[str] = None  # Specific agent, or None for auto-select

    # Request metadata
    request_id: str = field(default_factory=lambda: f"DEL-{uuid.uuid4().hex[:8].upper()}")
    requested_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Callback for async notification
    on_complete: Optional[Callable] = None


@dataclass
class DelegationResult:
    """
    Result returned from a delegated task.
    """
    # Status
    success: bool
    delegation_id: str
    task_id: str

    # Agents involved
    source_agent_id: str
    target_agent_id: str

    # Result data
    result_data: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    message: str = ""

    # Metadata
    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: int = 0

    # Next steps
    needs_followup: bool = False
    followup_type: Optional[DelegationType] = None
    followup_context: Optional[Dict[str, Any]] = None


class DelegationProtocol:
    """
    Protocol for handling agent-to-agent delegation.

    Features:
    - Context handoff between agents
    - Trust-based agent selection
    - Async delegation with callbacks
    - Delegation chain tracking

    Usage:
        protocol = DelegationProtocol(orchestrator_engine)

        # Create delegation request
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

        # Execute delegation
        result = await protocol.delegate(request)
    """

    def __init__(self, engine: Any):
        """
        Initialize delegation protocol.

        Args:
            engine: OrchestratorEngine instance for agent management
        """
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
        handler: Callable
    ) -> None:
        """
        Register a handler for a delegation type.

        Args:
            delegation_type: Type of delegation
            handler: Async callable(context: DelegationContext) -> Dict[str, Any]
        """
        self._handlers[delegation_type] = handler

    async def delegate(self, request: DelegationRequest) -> DelegationResult:
        """
        Execute a delegation request.

        Args:
            request: Delegation request

        Returns:
            Delegation result
        """
        start_time = datetime.now()

        # Track active delegation
        self._active_delegations[request.request_id] = request

        try:
            # Select target agent
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

            # Validate trust requirements
            if target_agent.trust_score < request.context.min_trust_score:
                return DelegationResult(
                    success=False,
                    delegation_id=request.context.delegation_id,
                    task_id=request.task_id,
                    source_agent_id=request.context.source_agent_id,
                    target_agent_id=target_agent.agent_id,
                    message=f"Agent trust {target_agent.trust_score} < required {request.context.min_trust_score}",
                )

            # Execute handler if registered
            handler = self._handlers.get(request.delegation_type)
            if handler:
                result_data = await handler(request.context)
            else:
                # Default: return context as-is for manual handling
                result_data = {
                    "status": "pending_manual",
                    "context": request.context.to_dict(),
                }

            # Calculate duration
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Create result
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

            # Store in history
            self._delegation_history.append(result)

            # Invoke callback if provided
            if request.on_complete:
                try:
                    request.on_complete(result)
                except Exception:
                    pass  # Don't fail delegation due to callback error

            return result

        finally:
            # Remove from active
            self._active_delegations.pop(request.request_id, None)

    def _select_target_agent(self, request: DelegationRequest) -> Optional[AgentInfo]:
        """
        Select target agent for delegation.

        Selection criteria:
        1. If specific agent requested, use that
        2. Otherwise, select by role with highest trust
        """
        # Specific agent requested
        if request.target_agent_id:
            return self._engine.get_agent(request.target_agent_id)

        # Select by role
        available = self._engine.get_available_agents(request.target_role)
        if not available:
            return None

        # Sort by trust (descending)
        available.sort(key=lambda a: -a.trust_score)
        return available[0]

    async def delegate_research(
        self,
        task_id: str,
        source_agent_id: str,
        query: str,
        gathered_context: Dict[str, Any] = None
    ) -> DelegationResult:
        """
        Convenience method: Delegate research to Research Agent.

        Args:
            task_id: Task ID
            source_agent_id: Source agent ID
            query: Research query
            gathered_context: Any existing context

        Returns:
            Delegation result with research findings
        """
        context = DelegationContext(
            delegation_id=f"DEL-RES-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            source_agent_id=source_agent_id,
            task_description=query,
            gathered_context=gathered_context or {},
        )

        request = DelegationRequest(
            task_id=task_id,
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=context,
        )

        return await self.delegate(request)

    async def delegate_implementation(
        self,
        task_id: str,
        source_agent_id: str,
        spec: str,
        context: Dict[str, Any] = None,
        constraints: List[str] = None
    ) -> DelegationResult:
        """
        Convenience method: Delegate implementation to Coding Agent.

        Args:
            task_id: Task ID
            source_agent_id: Source agent ID
            spec: Implementation specification
            context: Gathered context
            constraints: Implementation constraints

        Returns:
            Delegation result with implementation
        """
        delegation_context = DelegationContext(
            delegation_id=f"DEL-IMP-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            source_agent_id=source_agent_id,
            task_description=spec,
            gathered_context=context or {},
            constraints=constraints or [],
        )

        request = DelegationRequest(
            task_id=task_id,
            delegation_type=DelegationType.IMPLEMENTATION,
            target_role=AgentRole.CODING,
            context=delegation_context,
        )

        return await self.delegate(request)

    async def delegate_validation(
        self,
        task_id: str,
        source_agent_id: str,
        item_to_validate: Dict[str, Any],
        rules: List[str] = None
    ) -> DelegationResult:
        """
        Convenience method: Delegate validation to Rules Curator.

        Args:
            task_id: Task ID
            source_agent_id: Source agent ID
            item_to_validate: Item to validate
            rules: Specific rules to check

        Returns:
            Delegation result with validation outcome
        """
        context = DelegationContext(
            delegation_id=f"DEL-VAL-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            source_agent_id=source_agent_id,
            task_description="Validate against governance rules",
            gathered_context={"item": item_to_validate},
            constraints=rules or [],
        )

        request = DelegationRequest(
            task_id=task_id,
            delegation_type=DelegationType.VALIDATION,
            target_role=AgentRole.CURATOR,
            context=context,
        )

        return await self.delegate(request)

    async def escalate(
        self,
        task_id: str,
        source_agent_id: str,
        reason: str,
        context: Dict[str, Any] = None
    ) -> DelegationResult:
        """
        Escalate a task to the orchestrator for re-routing.

        Args:
            task_id: Task ID
            source_agent_id: Source agent ID
            reason: Reason for escalation
            context: Current context

        Returns:
            Delegation result with escalation handling
        """
        delegation_context = DelegationContext(
            delegation_id=f"DEL-ESC-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            source_agent_id=source_agent_id,
            task_description=f"ESCALATION: {reason}",
            gathered_context=context or {},
            priority=DelegationPriority.HIGH,
        )

        request = DelegationRequest(
            task_id=task_id,
            delegation_type=DelegationType.ESCALATION,
            target_role=AgentRole.ORCHESTRATOR,
            context=delegation_context,
        )

        return await self.delegate(request)

    def get_delegation_chain(self, task_id: str) -> List[DelegationResult]:
        """
        Get the chain of delegations for a task.

        Args:
            task_id: Task ID

        Returns:
            List of delegations in order
        """
        return [d for d in self._delegation_history if d.task_id == task_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get delegation statistics."""
        by_type = {}
        for result in self._delegation_history:
            # Try to find the type from active delegations or default
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


# =============================================================================
# Convenience Functions
# =============================================================================

def create_delegation_context(
    task_id: str,
    source_agent_id: str,
    description: str,
    **kwargs
) -> DelegationContext:
    """
    Create a delegation context with auto-generated ID.

    Args:
        task_id: Task ID
        source_agent_id: Source agent
        description: Task description
        **kwargs: Additional context fields

    Returns:
        DelegationContext instance
    """
    return DelegationContext(
        delegation_id=f"DEL-{uuid.uuid4().hex[:8].upper()}",
        task_id=task_id,
        source_agent_id=source_agent_id,
        task_description=description,
        **kwargs
    )


def create_research_request(
    task_id: str,
    source_agent_id: str,
    query: str
) -> DelegationRequest:
    """Create a research delegation request."""
    context = create_delegation_context(
        task_id=task_id,
        source_agent_id=source_agent_id,
        description=query,
    )
    return DelegationRequest(
        task_id=task_id,
        delegation_type=DelegationType.RESEARCH,
        target_role=AgentRole.RESEARCH,
        context=context,
    )


def create_implementation_request(
    task_id: str,
    source_agent_id: str,
    spec: str,
    context: Dict[str, Any] = None
) -> DelegationRequest:
    """Create an implementation delegation request."""
    delegation_context = create_delegation_context(
        task_id=task_id,
        source_agent_id=source_agent_id,
        description=spec,
        gathered_context=context or {},
    )
    return DelegationRequest(
        task_id=task_id,
        delegation_type=DelegationType.IMPLEMENTATION,
        target_role=AgentRole.CODING,
        context=delegation_context,
    )
