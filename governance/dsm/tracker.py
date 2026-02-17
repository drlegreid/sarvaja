"""DSM Tracker - RULE-012 Deep Sleep Protocol cycle tracking.

Per WORKFLOW-DSP-01-v1:
- Thread-safe singleton with lock
- Cycle lifecycle: start -> advance -> checkpoint -> complete
- Persistence delegated to tracker_persistence.py (DOC-SIZE-01-v1)

Created: 2024-12-24
Updated: 2026-02-09 - Split persistence to tracker_persistence.py
"""
import json
import logging
import threading
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pathlib import Path

from governance.dsm.phases import DSPPhase
from governance.dsm.models import DSMCycle, PhaseCheckpoint
from governance.dsm.validation import validate_phase_evidence
from governance.dsm.evidence import generate_evidence
from governance.dsm.memory import get_session_memory_payload as _get_memory_payload
from governance.dsm.tracker_persistence import (
    load_state, save_state, check_abandoned_cycle,
)

logger = logging.getLogger(__name__)

# Per WORKFLOW-DSP-01-v1: Thread lock for singleton access
_tracker_lock = threading.Lock()


class DSMTracker:
    """Tracks Deep Sleep Mode cycles through DSP phases."""

    def __init__(self, evidence_dir: str = None, state_file: str = None):
        """Initialize DSM Tracker with optional evidence_dir and state_file."""
        self.evidence_dir = Path(evidence_dir or "./evidence")
        self.state_file = Path(state_file or ".dsm_state.json")
        # BUG-337-TRACK-001: Per-instance lock for thread-safe method access
        self._lock = threading.Lock()

        self.current_cycle: Optional[DSMCycle] = None
        self.completed_cycles: List[DSMCycle] = []

        # Load state from file (delegated to persistence module)
        self.current_cycle = load_state(self.state_file)
        if self.current_cycle and check_abandoned_cycle(self.current_cycle):
            self.current_cycle = None
            self._save_state()

    def _save_state(self) -> None:
        """Save state to file (delegates to persistence module)."""
        save_state(self.state_file, self.current_cycle, len(self.completed_cycles))

    def start_cycle(self, batch_id: str = None) -> DSMCycle:
        """Start a new DSM cycle with optional batch_id."""
        # BUG-337-TRACK-001: Thread-safe access via per-instance lock
        with self._lock:
            return self._start_cycle_locked(batch_id)

    def _start_cycle_locked(self, batch_id: str = None) -> DSMCycle:
        # BUG-337-TRACK-002: Also accept "aborted" as restartable state
        if self.current_cycle and self.current_cycle.current_phase not in ("complete", "aborted"):
            raise ValueError("A cycle is already in progress. Complete or abort it first.")

        cycle_id = f"DSM-{date.today()}-{datetime.now().strftime('%H%M%S')}"

        self.current_cycle = DSMCycle(
            cycle_id=cycle_id,
            batch_id=batch_id,
            start_time=datetime.now().isoformat(),
            current_phase=DSPPhase.IDLE.value
        )

        self._save_state()
        return self.current_cycle

    def get_current_phase(self) -> DSPPhase:
        """Get current phase as enum."""
        if not self.current_cycle:
            return DSPPhase.IDLE
        # BUG-245-TRK-001: Guard against unknown/aborted phase values
        try:
            return DSPPhase(self.current_cycle.current_phase)
        except ValueError:
            return DSPPhase.IDLE

    def advance_phase(self, force: bool = False) -> DSPPhase:
        """Advance to next phase. Validates evidence unless force=True."""
        if not self.current_cycle:
            raise ValueError("No cycle in progress. Start one with start_cycle()")

        current = self.get_current_phase()
        next_phase = current.next_phase()

        if next_phase is None:
            raise ValueError("Cycle is complete. Cannot advance further.")

        # Validate evidence was produced (skip for IDLE phase)
        if current != DSPPhase.IDLE and not force:
            validation_error = validate_phase_evidence(self.current_cycle, current)
            if validation_error:
                raise ValueError(
                    f"Cannot advance from {current.value}: {validation_error}. "
                    f"Add checkpoint() or add_finding() before advancing."
                )

        # Record completion of current phase
        # BUG-231-006: Dedup to prevent progress_percent > 100%
        if current != DSPPhase.IDLE and current.value not in self.current_cycle.phases_completed:
            self.current_cycle.phases_completed.append(current.value)

        self.current_cycle.current_phase = next_phase.value

        self._save_state()
        return next_phase

    def go_to_phase(self, phase: DSPPhase) -> DSPPhase:
        """Jump to a specific phase (for non-linear workflows)."""
        if not self.current_cycle:
            raise ValueError("No cycle in progress. Start one with start_cycle()")

        if phase in (DSPPhase.IDLE, DSPPhase.COMPLETE):
            raise ValueError(f"Cannot jump to {phase.value}")

        current = self.get_current_phase()
        # BUG-DSM-DEDUP-001: Deduplicate to prevent progress_percent > 100%
        if current != DSPPhase.IDLE and current.value not in self.current_cycle.phases_completed:
            self.current_cycle.phases_completed.append(current.value)

        self.current_cycle.current_phase = phase.value
        self._save_state()
        return phase

    def checkpoint(self, description: str, metrics: Dict[str, Any] = None,
                   evidence: List[str] = None) -> PhaseCheckpoint:
        """Create a checkpoint in the current phase."""
        if not self.current_cycle:
            raise ValueError("No cycle in progress")

        cp = PhaseCheckpoint(
            phase=self.current_cycle.current_phase,
            timestamp=datetime.now().isoformat(),
            description=description,
            metrics=metrics or {},
            evidence=evidence or []
        )

        self.current_cycle.checkpoints.append(cp)
        self._save_state()
        return cp

    def add_finding(self, finding_type: str, description: str, severity: str = "MEDIUM",
                    related_rules: List[str] = None) -> Dict[str, Any]:
        """Add a finding (gap/orphan/conflict/improvement) during current phase.
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress")

        finding = {
            "id": f"FINDING-{len(self.current_cycle.findings) + 1:03d}",
            "type": finding_type,
            "description": description,
            "severity": severity,
            "phase": self.current_cycle.current_phase,
            "timestamp": datetime.now().isoformat(),
            "related_rules": related_rules or []
        }

        self.current_cycle.findings.append(finding)
        self._save_state()
        return finding

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Update cycle metrics.

        Args:
            metrics: Dictionary of metrics to update
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress")

        self.current_cycle.metrics.update(metrics)
        self._save_state()

    def complete_cycle(self) -> str:
        """
        Complete the current cycle and generate evidence.

        Returns:
            Path to generated evidence file
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress")

        # Mark complete
        current = self.get_current_phase()
        # BUG-231-006: Dedup phases_completed to prevent progress_percent > 100%
        if current != DSPPhase.IDLE and current not in (DSPPhase.COMPLETE, DSPPhase.REPORT):
            if current.value not in self.current_cycle.phases_completed:
                self.current_cycle.phases_completed.append(current.value)

        self.current_cycle.current_phase = DSPPhase.COMPLETE.value
        self.current_cycle.end_time = datetime.now().isoformat()

        # Generate evidence file
        evidence_path = generate_evidence(self.current_cycle, self.evidence_dir)

        # Archive cycle (retain last 50 to prevent unbounded growth)
        self.completed_cycles.append(self.current_cycle)
        if len(self.completed_cycles) > 50:
            self.completed_cycles = self.completed_cycles[-50:]
        self.current_cycle = None
        self._save_state()

        return evidence_path

    def abort_cycle(self, reason: str = None) -> None:
        """
        Abort the current cycle.

        Args:
            reason: Optional abort reason
        """
        if not self.current_cycle:
            return

        self.current_cycle.metrics["aborted"] = True
        self.current_cycle.metrics["abort_reason"] = reason or "Unknown"
        self.current_cycle.end_time = datetime.now().isoformat()
        self.current_cycle.current_phase = "aborted"

        # BUG-DSM-ABORT-001: Save BEFORE nulling current_cycle,
        # otherwise abort metadata is lost (writes null to disk)
        self._save_state()
        self.current_cycle = None

    def get_status(self) -> Dict[str, Any]:
        """
        Get current tracker status.

        Returns:
            Status dictionary
        """
        if not self.current_cycle:
            return {
                "active": False,
                "message": "No cycle in progress"
            }

        current_phase = self.get_current_phase()
        phases_order = DSPPhase.phase_order()
        completed_count = len(self.current_cycle.phases_completed)
        total_phases = len(phases_order)

        return {
            "active": True,
            "cycle_id": self.current_cycle.cycle_id,
            "batch_id": self.current_cycle.batch_id,
            "current_phase": current_phase.value,
            "phases_completed": self.current_cycle.phases_completed,
            "progress": f"{completed_count}/{total_phases}",
            # BUG-270-TRACKER-001: Guard against division by zero if phase_order() is empty
            "progress_percent": round(completed_count / total_phases * 100, 1) if total_phases else 0.0,
            "checkpoints_count": len(self.current_cycle.checkpoints),
            "findings_count": len(self.current_cycle.findings),
            "required_mcps": current_phase.required_mcps,
            "start_time": self.current_cycle.start_time
        }

    def get_session_memory_payload(self) -> Optional[Dict[str, Any]]:
        """Get payload for saving cycle context to claude-mem (P11.4)."""
        return _get_memory_payload(self.current_cycle)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tracker state to dictionary."""
        return {
            "current_cycle": self.current_cycle.to_dict() if self.current_cycle else None,
            "completed_cycles_count": len(self.completed_cycles),
            "evidence_dir": str(self.evidence_dir),
            "state_file": str(self.state_file)
        }

    def to_json(self) -> str:
        """Convert tracker state to JSON."""
        return json.dumps(self.to_dict(), indent=2)


# Global tracker instance (protected by _tracker_lock)
_tracker: Optional[DSMTracker] = None


def get_tracker(evidence_dir: str = None) -> DSMTracker:
    """Get or create global tracker instance.

    Per WORKFLOW-DSP-01-v1: Thread-safe singleton access with lock.
    """
    global _tracker
    with _tracker_lock:
        if _tracker is None:
            _tracker = DSMTracker(evidence_dir=evidence_dir)
        return _tracker


def reset_tracker() -> None:
    """Reset global tracker instance (for testing).

    Per WORKFLOW-DSP-01-v1: Thread-safe reset with lock.
    """
    global _tracker
    with _tracker_lock:
        _tracker = None
