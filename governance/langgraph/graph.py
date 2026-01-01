"""
LangGraph Graph Construction
============================
Graph construction, compilation and execution.

Per RULE-011: Multi-Agent Governance Protocol
Per GAP-FILE-009: Extracted from langgraph_workflow.py

Created: 2024-12-28
"""

from typing import Literal, Optional, List
from datetime import datetime

from .state import ProposalState
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
from .edges import check_validation, check_decision, check_status


# Conditional import for LangGraph
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Stub classes for testing without langgraph
    START = "START"
    END = "END"

    class StateGraph:
        def __init__(self, state_type):
            self.state_type = state_type
            self.nodes = {}
            self.edges = []
            self.conditional_edges = []

        def add_node(self, name, func):
            self.nodes[name] = func

        def add_edge(self, from_node, to_node):
            self.edges.append((from_node, to_node))

        def add_conditional_edges(self, from_node, condition, mapping):
            self.conditional_edges.append((from_node, condition, mapping))

        def compile(self, checkpointer=None):
            return CompiledGraph(self)

    class CompiledGraph:
        def __init__(self, graph):
            self.graph = graph

        def stream(self, initial_state, config):
            # Simple execution for testing
            state = initial_state.copy()
            yield {"start": state}

    class MemorySaver:
        pass


def build_proposal_graph() -> StateGraph:
    """Build the governance proposal workflow graph."""

    if not LANGGRAPH_AVAILABLE:
        # Return stub graph for testing
        graph = StateGraph(ProposalState)
        return graph

    # Create graph with state schema
    graph = StateGraph(ProposalState)

    # Add nodes
    graph.add_node("submit", submit_node)
    graph.add_node("validate", validate_node)
    graph.add_node("assess", assess_node)
    graph.add_node("vote", vote_node)
    graph.add_node("decide", decide_node)
    graph.add_node("implement", implement_node)
    graph.add_node("complete", complete_node)
    graph.add_node("reject", reject_node)

    # Add edges
    graph.add_edge(START, "submit")

    # After submit, check status
    graph.add_conditional_edges(
        "submit",
        check_status,
        {
            "continue": "validate",
            "reject": "reject"
        }
    )

    # After validate, check if passed
    graph.add_conditional_edges(
        "validate",
        check_validation,
        {
            "assess": "assess",
            "reject": "reject"
        }
    )

    # Linear flow: assess → vote → decide
    graph.add_edge("assess", "vote")
    graph.add_edge("vote", "decide")

    # After decide, route based on decision
    graph.add_conditional_edges(
        "decide",
        check_decision,
        {
            "implement": "implement",
            "reject": "reject"
        }
    )

    # Final edges
    graph.add_edge("implement", "complete")
    graph.add_edge("reject", "complete")
    graph.add_edge("complete", END)

    return graph


def create_initial_state(
    action: Literal["create", "modify", "deprecate"],
    hypothesis: str,
    evidence: List[str],
    submitter_id: str = "AGENT-001",
    submitter_trust_score: float = 0.8,
    rule_id: Optional[str] = None,
    directive: Optional[str] = None,
    dry_run: bool = True
) -> ProposalState:
    """Create initial proposal state."""
    return {
        "proposal_id": "",
        "action": action,
        "rule_id": rule_id,
        "hypothesis": hypothesis,
        "evidence": evidence,
        "directive": directive,
        "submitter_id": submitter_id,
        "submitter_trust_score": submitter_trust_score,
        "current_phase": "start",
        "phases_completed": [],
        "validation_passed": False,
        "validation_errors": [],
        "impact_score": 0.0,
        "risk_level": "LOW",
        "affected_rules": [],
        "recommendations": [],
        "votes": [],
        "votes_for": 0.0,
        "votes_against": 0.0,
        "quorum_reached": False,
        "threshold_met": False,
        "decision": "pending",
        "decision_reasoning": "",
        "dry_run": dry_run,
        "changes_applied": [],
        "rollback_available": False,
        "status": "pending",
        "error_message": None,
        "started_at": None,
        "completed_at": None
    }


