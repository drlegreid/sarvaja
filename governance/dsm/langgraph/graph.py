"""
DSP LangGraph Graph Construction
================================
Compilation and execution of DSP workflow graph.

Per WORKFLOW-DSP-01-v1: DSP Workflow Stability Requirements
Per RULE-012: DSP Semantic Code Structure
Per DOC-SIZE-01-v1: Mock classes & diagram in graph_mock.py.

Graph structure:
    START → start → [abort | audit]
                       ↓
    [critical gaps] → skip_to_report → report → complete → END
                       ↓
                   hypothesize → measure → optimize → validate
                       ↑                                 ↓
                       └── loop_to_hypothesize ──────── [failed, retries < MAX]
                                                         ↓
                                    [failed, no retries] → report → complete → END
                                        ↓
                                      dream → report → complete → END

Created: 2026-02-08
"""

import logging
from typing import Optional, List
from datetime import datetime

from .state import DSPState, create_initial_state
from .nodes import (
    start_node,
    audit_node,
    hypothesize_node,
    measure_node,
    optimize_node,
    validate_node,
    dream_node,
    report_node,
    complete_node,
    abort_node,
    skip_to_report_node,
)
from .edges import (
    check_start_status,
    check_audit_result,
    check_phase_status,
    check_validation_result,
    check_should_skip_dream,
    check_report_status,
)

# Re-export mock diagram for backward compatibility
from .graph_mock import print_dsp_workflow_diagram  # noqa: F401

logger = logging.getLogger(__name__)

# Try to import LangGraph, fallback to mock if not available
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    START, END = "START", "END"

    from .graph_mock import StateGraph, MemorySaver  # noqa: F811


def build_dsp_graph() -> StateGraph:
    """Build the DSP workflow graph.

    Per WORKFLOW-DSP-01-v1: Conditional routing for workflow stability.

    Returns:
        StateGraph configured with DSP phases and routing
    """
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available - using mock graph")

    graph = StateGraph(DSPState)

    # Add all nodes (both real and mock graphs get nodes)
    node_mapping = [
        ("start", start_node),
        ("audit", audit_node),
        ("hypothesize", hypothesize_node),
        ("measure", measure_node),
        ("optimize", optimize_node),
        ("validate", validate_node),
        ("dream", dream_node),
        ("report", report_node),
        ("complete", complete_node),
        ("abort", abort_node),
        ("skip_to_report", skip_to_report_node),
    ]

    for name, func in node_mapping:
        graph.add_node(name, func)

    # Entry point
    graph.add_edge(START, "start")

    # Start → [audit | abort]
    graph.add_conditional_edges(
        "start",
        check_start_status,
        {"audit": "audit", "abort": "abort"}
    )

    # Audit → [hypothesize | skip_to_report | abort]
    graph.add_conditional_edges(
        "audit",
        check_audit_result,
        {"hypothesize": "hypothesize", "skip_to_report": "skip_to_report", "abort": "abort"}
    )

    # skip_to_report → report
    graph.add_edge("skip_to_report", "report")

    # Linear phases: hypothesize → measure → optimize → validate
    graph.add_conditional_edges(
        "hypothesize",
        check_phase_status,
        {"continue": "measure", "abort": "abort"}
    )

    graph.add_conditional_edges(
        "measure",
        check_phase_status,
        {"continue": "optimize", "abort": "abort"}
    )

    graph.add_conditional_edges(
        "optimize",
        check_phase_status,
        {"continue": "validate", "abort": "abort"}
    )

    # Validate → [dream | loop_to_hypothesize | report | abort]
    # Per GAP-WORKFLOW-LOOP-001: Loop back on validation failure if retries remain
    graph.add_conditional_edges(
        "validate",
        check_validation_result,
        {
            "dream": "dream",
            "loop_to_hypothesize": "hypothesize",
            "report": "report",
            "abort": "abort",
        }
    )

    # Dream → report
    graph.add_conditional_edges(
        "dream",
        check_phase_status,
        {"continue": "report", "abort": "abort"}
    )

    # Report → complete
    graph.add_edge("report", "complete")

    # Abort → complete (for cleanup)
    graph.add_edge("abort", "complete")

    # Complete → END
    graph.add_edge("complete", END)

    return graph


