"""Orchestrator graph construction and execution.

Per WORKFLOW-ORCH-01-v1: Builds the continuous loop graph
GATE -> BACKLOG -> SPEC -> IMPLEMENT -> VALIDATE -> (INJECT | COMPLETE_CYCLE)
with retry and park_task branches.

Uses mock StateGraph (same lightweight pattern as DSP/SFDC workflows).
"""

from typing import Any, Dict

from governance.workflows.orchestrator.state import (
    create_initial_state,
    add_to_backlog,
)
from governance.workflows.orchestrator.nodes import (
    gate_node,
    backlog_node,
    spec_node,
    implement_node,
    validate_node,
    inject_node,
    complete_cycle_node,
    park_task_node,
    certify_node,
    complete_node,
)
from governance.workflows.orchestrator.edges import (
    check_gate_decision,
    check_validation_result,
)


class MockStateGraph:
    """Lightweight graph that tracks nodes and edges for execution."""

    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self._edges = []
        self._conditional_edges = []
        self._entry_point = None

    def add_node(self, name: str, func):
        self.nodes[name] = func

    def add_edge(self, source: str, target: str):
        self._edges.append((source, target))

    def add_conditional_edges(self, source, condition_fn, mapping):
        self._conditional_edges.append((source, condition_fn, mapping))

    def set_entry_point(self, name: str):
        self._entry_point = name

    def compile(self):
        return self


def build_orchestrator_graph() -> MockStateGraph:
    """Build the orchestrator workflow graph with all nodes and edges."""
    graph = MockStateGraph()

    graph.add_node("gate", gate_node)
    graph.add_node("backlog", backlog_node)
    graph.add_node("spec", spec_node)
    graph.add_node("implement", implement_node)
    graph.add_node("validate", validate_node)
    graph.add_node("inject", inject_node)
    graph.add_node("complete_cycle", complete_cycle_node)
    graph.add_node("park_task", park_task_node)
    graph.add_node("certify", certify_node)
    graph.add_node("complete", complete_node)

    graph.set_entry_point("gate")

    graph.add_conditional_edges(
        "gate", check_gate_decision,
        {"backlog": "backlog", "complete": "certify"},
    )
    graph.add_edge("backlog", "spec")
    graph.add_edge("spec", "implement")
    graph.add_edge("implement", "validate")
    graph.add_conditional_edges(
        "validate", check_validation_result,
        {
            "complete_cycle": "complete_cycle",
            "inject": "inject",
            "loop_to_spec": "spec",
            "park_task": "park_task",
        },
    )
    graph.add_edge("inject", "complete_cycle")
    graph.add_edge("complete_cycle", "gate")
    graph.add_edge("park_task", "gate")
    graph.add_edge("certify", "complete")

    return graph.compile()


def _run_fallback_workflow(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the orchestrator loop without LangGraph runtime."""
    # BUG-ORCH-LOOP-001: Hard safety cap prevents infinite loop if gate/budget logic fails
    _MAX_ITERATIONS = state.get("max_cycles", 100) * 3  # 3x max_cycles as safety margin
    _iteration = 0
    _retrying = False
    while _iteration < _MAX_ITERATIONS:
        _iteration += 1

        if not _retrying:
            result = gate_node(state)
            state.update(result)

            decision = check_gate_decision(state)
            if decision == "complete":
                state.update(certify_node(state))
                state.update(complete_node(state))
                break

            state.update(backlog_node(state))

        _retrying = False
        state.update(spec_node(state))
        state.update(implement_node(state))
        state.update(validate_node(state))

        route = check_validation_result(state)

        if route == "inject":
            state.update(inject_node(state))
            state.update(complete_cycle_node(state))
        elif route == "complete_cycle":
            state.update(complete_cycle_node(state))
        elif route == "loop_to_spec":
            # BUG-ORCH-RETRY-001: Retry must re-spec same task, not pop new from backlog
            state["retry_count"] = state.get("retry_count", 0) + 1
            _retrying = True
            continue
        elif route == "park_task":
            state.update(park_task_node(state))
    else:
        # Safety cap reached — force completion
        state["gate_decision"] = "stop"
        state["safety_cap_reached"] = True

    return state


def run_orchestrator(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full orchestrator loop."""
    return _run_fallback_workflow(state)


def run_single_cycle(
    task_id: str,
    description: str,
    dry_run: bool = True,
    _simulate_validation_failure: bool = False,
) -> Dict[str, Any]:
    """Run a single spec->impl->validate cycle for one task."""
    state = create_initial_state(max_cycles=1, dry_run=dry_run)
    state = add_to_backlog(state, task_id, "HIGH", description)
    if _simulate_validation_failure:
        state["_simulate_validation_failure"] = True
    return _run_fallback_workflow(state)
