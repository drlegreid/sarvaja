"""
SFDC LangGraph Graph Construction
===================================
Compilation and execution of SFDC workflow graph.

Graph structure:
    START → start → discover → [develop | skip_to_report | abort]
                                   ↓
    develop → test → [review | loop_to_develop | abort]
                        ↓
    review → [deploy | loop_to_develop | abort]
                ↓
    deploy → [validate | rollback | abort]
                ↓
    validate → [monitor | rollback | skip_monitor]
                  ↓
    monitor → report → complete → END

    rollback → report → complete → END
    skip_to_report → report → complete → END

Created: 2026-02-09
"""

import logging
from typing import Optional, List
from datetime import datetime

from .state import SFDCState, create_initial_state, MAX_DEPLOY_RETRIES
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
    """Build the SFDC workflow graph.

    Returns:
        StateGraph configured with SFDC phases and routing
    """
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available - using mock graph")

    graph = StateGraph(SFDCState)

    # Add all nodes
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

    # Entry point
    graph.add_edge(START, "start")

    # Start → discover (always)
    graph.add_conditional_edges(
        "start",
        check_phase_status,
        {"continue": "discover", "abort": "abort"}
    )

    # Discover → [develop | skip_to_report | abort]
    graph.add_conditional_edges(
        "discover",
        check_discover_status,
        {
            "develop": "develop",
            "skip_to_report": "skip_to_report",
            "abort": "abort",
        }
    )

    # skip_to_report → report
    graph.add_edge("skip_to_report", "report")

    # Develop → test
    graph.add_conditional_edges(
        "develop",
        check_phase_status,
        {"continue": "test", "abort": "abort"}
    )

    # Test → [review | loop_to_develop | abort]
    graph.add_conditional_edges(
        "test",
        check_test_result,
        {
            "continue": "review",
            "loop_to_develop": "develop",
            "abort": "abort",
        }
    )

    # Review → [deploy | loop_to_develop | abort]
    graph.add_conditional_edges(
        "review",
        check_review_result,
        {
            "continue": "deploy",
            "loop_to_develop": "develop",
            "abort": "abort",
        }
    )

    # Deploy → [validate | rollback | abort]
    graph.add_conditional_edges(
        "deploy",
        check_deploy_result,
        {
            "validate": "validate",
            "rollback": "rollback",
            "abort": "abort",
        }
    )

    # Validate → [monitor | rollback | skip_monitor]
    graph.add_conditional_edges(
        "validate",
        check_validation_result,
        {
            "monitor": "monitor",
            "rollback": "rollback",
            "skip_monitor": "report",
            "abort": "abort",
        }
    )

    # Monitor → report
    graph.add_conditional_edges(
        "monitor",
        check_phase_status,
        {"continue": "report", "abort": "abort"}
    )

    # Rollback → report
    graph.add_edge("rollback", "report")

    # Report → complete
    graph.add_edge("report", "complete")

    # Abort → complete (cleanup)
    graph.add_edge("abort", "complete")

    # Complete → END
    graph.add_edge("complete", END)

    return graph


