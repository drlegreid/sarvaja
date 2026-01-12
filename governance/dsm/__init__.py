"""
DSM Tracker Package - Deep Sleep Mode Cycle Tracking
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Implements RULE-012 (Deep Sleep Protocol) cycle tracking with:
- Phase transitions: AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE → DREAM → REPORT
- Evidence collection per phase
- MCP integration for phase-specific tools
- Cycle metrics and checkpoints
- Session memory integration (P11.4) for claude-mem context persistence

Per: RULE-012 (DSP), RULE-017 (Cross-Workspace Patterns), RULE-024 (AMNESIA Protocol)

Usage:
    from governance.dsm import DSMTracker, DSPPhase, get_tracker

    tracker = get_tracker()
    tracker.start_cycle("1001-1100")
    tracker.advance_phase()  # AUDIT
    tracker.checkpoint("Audited modules")
    evidence = tracker.complete_cycle()
"""

from governance.dsm.phases import DSPPhase
from governance.dsm.models import DSMCycle, PhaseCheckpoint
from governance.dsm.validation import validate_phase_evidence, PHASE_REQUIREMENTS
from governance.dsm.evidence import generate_evidence
from governance.dsm.tracker import DSMTracker, get_tracker, reset_tracker

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
