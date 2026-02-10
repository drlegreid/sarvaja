"""
SFDC LangGraph Package
=======================
LangGraph-based workflow for Salesforce Development Lifecycle.

Usage:
    from governance.sfdc.langgraph import run_sfdc_workflow, create_initial_state

    # Run a dry-run cycle
    result = run_sfdc_workflow(org_alias="mydev", dry_run=True)

    # Deploy to sandbox
    result = run_sfdc_workflow(
        org_alias="mydev",
        target_org="mysandbox",
        sandbox_only=True,
    )

Created: 2026-02-09
"""

from .state import (
    SFDCState,
    PhaseResult,
    MetadataComponent,
    create_initial_state,
    MIN_CODE_COVERAGE,
    RECOMMENDED_COVERAGE,
    MAX_DEPLOY_RETRIES,
    MAX_CYCLE_HOURS,
    MAX_COMPONENTS_PER_DEPLOY,
    BREAKING_CHANGE_THRESHOLD,
)

from .graph import (
    build_sfdc_graph,
    run_sfdc_workflow,
    print_sfdc_workflow_diagram,
    LANGGRAPH_AVAILABLE,
)

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

__all__ = [
    # State
    "SFDCState",
    "PhaseResult",
    "MetadataComponent",
    "create_initial_state",

    # Constants
    "MIN_CODE_COVERAGE",
    "RECOMMENDED_COVERAGE",
    "MAX_DEPLOY_RETRIES",
    "MAX_CYCLE_HOURS",
    "MAX_COMPONENTS_PER_DEPLOY",
    "BREAKING_CHANGE_THRESHOLD",

    # Graph
    "build_sfdc_graph",
    "run_sfdc_workflow",
    "print_sfdc_workflow_diagram",
    "LANGGRAPH_AVAILABLE",

    # Nodes
    "start_node",
    "discover_node",
    "develop_node",
    "test_node",
    "review_node",
    "deploy_node",
    "validate_node",
    "monitor_node",
    "report_node",
    "complete_node",
    "abort_node",
    "rollback_node",
    "skip_to_report_node",

    # Edges
    "check_discover_status",
    "check_phase_status",
    "check_test_result",
    "check_review_result",
    "check_deploy_result",
    "check_validation_result",
]
