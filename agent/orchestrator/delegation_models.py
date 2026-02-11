"""
Delegation Protocol Models.

Per DOC-SIZE-01-v1: Extracted from delegation.py (578 lines).
Enums and dataclasses for delegation context, requests, and results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import uuid

from .engine import AgentRole


class DelegationType(Enum):
    """Types of delegation between agents."""
    RESEARCH = "research"
    IMPLEMENTATION = "impl"
    REVIEW = "review"
    ESCALATION = "escalation"
    VALIDATION = "validation"
    SYNC = "sync"


class DelegationPriority(Enum):
    """Priority levels for delegations."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class DelegationContext:
    """Context passed to target agent during delegation."""
    delegation_id: str
    task_id: str
    source_agent_id: str
    task_description: str
    gathered_context: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: Optional[str] = None
    priority: DelegationPriority = DelegationPriority.MEDIUM
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
    """Request to delegate work to another agent."""
    task_id: str
    delegation_type: DelegationType
    target_role: AgentRole
    context: DelegationContext
    target_agent_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: f"DEL-{uuid.uuid4().hex[:8].upper()}")
    requested_at: str = field(default_factory=lambda: datetime.now().isoformat())
    on_complete: Optional[Callable] = None


@dataclass
class DelegationResult:
    """Result returned from a delegated task."""
    success: bool
    delegation_id: str
    task_id: str
    source_agent_id: str
    target_agent_id: str
    result_data: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    message: str = ""
    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: int = 0
    needs_followup: bool = False
    followup_type: Optional[DelegationType] = None
    followup_context: Optional[Dict[str, Any]] = None
