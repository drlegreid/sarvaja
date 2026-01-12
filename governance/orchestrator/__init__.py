"""
Agent Orchestrator Package.

Per AGENT-WORKSPACES.md: Multi-agent workspace orchestration.
Per RULE-011: Multi-Agent Governance Protocol.
"""

from governance.orchestrator.handoff import (
    TaskHandoff,
    HandoffStatus,
    AgentRole,
    create_handoff,
    parse_handoff,
    write_handoff_evidence,
    read_handoff_evidence,
    get_pending_handoffs,
)

from governance.orchestrator.launcher import (
    LaunchConfig,
    LaunchResult,
    get_workspace_path,
    list_workspaces,
    validate_workspace,
    launch_workspace,
    launch_for_handoff,
    launch_all_pending,
    generate_launch_script,
)

__all__ = [
    # Handoff
    "TaskHandoff",
    "HandoffStatus",
    "AgentRole",
    "create_handoff",
    "parse_handoff",
    "write_handoff_evidence",
    "read_handoff_evidence",
    "get_pending_handoffs",
    # Launcher
    "LaunchConfig",
    "LaunchResult",
    "get_workspace_path",
    "list_workspaces",
    "validate_workspace",
    "launch_workspace",
    "launch_for_handoff",
    "launch_all_pending",
    "generate_launch_script",
]
