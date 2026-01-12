"""
DSM Phase Validation
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Validates evidence requirements for each DSP phase.
"""
from typing import Optional, List, Dict, Any

from governance.dsm.phases import DSPPhase
from governance.dsm.models import DSMCycle, PhaseCheckpoint


# Phase-specific evidence requirements
PHASE_REQUIREMENTS = {
    DSPPhase.AUDIT: {
        "need_checkpoint_or_finding": True,
        "finding_types": ["gap", "issue", "improvement", "orphan"],
        "min_checkpoint_chars": 20,
        "description": "Audit must identify at least one gap, issue, or checkpoint"
    },
    DSPPhase.HYPOTHESIZE: {
        "need_checkpoint": True,
        "min_checkpoint_chars": 30,
        "description": "Hypothesis must be documented in checkpoint"
    },
    DSPPhase.MEASURE: {
        "need_checkpoint_with_metrics": True,
        "description": "Measurements must include metrics in checkpoint"
    },
    DSPPhase.OPTIMIZE: {
        "need_checkpoint": True,
        "min_checkpoint_chars": 20,
        "description": "Optimizations must be documented in checkpoint"
    },
    DSPPhase.VALIDATE: {
        "need_checkpoint": True,
        "min_checkpoint_chars": 10,
        "description": "Validation results must be documented"
    },
    DSPPhase.DREAM: {
        "need_checkpoint_or_finding": True,
        "min_checkpoint_chars": 10,
        "description": "Dream phase must produce discoveries or observations"
    },
    DSPPhase.REPORT: {
        # Report phase generates evidence automatically
        "need_checkpoint_or_finding": False,
        "description": "Report auto-generates evidence"
    }
}


def validate_phase_evidence(
    cycle: DSMCycle,
    phase: DSPPhase
) -> Optional[str]:
    """
    Validate that required evidence exists for a phase.

    Per TASK 3.1: Each phase MUST produce evidence.

    Args:
        cycle: The current DSM cycle
        phase: The phase to validate

    Returns:
        Error message if validation fails, None if valid
    """
    # Get checkpoints and findings for this phase
    phase_checkpoints = [
        cp for cp in cycle.checkpoints
        if cp.phase == phase.value
    ]
    phase_findings = [
        f for f in cycle.findings
        if f.get("phase") == phase.value
    ]

    req = PHASE_REQUIREMENTS.get(phase)
    if not req:
        return None  # Unknown phase, allow

    # Check requirements
    has_valid_checkpoint = any(
        len(cp.description) >= req.get("min_checkpoint_chars", 0)
        for cp in phase_checkpoints
    )
    has_valid_finding = len(phase_findings) > 0

    if req.get("need_checkpoint_with_metrics"):
        # Must have checkpoint with non-empty metrics
        has_metrics = any(
            cp.metrics and len(cp.metrics) > 0
            for cp in phase_checkpoints
        )
        if not has_metrics:
            return f"{phase.value.upper()}: Requires checkpoint with metrics"
        return None

    if req.get("need_checkpoint"):
        if not has_valid_checkpoint:
            return f"{phase.value.upper()}: Requires checkpoint (min {req.get('min_checkpoint_chars', 0)} chars)"
        return None

    if req.get("need_checkpoint_or_finding"):
        if not has_valid_checkpoint and not has_valid_finding:
            return f"{phase.value.upper()}: Requires checkpoint or finding"
        return None

    return None  # All checks passed