def run_proposal_workflow(
    action: Literal["create", "modify", "deprecate"],
    hypothesis: str,
    evidence: List[str],
    submitter_id: str = "AGENT-001",
    submitter_trust_score: float = 0.8,
    rule_id: Optional[str] = None,
    directive: Optional[str] = None,
    dry_run: bool = True
) -> ProposalState:
    """Run the proposal workflow."""

    # Build graph
    graph = build_proposal_graph()

    if not LANGGRAPH_AVAILABLE:
        # Run simplified execution for testing
        state = create_initial_state(
            action=action,
            hypothesis=hypothesis,
            evidence=evidence,
            submitter_id=submitter_id,
            submitter_trust_score=submitter_trust_score,
            rule_id=rule_id,
            directive=directive,
            dry_run=dry_run
        )

        # Execute nodes sequentially
        for node_name in ["submit", "validate", "assess", "vote", "decide", "implement", "complete"]:
            if node_name in graph.nodes:
                result = graph.nodes[node_name](state)
                state.update(result)

                # Check for early exit
                if state.get("status") == "failed":
                    reject_result = reject_node(state)
                    state.update(reject_result)
                    complete_result = complete_node(state)
                    state.update(complete_result)
                    break

        return state

    # Add checkpointer for persistence
    checkpointer = MemorySaver()

    # Compile graph
    app = graph.compile(checkpointer=checkpointer)

    # Initial state
    initial_state = create_initial_state(
        action=action,
        hypothesis=hypothesis,
        evidence=evidence,
        submitter_id=submitter_id,
        submitter_trust_score=submitter_trust_score,
        rule_id=rule_id,
        directive=directive,
        dry_run=dry_run
    )

    # Configuration for checkpointing
    config = {
        "configurable": {
            "thread_id": f"proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    }

    # Run the graph
    print("\n" + "="*60)
    print("🔄 LANGGRAPH GOVERNANCE WORKFLOW")
    print("="*60)
    print(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
    print(f"Action: {action}")

    final_state = initial_state
    for event in app.stream(initial_state, config):
        for node_name, node_state in event.items():
            if isinstance(node_state, dict):
                final_state.update(node_state)

    return final_state


def print_workflow_diagram():
    """Print ASCII visualization of the workflow."""
    print("""
    +-----------------------------------------------------------+
    |           LANGGRAPH GOVERNANCE WORKFLOW (RULE-011)        |
    +-----------------------------------------------------------+

                          +---------+
                          |  START  |
                          +----+----+
                               |
                          +----v----+
                          | SUBMIT  |
                          +----+----+
                               |
                    +----------+----------+
                    |                     |
                [failed]              [continue]
                    |                     |
                    |              +------v------+
                    |              |   VALIDATE  |
                    |              +------+------+
                    |                     |
                    |          +----------+----------+
                    |          |                     |
                    |      [passed]              [failed]
                    |          |                     |
                    |    +-----v-----+               |
                    |    |   ASSESS  |               |
                    |    +-----+-----+               |
                    |          |                     |
                    |    +-----v-----+               |
                    |    |   VOTE    |               |
                    |    +-----+-----+               |
                    |          |                     |
                    |    +-----v-----+               |
                    |    |  DECIDE   |               |
                    |    +-----+-----+               |
                    |          |                     |
                    |    +-----+-----+               |
                    |    |           |               |
                    | [approved] [rejected]          |
                    |    |           |               |
                    | +--v-------+   |               |
                    | |IMPLEMENT |   |               |
                    | +----+-----+   |               |
                    |      |         |               |
                    |      |   +-----v-----+         |
                    |      |   |  REJECT   |<--------+
                    |      |   +-----+-----+
                    |      |         |
                    +------+---------+
                           |
                      +----v----+
                      |COMPLETE |
                      +----+----+
                           |
                       +---v---+
                       |  END  |
                       +-------+
    """)
