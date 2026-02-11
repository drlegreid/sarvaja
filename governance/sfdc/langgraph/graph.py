"""
SFDC LangGraph Graph Construction
===================================
Compilation and execution of SFDC workflow graph.

Graph structure:
    START -> start -> discover -> [develop | skip_to_report | abort]
                                   |
    develop -> test -> [review | loop_to_develop | abort]
                        |
    review -> [deploy | loop_to_develop | abort]
                |
    deploy -> [validate | rollback | abort]
                |
    validate -> [monitor | rollback | skip_monitor]
                  |
    monitor -> report -> complete -> END

    rollback -> report -> complete -> END
    skip_to_report -> report -> complete -> END

Created: 2026-02-09
Per DOC-SIZE-01-v1: Fallback runner + diagram in graph_fallback.py.
"""

import logging
from typing import Optional

from .state import SFDCState, create_initial_state
from .nodes import (
    start_node,
    discover_node,
    develop_node,
    run_tests_node,
    review_node,
    deploy_node,
    validate_node,
    monitor_node,
    report_node,
    complete_node,
    abort_node,
    rollback_node,
    skip_to_report_node,
)
from .edges import (
    check_discover_status,
    check_phase_status,
    check_test_result,
    check_review_result,
    check_deploy_result,
    check_validation_result,
)
from .graph_fallback import (  # noqa: F401 — re-export
    run_fallback_workflow,
    print_sfdc_workflow_diagram,
)

logger = logging.getLogger(__name__)

# Try to import LangGraph, fallback to mock if not available
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    START, END = "START", "END"

    class StateGraph:
        """Mock StateGraph for when LangGraph is not installed."""

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
            return CompiledMockGraph(self)

    class CompiledMockGraph:
        """Mock compiled graph that executes nodes in sequence."""

        def __init__(self, graph):
            self.graph = graph

        def stream(self, initial_state, config):
            """Execute nodes in linear fallback mode."""
            state = initial_state.copy()
            yield {"start": state}

    class MemorySaver:
        """Mock memory saver."""
        pass


def build_sfdc_graph() -> StateGraph:
    """Build the SFDC workflow graph."""
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available - using mock graph")

    graph = StateGraph(SFDCState)

    node_mapping = [
        ("start", start_node),
        ("discover", discover_node),
        ("develop", develop_node),
        ("test", run_tests_node),
        ("review", review_node),
        ("deploy", deploy_node),
        ("validate", validate_node),
        ("monitor", monitor_node),
        ("report", report_node),
        ("complete", complete_node),
        ("abort", abort_node),
        ("rollback", rollback_node),
        ("skip_to_report", skip_to_report_node),
    ]

    for name, func in node_mapping:
        graph.add_node(name, func)

    graph.add_edge(START, "start")

    graph.add_conditional_edges(
        "start", check_phase_status,
        {"continue": "discover", "abort": "abort"},
    )

    graph.add_conditional_edges(
        "discover", check_discover_status,
        {"develop": "develop", "skip_to_report": "skip_to_report", "abort": "abort"},
    )

    graph.add_edge("skip_to_report", "report")

    graph.add_conditional_edges(
        "develop", check_phase_status,
        {"continue": "test", "abort": "abort"},
    )

    graph.add_conditional_edges(
        "test", check_test_result,
        {"continue": "review", "loop_to_develop": "develop", "abort": "abort"},
    )

    graph.add_conditional_edges(
        "review", check_review_result,
        {"continue": "deploy", "loop_to_develop": "develop", "abort": "abort"},
    )

    graph.add_conditional_edges(
        "deploy", check_deploy_result,
        {"validate": "validate", "rollback": "rollback", "abort": "abort"},
    )

    graph.add_conditional_edges(
        "validate", check_validation_result,
        {"monitor": "monitor", "rollback": "rollback", "skip_monitor": "report", "abort": "abort"},
    )

    graph.add_conditional_edges(
        "monitor", check_phase_status,
        {"continue": "report", "abort": "abort"},
    )

    graph.add_edge("rollback", "report")
    graph.add_edge("report", "complete")
    graph.add_edge("abort", "complete")
    graph.add_edge("complete", END)

    return graph


def run_sfdc_workflow(
    org_alias: str = "default",
    target_org: Optional[str] = None,
    dry_run: bool = True,
    sandbox_only: bool = True,
) -> SFDCState:
    """Run the SFDC deployment workflow."""
    graph = build_sfdc_graph()
    initial_state = create_initial_state(
        org_alias=org_alias,
        target_org=target_org,
        dry_run=dry_run,
        sandbox_only=sandbox_only,
    )

    if not LANGGRAPH_AVAILABLE:
        logger.info("[SFDC] Running in fallback mode (LangGraph not available)")
        return run_fallback_workflow(graph, initial_state)

    app = graph.compile(checkpointer=MemorySaver())

    config = {
        "configurable": {
            "thread_id": f"sfdc_{initial_state['cycle_id']}"
        }
    }

    logger.info(f"\n{'='*60}")
    logger.info("SFDC LANGGRAPH WORKFLOW")
    logger.info(f"{'='*60}")
    logger.info(f"Cycle: {initial_state['cycle_id']}")
    logger.info(f"Org: {org_alias} -> {target_org or org_alias}")
    logger.info(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")

    final_state = initial_state.copy()

    for event in app.stream(initial_state, config):
        for node_name, node_state in event.items():
            if isinstance(node_state, dict):
                final_state.update(node_state)
                logger.info(f"[{node_name}] -> {node_state.get('current_phase', 'unknown')}")

    logger.info(f"\n{'='*60}")
    logger.info(f"SFDC COMPLETE: {final_state.get('status', 'unknown')}")
    logger.info(f"Phases: {' -> '.join(final_state.get('phases_completed', []))}")
    logger.info(f"{'='*60}\n")

    return final_state
