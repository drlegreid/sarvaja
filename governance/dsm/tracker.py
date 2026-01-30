"""DSM Tracker - RULE-012 Deep Sleep Protocol cycle tracking. Created: 2024-12-24"""
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pathlib import Path

from governance.dsm.phases import DSPPhase
from governance.dsm.models import DSMCycle, PhaseCheckpoint
from governance.dsm.validation import validate_phase_evidence
from governance.dsm.evidence import generate_evidence

logger = logging.getLogger(__name__)
from governance.dsm.memory import get_session_memory_payload as _get_memory_payload


class DSMTracker:
    """Tracks Deep Sleep Mode cycles through DSP phases."""

    def __init__(self, evidence_dir: str = None, state_file: str = None):
        """Initialize DSM Tracker with optional evidence_dir and state_file."""
        self.evidence_dir = Path(evidence_dir or "./evidence")
        self.state_file = Path(state_file or ".dsm_state.json")

        self.current_cycle: Optional[DSMCycle] = None
        self.completed_cycles: List[DSMCycle] = []

        # Load state if exists
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file if exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)

                if state.get("current_cycle"):
                    cycle_data = state["current_cycle"]
                    self.current_cycle = DSMCycle(
                        cycle_id=cycle_data["cycle_id"],
                        batch_id=cycle_data.get("batch_id"),
                        start_time=cycle_data.get("start_time"),
                        end_time=cycle_data.get("end_time"),
                        current_phase=cycle_data.get("current_phase", "idle"),
                        phases_completed=cycle_data.get("phases_completed", []),
                        checkpoints=[
                            PhaseCheckpoint(**cp) for cp in cycle_data.get("checkpoints", [])
                        ],
                        findings=cycle_data.get("findings", []),
                        metrics=cycle_data.get("metrics", {})
                    )
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Failed to load DSM state: {e}")

    def _save_state(self) -> None:
        """Save state to file."""
        state = {
            "current_cycle": self.current_cycle.to_dict() if self.current_cycle else None,
            "completed_count": len(self.completed_cycles),
            "last_updated": datetime.now().isoformat()
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def start_cycle(self, batch_id: str = None) -> DSMCycle:
        """Start a new DSM cycle with optional batch_id."""
        if self.current_cycle and self.current_cycle.current_phase != "complete":
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
        return DSPPhase(self.current_cycle.current_phase)

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
        if current != DSPPhase.IDLE:
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
        if current != DSPPhase.IDLE:
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
        if current != DSPPhase.IDLE and current not in (DSPPhase.COMPLETE, DSPPhase.REPORT):
            self.current_cycle.phases_completed.append(current.value)

        self.current_cycle.current_phase = DSPPhase.COMPLETE.value
        self.current_cycle.end_time = datetime.now().isoformat()

        # Generate evidence file
        evidence_path = generate_evidence(self.current_cycle, self.evidence_dir)

        # Archive cycle
        self.completed_cycles.append(self.current_cycle)
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

        # Save but don't archive
        self.current_cycle = None
        self._save_state()

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
            "progress_percent": round(completed_count / total_phases * 100, 1),
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


# Global tracker instance
_tracker: Optional[DSMTracker] = None


def get_tracker(evidence_dir: str = None) -> DSMTracker:
    """Get or create global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = DSMTracker(evidence_dir=evidence_dir)
    return _tracker


def reset_tracker() -> None:
    """Reset global tracker instance (for testing)."""
    global _tracker
    _tracker = None
