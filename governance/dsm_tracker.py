"""
DSM Tracker (DEPRECATED - use governance.dsm package)
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

This file is kept for backward compatibility.
Import from governance.dsm instead:

    from governance.dsm import DSMTracker, DSPPhase, get_tracker

Per: RULE-012 (DSP), RULE-032 (File Size Limit)
"""
import warnings

# Re-export from modular package for backward compatibility
from governance.dsm import (
    DSPPhase,
    DSMCycle,
    PhaseCheckpoint,
    validate_phase_evidence,
    PHASE_REQUIREMENTS,
    generate_evidence,
    DSMTracker,
    get_tracker,
    reset_tracker,
)

__all__ = [
    "DSPPhase",
    "DSMCycle",
    "PhaseCheckpoint",
    "validate_phase_evidence",
    "PHASE_REQUIREMENTS",
    "generate_evidence",
    "DSMTracker",
    "get_tracker",
    "reset_tracker",
]

# Emit deprecation warning on import
warnings.warn(
    "governance.dsm_tracker is deprecated. "
    "Use 'from governance.dsm import DSMTracker' instead.",
    DeprecationWarning,
    stacklevel=2
)
