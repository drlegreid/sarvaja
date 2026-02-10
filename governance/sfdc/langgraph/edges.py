"""
SFDC LangGraph Conditional Edges
=================================
Router functions for SFDC workflow conditional edges.

Created: 2026-02-09
"""

from .state import SFDCState, MAX_DEPLOY_RETRIES


def check_discover_status(state: SFDCState) -> str:
    """Route after DISCOVER based on initialization and metadata scan.

    Returns:
        "develop" if discovery successful
        "skip_to_report" if breaking changes detected
        "abort" if discovery failed
    """
    if state.get("status") == "failed":
        return "abort"

    if state.get("has_breaking_changes"):
        return "skip_to_report"

    return "develop"


def check_phase_status(state: SFDCState) -> str:
    """Generic check for phase status.

    Returns:
        "continue" if running successfully
        "abort" if failed
    """
    if state.get("status") == "failed":
        return "abort"
    return "continue"


def check_test_result(state: SFDCState) -> str:
    """Route after TEST based on coverage and results.

    Returns:
        "continue" if tests pass and coverage met
        "loop_to_develop" if tests fail but retries remain
        "abort" if tests fail and retries exhausted
    """
    if state.get("status") == "failed":
        return "abort"

    if not state.get("coverage_met"):
        retry_count = state.get("retry_count", 0)
        if retry_count < MAX_DEPLOY_RETRIES:
            return "loop_to_develop"
        return "abort"

    return "continue"


def check_review_result(state: SFDCState) -> str:
    """Route after REVIEW based on security scan and findings.

    Returns:
        "continue" if review passed
        "loop_to_develop" if security issues found, retries remain
        "abort" if critical security issues
    """
    if state.get("status") == "failed":
        return "abort"

    if not state.get("security_scan_passed"):
        retry_count = state.get("retry_count", 0)
        if retry_count < MAX_DEPLOY_RETRIES:
            return "loop_to_develop"
        return "abort"

    return "continue"


def check_deploy_result(state: SFDCState) -> str:
    """Route after DEPLOY based on deployment status.

    Returns:
        "validate" if deployment succeeded
        "rollback" if deployment failed
        "abort" if critical failure
    """
    if state.get("status") == "failed":
        return "abort"

    if state.get("deployment_status") == "Failed":
        return "rollback"

    return "validate"


def check_validation_result(state: SFDCState) -> str:
    """Route after VALIDATE based on post-deploy checks.

    Returns:
        "monitor" if validation passed
        "rollback" if validation failed
        "skip_monitor" if should skip monitoring
    """
    if state.get("status") == "failed":
        return "abort"

    if not state.get("validation_passed"):
        return "rollback"

    if state.get("should_skip_monitor"):
        return "skip_monitor"

    return "monitor"
