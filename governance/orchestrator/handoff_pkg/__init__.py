"""
Handoff Package for Multi-Agent Task Delegation.

Per DOC-SIZE-01-v1: Files under 300 lines.
Split from: governance/orchestrator/handoff.py (431 lines)

Per AGENT-WORKSPACES.md Phase 4: Delegation Protocol.
Per RULE-011: Multi-Agent Governance Protocol.

Created: 2026-01-17
"""

from .models import HandoffStatus, AgentRole, TaskHandoff
from .operations import (
    create_handoff,
    parse_handoff,
    write_handoff_evidence,
    read_handoff_evidence,
    get_pending_handoffs,
)

__all__ = [
    # Models
    "HandoffStatus",
    "AgentRole",
    "TaskHandoff",
    # Operations
    "create_handoff",
    "parse_handoff",
    "write_handoff_evidence",
    "read_handoff_evidence",
    "get_pending_handoffs",
]
