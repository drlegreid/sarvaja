"""
DSP LangGraph Lifecycle Nodes
==============================
Start, complete, abort, and skip nodes for DSP workflow control flow.

Per WORKFLOW-DSP-01-v1: DSP Workflow Stability Requirements
Per DOC-SIZE-01-v1: Modularized from nodes.py (572 lines)

Created: 2026-02-08
"""

import logging
import time
from datetime import datetime

from .state import DSPState, PhaseResult

logger = logging.getLogger(__name__)


def _create_phase_result(
    phase: str,
    status: str,
    state: DSPState,
    error: str = None,
    duration_ms: int = 0,
) -> PhaseResult:
    """Create a phase result record."""
    return {
        "phase": phase,
        "status": status,
        "checkpoints": len([c for c in state.get("checkpoints", []) if c.get("phase") == phase]),
        "findings": len([f for f in state.get("findings", []) if f.get("phase") == phase]),
        "metrics": state.get("metrics", {}).get(phase, {}),
        "evidence_files": state.get("evidence_files", []),
        "error": error,
        "duration_ms": duration_ms,
    }


def start_node(state: DSPState) -> dict:
    """Initialize the DSP cycle.

    Per WORKFLOW-DSP-01-v1: Validates MCP availability before starting.
    """
    start_time = time.perf_counter()
    logger.info(f"[DSP] Starting cycle {state['cycle_id']}")

    # Check required MCPs for first phase (AUDIT)
    required_mcps = ["claude-mem", "governance"]
    missing = [m for m in required_mcps if m not in state.get("available_mcps", [])]

    if missing and not state.get("force_advance"):
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "current_phase": "start_failed",
            "status": "failed",
            "error_message": f"Missing required MCPs for AUDIT phase: {missing}",
            "missing_mcps": missing,
            "phase_results": [_create_phase_result("start", "failed", state, f"Missing MCPs: {missing}", duration_ms)],
        }

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    return {
        "current_phase": "started",
        "phases_completed": ["start"],
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "phase_results": [_create_phase_result("start", "success", state, duration_ms=duration_ms)],
    }


def complete_node(state: DSPState) -> dict:
    """Complete the DSP cycle.

    Per WORKFLOW-DSP-01-v1: Final state consolidation.
    """
    start_time = time.perf_counter()
    logger.info(f"[DSP:{state['cycle_id']}] COMPLETE phase")

    # Determine final status
    if state.get("error_message"):
        final_status = "failed"
    elif state.get("abort_reason"):
        final_status = "aborted"
    else:
        final_status = "success"

    # Calculate summary metrics
    total_findings = len(state.get("findings", []))
    total_optimizations = len(state.get("optimizations_applied", []))

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    return {
        "current_phase": "complete",
        "phases_completed": state["phases_completed"] + ["complete"],
        "status": final_status,
        "completed_at": datetime.now().isoformat(),
        "metrics": {
            **state.get("metrics", {}),
            "total_findings": total_findings,
            "total_optimizations": total_optimizations,
            "phases_completed_count": len(state.get("phases_completed", [])) + 1,
        },
        "phase_results": state.get("phase_results", []) + [
            _create_phase_result("complete", "success", state, duration_ms=duration_ms)
        ],
    }


def abort_node(state: DSPState) -> dict:
    """Abort the DSP cycle.

    Per WORKFLOW-DSP-01-v1: Clean abort with reason tracking.
    """
    logger.warning(f"[DSP:{state['cycle_id']}] ABORTED: {state.get('error_message') or state.get('abort_reason')}")

    return {
        "current_phase": "aborted",
        "phases_completed": state["phases_completed"] + ["abort"],
        "status": "aborted",
        "abort_reason": state.get("error_message") or state.get("abort_reason") or "Unknown reason",
        "completed_at": datetime.now().isoformat(),
    }


def skip_to_report_node(state: DSPState) -> dict:
    """Skip to REPORT phase when critical gaps found.

    Per WORKFLOW-DSP-01-v1: Conditional routing for critical issues.
    """
    logger.warning(f"[DSP:{state['cycle_id']}] Skipping to REPORT due to critical gaps")

    return {
        "current_phase": "skipped_to_report",
        "phases_completed": state["phases_completed"] + ["skip_to_report"],
        "should_skip_dream": True,
    }
