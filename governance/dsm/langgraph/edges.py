"""
DSP LangGraph Conditional Edges
===============================
Router functions for DSP workflow conditional edges.

Per WORKFLOW-DSP-01-v1: DSP Workflow Stability Requirements
Per RULE-012: DSP Semantic Code Structure

Created: 2026-02-08
"""

from .state import DSPState


def check_start_status(state: DSPState) -> str:
    """Route after START based on initialization result.

    Returns:
        "audit" if started successfully
        "abort" if missing MCPs or other failure
    """
    if state.get("status") == "failed":
        return "abort"
    return "audit"


def check_audit_result(state: DSPState) -> str:
    """Route after AUDIT based on findings severity.

    Per WORKFLOW-DSP-01-v1: Skip to REPORT if critical gaps found.

    Returns:
        "hypothesize" for normal flow
        "skip_to_report" if critical gaps require immediate reporting
        "abort" if audit failed
    """
    if state.get("status") == "failed":
        return "abort"

    if state.get("has_critical_gaps"):
        return "skip_to_report"

    return "hypothesize"


def check_phase_status(state: DSPState) -> str:
    """Generic check for phase status.

    Returns:
        "continue" if running successfully
        "abort" if failed
    """
    if state.get("status") == "failed":
        return "abort"
    return "continue"


def check_validation_result(state: DSPState) -> str:
    """Route after VALIDATE based on test results.

    Per WORKFLOW-DSP-01-v1: Handle validation failures.

    Returns:
        "dream" if validation passed (normal flow)
        "report" if validation failed (skip dream, generate report)
        "abort" if phase execution failed
    """
    if state.get("status") == "failed":
        return "abort"

    if not state.get("validation_passed"):
        # Validation tests failed - skip DREAM, go to REPORT
        return "report"

    return "dream"


def check_should_skip_dream(state: DSPState) -> str:
    """Route before DREAM based on skip flag.

    Per WORKFLOW-DSP-01-v1: Skip DREAM for critical paths.

    Returns:
        "report" if dream should be skipped
        "dream" for normal flow
    """
    if state.get("should_skip_dream"):
        return "report"
    return "dream"


def check_report_status(state: DSPState) -> str:
    """Route after REPORT to completion.

    Returns:
        "complete" always (REPORT is the last real phase)
    """
    return "complete"
