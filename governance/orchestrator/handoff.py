"""
Task Handoff Module for Multi-Agent Workspaces.

Per DOC-SIZE-01-v1: Modularized to handoff_pkg/ package.
This file re-exports for backward compatibility.

Per AGENT-WORKSPACES.md Phase 4: Delegation Protocol.
Per RULE-011: Multi-Agent Governance Protocol.

Original: 431 lines → Split into:
  - handoff_pkg/models.py (278 lines)
  - handoff_pkg/operations.py (162 lines)
"""

# Re-export all public API from package
from governance.orchestrator.handoff_pkg import (
    # Models
    HandoffStatus,
    AgentRole,
    TaskHandoff,
    # Operations
    create_handoff,
    parse_handoff,
    write_handoff_evidence,
    read_handoff_evidence,
    get_pending_handoffs,
)

__all__ = [
    "HandoffStatus",
    "AgentRole",
    "TaskHandoff",
    "create_handoff",
    "parse_handoff",
    "write_handoff_evidence",
    "read_handoff_evidence",
    "get_pending_handoffs",
]
