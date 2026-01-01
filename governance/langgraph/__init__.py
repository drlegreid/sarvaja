"""
LangGraph Governance Workflow Package
=====================================
Modular stateful workflow for rule proposals per RULE-011.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-009: Extracted from langgraph_workflow.py (851 lines)

Modules:
- state: ProposalState TypedDict, Vote TypedDict, constants
- nodes: 8 workflow node functions
- edges: Conditional edge router functions
- graph: Graph construction and compilation
- mcp_wrapper: MCP tool interface

Created: 2024-12-28
"""

from .state import (
    Vote,
    ProposalState,
    QUORUM_THRESHOLD,
    APPROVAL_THRESHOLD,
    DISPUTE_THRESHOLD,
    TRUST_WEIGHTS,
)

from .nodes import (
    submit_node,
    validate_node,
    assess_node,
    vote_node,
    decide_node,
    implement_node,
    complete_node,
    reject_node,
)

from .edges import (
    check_validation,
    check_decision,
    check_status,
)

from .graph import (
    build_proposal_graph,
    create_initial_state,
    run_proposal_workflow,
    print_workflow_diagram,
    LANGGRAPH_AVAILABLE,
)

from .mcp_wrapper import proposal_submit_mcp

__all__ = [
    # State
    "Vote",
    "ProposalState",
    "QUORUM_THRESHOLD",
    "APPROVAL_THRESHOLD",
    "DISPUTE_THRESHOLD",
    "TRUST_WEIGHTS",
    # Nodes
    "submit_node",
    "validate_node",
    "assess_node",
    "vote_node",
    "decide_node",
    "implement_node",
    "complete_node",
    "reject_node",
    # Edges
    "check_validation",
    "check_decision",
    "check_status",
    # Graph
    "build_proposal_graph",
    "create_initial_state",
    "run_proposal_workflow",
    "print_workflow_diagram",
    "LANGGRAPH_AVAILABLE",
    # MCP
    "proposal_submit_mcp",
]
