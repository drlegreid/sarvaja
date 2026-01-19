"""LangGraph Graph Construction: compilation and execution. Per RULE-011, GAP-FILE-009."""

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

try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    START, END = "START", "END"
    class StateGraph:
        def __init__(self, state_type):
            self.state_type, self.nodes, self.edges, self.conditional_edges = state_type, {}, [], []
        def add_node(self, name, func): self.nodes[name] = func
        def add_edge(self, from_node, to_node): self.edges.append((from_node, to_node))
        def add_conditional_edges(self, from_node, condition, mapping): self.conditional_edges.append((from_node, condition, mapping))
        def compile(self, checkpointer=None): return CompiledGraph(self)
    class CompiledGraph:
        def __init__(self, graph): self.graph = graph
        def stream(self, initial_state, config):
            state = initial_state.copy()
            yield {"start": state}
    class MemorySaver: pass

def build_proposal_graph() -> StateGraph:
    """Build the governance proposal workflow graph."""
    if not LANGGRAPH_AVAILABLE:
        return StateGraph(ProposalState)
    graph = StateGraph(ProposalState)
    for name, func in [("submit", submit_node), ("validate", validate_node), ("assess", assess_node),
                       ("vote", vote_node), ("decide", decide_node), ("implement", implement_node),
                       ("complete", complete_node), ("reject", reject_node)]:
        graph.add_node(name, func)
    graph.add_edge(START, "submit")
    graph.add_conditional_edges("submit", check_status, {"continue": "validate", "reject": "reject"})
    graph.add_conditional_edges("validate", check_validation, {"assess": "assess", "reject": "reject"})
    graph.add_edge("assess", "vote")
    graph.add_edge("vote", "decide")
    graph.add_conditional_edges("decide", check_decision, {"implement": "implement", "reject": "reject"})
    graph.add_edge("implement", "complete")
    graph.add_edge("reject", "complete")
    graph.add_edge("complete", END)
    return graph

def create_initial_state(action: Literal["create", "modify", "deprecate"], hypothesis: str,
                         evidence: List[str], submitter_id: str = "AGENT-001",
                         submitter_trust_score: float = 0.8, rule_id: Optional[str] = None,
                         directive: Optional[str] = None, dry_run: bool = True) -> ProposalState:
    """Create initial proposal state."""
    return {"proposal_id": "", "action": action, "rule_id": rule_id, "hypothesis": hypothesis,
            "evidence": evidence, "directive": directive, "submitter_id": submitter_id,
            "submitter_trust_score": submitter_trust_score, "current_phase": "start",
            "phases_completed": [], "validation_passed": False, "validation_errors": [],
            "impact_score": 0.0, "risk_level": "LOW", "affected_rules": [], "recommendations": [],
            "votes": [], "votes_for": 0.0, "votes_against": 0.0, "quorum_reached": False,
            "threshold_met": False, "decision": "pending", "decision_reasoning": "",
            "dry_run": dry_run, "changes_applied": [], "rollback_available": False,
            "status": "pending", "error_message": None, "started_at": None, "completed_at": None}

def run_proposal_workflow(action: Literal["create", "modify", "deprecate"], hypothesis: str,
                          evidence: List[str], submitter_id: str = "AGENT-001",
                          submitter_trust_score: float = 0.8, rule_id: Optional[str] = None,
                          directive: Optional[str] = None, dry_run: bool = True) -> ProposalState:
    """Run the proposal workflow."""
    graph = build_proposal_graph()
    if not LANGGRAPH_AVAILABLE:
        state = create_initial_state(action, hypothesis, evidence, submitter_id,
                                     submitter_trust_score, rule_id, directive, dry_run)
        for node_name in ["submit", "validate", "assess", "vote", "decide", "implement", "complete"]:
            if node_name in graph.nodes:
                state.update(graph.nodes[node_name](state))
                if state.get("status") == "failed":
                    state.update(reject_node(state))
                    state.update(complete_node(state))
                    break
        return state
    app = graph.compile(checkpointer=MemorySaver())
    initial_state = create_initial_state(action, hypothesis, evidence, submitter_id,
                                         submitter_trust_score, rule_id, directive, dry_run)
    config = {"configurable": {"thread_id": f"proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}}
    print(f"\n{'='*60}\n🔄 LANGGRAPH GOVERNANCE WORKFLOW\n{'='*60}\nMode: {'DRY-RUN' if dry_run else 'EXECUTE'} | Action: {action}")
    final_state = initial_state
    for event in app.stream(initial_state, config):
        for node_name, node_state in event.items():
            if isinstance(node_state, dict):
                final_state.update(node_state)
    return final_state

def print_workflow_diagram():
    """Print ASCII visualization: START→SUBMIT→VALIDATE→ASSESS→VOTE→DECIDE→IMPLEMENT/REJECT→COMPLETE→END."""
    print("Workflow: START→SUBMIT→[fail→REJECT | continue→VALIDATE→[fail→REJECT | pass→ASSESS→VOTE→DECIDE→[approve→IMPLEMENT | reject→REJECT]→COMPLETE→END]")
