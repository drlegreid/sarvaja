"""
Agent Orchestrator Module (ORCH-002, ORCH-004, ORCH-005).

Task dispatch, priority queuing, agent delegation, and rules curation.

Per RULE-011: Multi-Agent Governance
Per RULE-014: Autonomous Task Sequencing
"""

from .engine import OrchestratorEngine, AgentInfo, AgentRole, DispatchResult
from .priority_queue import TaskPriorityQueue, QueuedTask, create_queue_from_tasks
from .task_poller import TypeDBTaskPoller, PollableTask, TaskPriority
from .delegation import (
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
from .curator_agent import (
    RulesCuratorAgent,
    CurationAction,
    CurationResult,
    RuleIssue,
    IssueSeverity,
    ConflictResolution,
    create_curator_agent,
)

__all__ = [
    # Engine (ORCH-002)
    "OrchestratorEngine",
    "AgentInfo",
    "AgentRole",
    "DispatchResult",
    # Priority Queue
    "TaskPriorityQueue",
    "QueuedTask",
    "create_queue_from_tasks",
    # Task Poller
    "TypeDBTaskPoller",
    "PollableTask",
    "TaskPriority",
    # Delegation (ORCH-004)
    "DelegationType",
    "DelegationPriority",
    "DelegationContext",
    "DelegationRequest",
    "DelegationResult",
    "DelegationProtocol",
    "create_delegation_context",
    "create_research_request",
    "create_implementation_request",
    # Rules Curator (ORCH-005)
    "RulesCuratorAgent",
    "CurationAction",
    "CurationResult",
    "RuleIssue",
    "IssueSeverity",
    "ConflictResolution",
    "create_curator_agent",
]