def run_sfdc_workflow(
    org_alias: str = "default",
    target_org: Optional[str] = None,
    dry_run: bool = True,
    sandbox_only: bool = True,
) -> SFDCState:
    """Run the SFDC deployment workflow.

    Args:
        org_alias: Source Salesforce org alias
        target_org: Target org for deployment
        dry_run: If True, simulate without actual deployment
        sandbox_only: If True, only deploy to sandbox orgs

    Returns:
        Final SFDCState after workflow completion
    """
    graph = build_sfdc_graph()
    initial_state = create_initial_state(
        org_alias=org_alias,
        target_org=target_org,
        dry_run=dry_run,
        sandbox_only=sandbox_only,
    )

    if not LANGGRAPH_AVAILABLE:
        logger.info("[SFDC] Running in fallback mode (LangGraph not available)")
        return _run_fallback_workflow(graph, initial_state)

    # Compile with checkpointer for crash recovery
    app = graph.compile(checkpointer=MemorySaver())

    config = {
        "configurable": {
            "thread_id": f"sfdc_{initial_state['cycle_id']}"
        }
    }

    logger.info(f"\n{'='*60}")
    logger.info(f"SFDC LANGGRAPH WORKFLOW")
    logger.info(f"{'='*60}")
    logger.info(f"Cycle: {initial_state['cycle_id']}")
    logger.info(f"Org: {org_alias} → {target_org or org_alias}")
    logger.info(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")

    final_state = initial_state.copy()

    for event in app.stream(initial_state, config):
        for node_name, node_state in event.items():
            if isinstance(node_state, dict):
                final_state.update(node_state)
                logger.info(f"[{node_name}] → {node_state.get('current_phase', 'unknown')}")

    logger.info(f"\n{'='*60}")
    logger.info(f"SFDC COMPLETE: {final_state.get('status', 'unknown')}")
    logger.info(f"Phases: {' → '.join(final_state.get('phases_completed', []))}")
    logger.info(f"{'='*60}\n")

    return final_state


def _run_fallback_workflow(graph: StateGraph, initial_state: SFDCState) -> SFDCState:
    """Run workflow in fallback mode without LangGraph.

    Executes nodes in linear sequence with basic routing.
    """
    state = initial_state.copy()

    phase_sequence = [
        "start",
        "discover",
        "develop",
        "test",
        "review",
        "deploy",
        "validate",
        "monitor",
        "report",
        "complete",
    ]

    i = 0
    while i < len(phase_sequence):
        node_name = phase_sequence[i]

        if node_name not in graph.nodes:
            i += 1
            continue

        # Check abort condition
        if state.get("status") == "failed":
            if "abort" in graph.nodes:
                state.update(graph.nodes["abort"](state))
            if "complete" in graph.nodes:
                state.update(graph.nodes["complete"](state))
            break

        # Check skip conditions
        if node_name == "monitor" and state.get("should_skip_monitor"):
            i += 1
            continue

        # Check breaking changes skip
        if node_name == "develop" and state.get("has_breaking_changes"):
            if "skip_to_report" in graph.nodes:
                state.update(graph.nodes["skip_to_report"](state))
            # Jump to report
            i = phase_sequence.index("report")
            continue

        # Execute node
        try:
            result = graph.nodes[node_name](state)
            state.update(result)
        except Exception as e:
            logger.error(f"[SFDC] Node {node_name} failed: {e}")
            state["status"] = "failed"
            state["error_message"] = str(e)
            break

        # Check for deployment failure → rollback
        if node_name == "deploy" and state.get("deployment_status") == "Failed":
            if "rollback" in graph.nodes:
                state.update(graph.nodes["rollback"](state))
            i = phase_sequence.index("report")
            continue

        # Check for validation failure → rollback
        if node_name == "validate" and not state.get("validation_passed"):
            if "rollback" in graph.nodes:
                state.update(graph.nodes["rollback"](state))
            i = phase_sequence.index("report")
            continue

        # Loop back on test failure
        if node_name == "test" and not state.get("coverage_met"):
            retry_count = state.get("retry_count", 0)
            if retry_count < MAX_DEPLOY_RETRIES:
                state["retry_count"] = retry_count + 1
                logger.info(
                    f"[SFDC] Tests failed, looping to develop "
                    f"(retry {retry_count + 1}/{MAX_DEPLOY_RETRIES})"
                )
                i = phase_sequence.index("develop")
                continue

        i += 1

    return state


def print_sfdc_workflow_diagram():
    """Print ASCII visualization of SFDC workflow."""
    print("""
SFDC LangGraph Workflow:

    START
      │
      ▼
    [start]──failed──►[abort]
      │                  │
      │ success          │
      ▼                  │
    [discover]           │
      │                  │
      ├─breaking─►[skip_to_report]──┐
      │                              │
      │ normal                       │
      ▼                              │
    [develop]◄────────────────┐      │
      │                       │      │
      ▼                       │      │
    [test]                    │      │
      │                  loop │      │
      ├─fail(retry<3)────────┘      │
      │                              │
      │ pass                         │
      ▼                              │
    [review]                         │
      │                              │
      ├─security fail(retry<3)──►[develop]
      │                              │
      │ pass                         │
      ▼                              │
    [deploy]                         │
      │                              │
      ├─failed──►[rollback]──────────┤
      │                              │
      │ success                      │
      ▼                              │
    [validate]                       │
      │                              │
      ├─failed──►[rollback]──────────┤
      │                              │
      │ passed                       │
      ▼                              │
    [monitor]                        │
      │                              │
      └─────────►[report]◄───────────┘
                    │
                    ▼
               [complete]
                    │
                    ▼
                   END
    """)
