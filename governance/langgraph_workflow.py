"""
LangGraph Governance Workflow
=============================
Stateful workflow for rule proposals per GOV-BICAM-01-v1 (Multi-Agent Governance).

**Refactored: 2024-12-28 per GAP-FILE-009**
Original: 851 lines → Package with 5 modules (~700 lines total)

Modules extracted to governance/langgraph/:
- state.py: ProposalState TypedDict, Vote TypedDict, constants
- nodes.py: 8 workflow node functions
- edges.py: Conditional edge router functions
- graph.py: Graph construction and compilation
- mcp_wrapper.py: MCP tool interface

Features:
- Explicit state management with TypedDict
- Checkpoint persistence (survives crashes)
- Dry-run mode for safe testing
- Trust-weighted voting
- Automatic rollback on failure

Workflow Phases:
    SUBMIT → VALIDATE → ASSESS → VOTE → DECIDE → IMPLEMENT → COMPLETE
                ↓                   ↓
              REJECT              DISPUTE
                ↓                   ↓
              COMPLETE            COMPLETE

Per: GOV-BICAM-01-v1 (Multi-Agent Governance Protocol)
"""

# Re-export everything from the package for backward compatibility
from governance.langgraph import (
    # State
    Vote,
    ProposalState,
    QUORUM_THRESHOLD,
    APPROVAL_THRESHOLD,
    DISPUTE_THRESHOLD,
    TRUST_WEIGHTS,
    # Nodes
    submit_node,
    validate_node,
    assess_node,
    vote_node,
    decide_node,
    implement_node,
    complete_node,
    reject_node,
    # Edges
    check_validation,
    check_decision,
    check_status,
    # Graph
    build_proposal_graph,
    create_initial_state,
    run_proposal_workflow,
    print_workflow_diagram,
    LANGGRAPH_AVAILABLE,
    # MCP
    proposal_submit_mcp,
)

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


# =============================================================================
# MAIN (CLI entrypoint)
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="LangGraph Governance Workflow")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Run in dry-run mode (default)")
    parser.add_argument("--execute", action="store_true",
                        help="Execute actual workflow")
    parser.add_argument("--action", default="create",
                        choices=["create", "modify", "deprecate"],
                        help="Proposal action type")
    parser.add_argument("--show-graph", action="store_true",
                        help="Show workflow diagram")

    args = parser.parse_args()

    if args.show_graph:
        print_workflow_diagram()
        exit(0)

    dry_run = not args.execute

    result = run_proposal_workflow(
        action=args.action,
        hypothesis="Test hypothesis for demonstration purposes",
        evidence=["Evidence item 1", "Evidence item 2"],
        directive="Test directive for new rule" if args.action != "deprecate" else None,
        dry_run=dry_run
    )

    print(f"\n\n{'='*60}")
    print("FINAL STATE:")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, default=str))
