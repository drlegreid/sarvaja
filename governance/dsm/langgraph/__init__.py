"""
DSP LangGraph Package
=====================
LangGraph-based workflow for Deep Sleep Protocol.

Per WORKFLOW-DSP-01-v1: DSP Workflow Stability Requirements
Per RULE-012: DSP Semantic Code Structure

Usage:
    from governance.dsm.langgraph import run_dsp_workflow, create_initial_state

    # Run a dry-run cycle
    result = run_dsp_workflow(dry_run=True)

    # Run with specific MCPs
    result = run_dsp_workflow(
        available_mcps=["claude-mem", "governance"],
        dry_run=False
    )

Created: 2026-02-08
"""

from .state import (
    DSPState,
    PhaseResult,
    create_initial_state,
    MIN_CHECKPOINT_CHARS,
    MIN_FINDING_COUNT,
    MIN_HYPOTHESIS_CHARS,
    CRITICAL_SEVERITY_THRESHOLD,
    MAX_CYCLE_HOURS,
    MAX_PHASE_RETRIES,
)

from .graph import (
    build_dsp_graph,
    run_dsp_workflow,
    print_dsp_workflow_diagram,
    LANGGRAPH_AVAILABLE,
)

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

__all__ = [
    # State
    "DSPState",
    "PhaseResult",
    "create_initial_state",

    # Constants
    "MIN_CHECKPOINT_CHARS",
    "MIN_FINDING_COUNT",
    "MIN_HYPOTHESIS_CHARS",
    "CRITICAL_SEVERITY_THRESHOLD",
    "MAX_CYCLE_HOURS",
    "MAX_PHASE_RETRIES",

    # Graph
    "build_dsp_graph",
    "run_dsp_workflow",
    "print_dsp_workflow_diagram",
    "LANGGRAPH_AVAILABLE",

    # Nodes
    "start_node",
    "audit_node",
    "hypothesize_node",
    "measure_node",
    "optimize_node",
    "validate_node",
    "dream_node",
    "report_node",
    "complete_node",
    "abort_node",
    "skip_to_report_node",

    # Edges
    "check_start_status",
    "check_audit_result",
    "check_phase_status",
    "check_validation_result",
    "check_should_skip_dream",
    "check_report_status",
]
