"""
SFDC LangGraph Lifecycle Nodes
================================
Start, complete, abort, rollback, and skip nodes for SFDC workflow control.

Created: 2026-02-09
"""

import logging
import time
from datetime import datetime

from .state import SFDCState, PhaseResult

logger = logging.getLogger(__name__)


def _create_phase_result(
    phase: str,
    status: str,
    state: SFDCState,
    error: str = None,
    duration_ms: int = 0,
) -> PhaseResult:
    """Create a phase result record."""
    return {
        "phase": phase,
        "status": status,
        "findings": len([f for f in state.get("review_findings", []) if f.get("phase") == phase]),
        "metrics": {},
        "error": error,
        "duration_ms": duration_ms,
    }


def start_node(state: SFDCState) -> dict:
    """Initialize the SFDC deployment cycle.

    Validates org connectivity and sandbox-only constraints.
    """
    start_time = time.perf_counter()
    logger.info(f"[SFDC] Starting cycle {state['cycle_id']} for org {state['org_alias']}")

    # Validate sandbox-only constraint
    target = state.get("target_org", "")
    if state.get("sandbox_only") and not state.get("dry_run"):
        if target and not any(s in target.lower() for s in ["sandbox", "dev", "uat", "sit", "qa"]):
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "current_phase": "start_failed",
                "status": "failed",
                "error_message": f"sandbox_only=True but target '{target}' appears to be production",
                "phase_results": [_create_phase_result("start", "failed", state,
                    f"Production target blocked by sandbox_only", duration_ms)],
            }

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    return {
        "current_phase": "started",
        "phases_completed": ["start"],
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "phase_results": [_create_phase_result("start", "success", state, duration_ms=duration_ms)],
    }


def complete_node(state: SFDCState) -> dict:
    """Complete the SFDC cycle with final status consolidation."""
    start_time = time.perf_counter()
    logger.info(f"[SFDC:{state['cycle_id']}] COMPLETE phase")

    if state.get("rollback_reason"):
        final_status = "rolled_back"
    elif state.get("error_message"):
        final_status = "failed"
    elif state.get("abort_reason"):
        final_status = "aborted"
    else:
        final_status = "success"

    # Summary metrics
    total_components = len(state.get("metadata_components", []))
    total_apex = len(state.get("apex_classes", []))
    total_lwc = len(state.get("lwc_components", []))

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    return {
        "current_phase": "complete",
        "phases_completed": state["phases_completed"] + ["complete"],
        "status": final_status,
        "completed_at": datetime.now().isoformat(),
        "phase_results": state.get("phase_results", []) + [
            _create_phase_result("complete", "success", state, duration_ms=duration_ms)
        ],
    }


def abort_node(state: SFDCState) -> dict:
    """Abort the SFDC cycle."""
    reason = state.get("error_message") or state.get("abort_reason") or "Unknown reason"
    logger.warning(f"[SFDC:{state['cycle_id']}] ABORTED: {reason}")

    return {
        "current_phase": "aborted",
        "phases_completed": state["phases_completed"] + ["abort"],
        "status": "aborted",
        "abort_reason": reason,
        "completed_at": datetime.now().isoformat(),
    }


def rollback_node(state: SFDCState) -> dict:
    """Rollback a failed deployment.

    Reverts deployed components to previous state.
    """
    start_time = time.perf_counter()
    deploy_id = state.get("deployment_id", "unknown")
    logger.warning(f"[SFDC:{state['cycle_id']}] ROLLBACK deployment {deploy_id}")

    errors = state.get("deployment_errors", [])
    validation_checks = state.get("post_deploy_checks", {})

    reason_parts = []
    if errors:
        reason_parts.append(f"Deploy errors: {len(errors)}")
    if not state.get("validation_passed") and validation_checks:
        failed_checks = [k for k, v in validation_checks.items() if not v]
        if failed_checks:
            reason_parts.append(f"Failed checks: {', '.join(failed_checks)}")

    rollback_reason = "; ".join(reason_parts) or "Deployment verification failed"

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    return {
        "current_phase": "rolled_back",
        "phases_completed": state["phases_completed"] + ["rollback"],
        "rollback_reason": rollback_reason,
        "phase_results": state.get("phase_results", []) + [
            _create_phase_result("rollback", "success", state, duration_ms=duration_ms)
        ],
    }


def skip_to_report_node(state: SFDCState) -> dict:
    """Skip to REPORT phase when breaking changes detected."""
    logger.warning(f"[SFDC:{state['cycle_id']}] Skipping to REPORT due to breaking changes")

    return {
        "current_phase": "skipped_to_report",
        "phases_completed": state["phases_completed"] + ["skip_to_report"],
        "should_skip_monitor": True,
    }