def run_dsp_workflow(
    batch_id: Optional[str] = None,
    dry_run: bool = True,
    available_mcps: Optional[List[str]] = None,
    force_advance: bool = False,
) -> DSPState:
    """Run the DSP workflow.

    Per WORKFLOW-DSP-01-v1: Main entry point for DSP execution.

    Args:
        batch_id: Optional batch identifier
        dry_run: If True, skip actual modifications
        available_mcps: List of available MCP servers
        force_advance: If True, skip MCP availability checks

    Returns:
        Final DSPState after workflow completion
    """
    graph = build_dsp_graph()
    initial_state = create_initial_state(
        batch_id=batch_id,
        dry_run=dry_run,
        available_mcps=available_mcps or ["claude-mem", "governance", "sequential-thinking"],
        force_advance=force_advance,
    )

    if not LANGGRAPH_AVAILABLE:
        logger.info("[DSP] Running in fallback mode (LangGraph not available)")
        return _run_fallback_workflow(graph, initial_state)

    # Compile with checkpointer for crash recovery
    app = graph.compile(checkpointer=MemorySaver())

    config = {
        "configurable": {
            "thread_id": f"dsp_{initial_state['cycle_id']}"
        }
    }

    logger.info(f"\n{'='*60}")
    logger.info(f"🌙 DSP LANGGRAPH WORKFLOW")
    logger.info(f"{'='*60}")
    logger.info(f"Cycle: {initial_state['cycle_id']}")
    logger.info(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
    logger.info(f"Batch: {batch_id or 'None'}")

    final_state = initial_state.copy()

    for event in app.stream(initial_state, config):
        for node_name, node_state in event.items():
            if isinstance(node_state, dict):
                final_state.update(node_state)
                logger.info(f"[{node_name}] → {node_state.get('current_phase', 'unknown')}")

    logger.info(f"\n{'='*60}")
    logger.info(f"DSP COMPLETE: {final_state.get('status', 'unknown')}")
    logger.info(f"Phases: {' → '.join(final_state.get('phases_completed', []))}")
    logger.info(f"{'='*60}\n")

    return final_state


def _run_fallback_workflow(graph: StateGraph, initial_state: DSPState) -> DSPState:
    """Run workflow in fallback mode without LangGraph.

    Executes nodes in linear sequence with basic routing.
    Per GAP-WORKFLOW-LOOP-001: Supports retry loops (validate → hypothesize).
    """
    from .state import MAX_PHASE_RETRIES

    state = initial_state.copy()

    # Define linear execution order
    phase_sequence = [
        "start",
        "audit",
        "hypothesize",
        "measure",
        "optimize",
        "validate",
        "dream",
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
        if node_name == "dream" and state.get("should_skip_dream"):
            i += 1
            continue

        # Execute node
        try:
            result = graph.nodes[node_name](state)
            state.update(result)
        except Exception as e:
            logger.error(f"[DSP] Node {node_name} failed: {e}")
            state["status"] = "failed"
            state["error_message"] = str(e)
            break

        # GAP-WORKFLOW-LOOP-001: Check for retry loop after validate
        if node_name == "validate" and not state.get("validation_passed"):
            retry_count = state.get("retry_count", 0)
            if retry_count < MAX_PHASE_RETRIES:
                state["retry_count"] = retry_count + 1
                logger.info(
                    f"[DSP] Validation failed, looping back to hypothesize "
                    f"(retry {retry_count + 1}/{MAX_PHASE_RETRIES})"
                )
                # Jump back to hypothesize (index 2)
                i = phase_sequence.index("hypothesize")
                continue

        i += 1

    return state
