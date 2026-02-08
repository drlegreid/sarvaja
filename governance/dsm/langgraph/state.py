"""
DSP LangGraph State Schema
==========================
State types and constants for Deep Sleep Protocol workflow.

Per WORKFLOW-DSP-01-v1: DSP Workflow Stability Requirements
Per RULE-012: DSP Semantic Code Structure

Created: 2026-02-08
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any


class PhaseResult(TypedDict):
    """Result from a single phase execution."""
    phase: str
    status: Literal["success", "failed", "skipped"]
    checkpoints: int
    findings: int
    metrics: Dict[str, Any]
    evidence_files: List[str]
    error: Optional[str]
    duration_ms: int


class DSPState(TypedDict):
    """State that flows through the DSP workflow.

    Per WORKFLOW-DSP-01-v1: Typed state for workflow stability.
    """

    # Cycle identity
    cycle_id: str
    batch_id: Optional[str]

    # Progress tracking
    current_phase: str
    phases_completed: List[str]
    phase_results: List[PhaseResult]

    # Evidence collection
    checkpoints: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    evidence_files: List[str]

    # Phase-specific data
    audit_gaps: List[str]
    audit_orphans: List[str]
    hypotheses: List[str]
    measurements: Dict[str, float]
    optimizations_applied: List[str]
    validation_results: Dict[str, Any]
    dream_insights: List[str]

    # Decision routing
    has_critical_gaps: bool
    validation_passed: bool
    should_skip_dream: bool

    # MCP availability
    available_mcps: List[str]
    missing_mcps: List[str]

    # Execution mode
    dry_run: bool
    force_advance: bool

    # Status
    status: Literal["pending", "running", "success", "failed", "aborted"]
    error_message: Optional[str]
    abort_reason: Optional[str]

    # Timestamps
    started_at: Optional[str]
    completed_at: Optional[str]


# =============================================================================
# CONSTANTS (WORKFLOW-DSP-01-v1)
# =============================================================================

# Phase validation thresholds
MIN_CHECKPOINT_CHARS = 20
MIN_FINDING_COUNT = 1
MIN_HYPOTHESIS_CHARS = 30
MIN_MEASUREMENT_METRICS = 1

# Cycle limits
MAX_CYCLE_HOURS = 24  # Auto-abort threshold
MAX_PHASE_RETRIES = 3

# Severity thresholds for routing
CRITICAL_SEVERITY_THRESHOLD = 3  # Skip to REPORT if >= 3 CRITICAL findings


def create_initial_state(
    batch_id: Optional[str] = None,
    dry_run: bool = False,
    available_mcps: Optional[List[str]] = None,
    force_advance: bool = False,
) -> DSPState:
    """Create initial DSP cycle state.

    Args:
        batch_id: Optional batch identifier for grouping cycles
        dry_run: If True, skip actual modifications
        available_mcps: List of available MCP servers
        force_advance: If True, skip MCP availability checks

    Returns:
        Initial DSPState for workflow execution
    """
    from datetime import datetime

    cycle_id = f"DSM-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"

    return {
        # Identity
        "cycle_id": cycle_id,
        "batch_id": batch_id,

        # Progress
        "current_phase": "idle",
        "phases_completed": [],
        "phase_results": [],

        # Evidence
        "checkpoints": [],
        "findings": [],
        "metrics": {},
        "evidence_files": [],

        # Phase data
        "audit_gaps": [],
        "audit_orphans": [],
        "hypotheses": [],
        "measurements": {},
        "optimizations_applied": [],
        "validation_results": {},
        "dream_insights": [],

        # Decision routing
        "has_critical_gaps": False,
        "validation_passed": False,
        "should_skip_dream": False,

        # MCP availability
        "available_mcps": available_mcps or [],
        "missing_mcps": [],

        # Execution
        "dry_run": dry_run,
        "force_advance": force_advance,

        # Status
        "status": "pending",
        "error_message": None,
        "abort_reason": None,

        # Timestamps
        "started_at": None,
        "completed_at": None,
    }
