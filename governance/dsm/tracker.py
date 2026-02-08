"""DSM Tracker - RULE-012 Deep Sleep Protocol cycle tracking.

Per WORKFLOW-DSP-01-v1:
- Thread-safe singleton with lock
- Atomic file writes (temp + rename)
- Abandoned cycle detection (>24h auto-abort)
- Graceful state load failure handling

Created: 2024-12-24
Updated: 2026-02-08 - Added thread safety and stability fixes
"""
import json
import logging
import os
import shutil
import tempfile
import threading
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

from governance.dsm.phases import DSPPhase
from governance.dsm.models import DSMCycle, PhaseCheckpoint
from governance.dsm.validation import validate_phase_evidence
from governance.dsm.evidence import generate_evidence

logger = logging.getLogger(__name__)
from governance.dsm.memory import get_session_memory_payload as _get_memory_payload

# Per WORKFLOW-DSP-01-v1: Thread lock for singleton access
_tracker_lock = threading.Lock()

# Per WORKFLOW-DSP-01-v1: Auto-abort threshold for abandoned cycles
ABANDONED_CYCLE_HOURS = 24


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
        """Load state from file if exists.

        Per WORKFLOW-DSP-01-v1:
        - Auto-aborts cycles abandoned >24h
        - Backs up corrupted state files
        - Gracefully handles load failures
        """
        if not self.state_file.exists():
            return

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

                # Per WORKFLOW-DSP-01-v1: Auto-abort abandoned cycles
                self._check_abandoned_cycle()

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to load DSM state: {e}. Backing up corrupted file.")
            # Backup corrupted state file
            backup_path = self.state_file.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
            try:
                shutil.copy2(self.state_file, backup_path)
                logger.info(f"Corrupted state backed up to {backup_path}")
            except Exception:
                pass
            # Start fresh
            self.current_cycle = None

    def _check_abandoned_cycle(self) -> None:
        """Auto-abort cycles that have been abandoned for >24h.

        Per WORKFLOW-DSP-01-v1: Stale cycles indicate forgotten cleanup.
        """
        if not self.current_cycle or self.current_cycle.current_phase == "complete":
            return

        start_time_str = self.current_cycle.start_time
        if not start_time_str:
            return

        try:
            # Parse start time (handle both naive and aware datetimes)
            if "+" in start_time_str or start_time_str.endswith("Z"):
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            else:
                start_time = datetime.fromisoformat(start_time_str)
                start_time = start_time.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            age_hours = (now - start_time).total_seconds() / 3600

            if age_hours > ABANDONED_CYCLE_HOURS:
                logger.warning(
                    f"Auto-aborting abandoned cycle {self.current_cycle.cycle_id} "
                    f"(age: {age_hours:.1f}h > {ABANDONED_CYCLE_HOURS}h threshold)"
                )
                self.current_cycle.metrics["auto_aborted"] = True
                self.current_cycle.metrics["abort_reason"] = f"Abandoned for {age_hours:.1f}h"
                self.current_cycle.end_time = now.isoformat()
                self.current_cycle.current_phase = "aborted"
                self.current_cycle = None
                self._save_state()
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse cycle start time for age check: {e}")

    def _save_state(self) -> None:
        """Save state to file using atomic write.

        Per WORKFLOW-DSP-01-v1: Uses temp file + atomic rename to prevent
        corruption on crash during write.
        """
        state = {
            "current_cycle": self.current_cycle.to_dict() if self.current_cycle else None,
            "completed_count": len(self.completed_cycles),
            "last_updated": datetime.now().isoformat()
        }

        # Atomic write: write to temp, then rename
        dir_path = self.state_file.parent
        dir_path.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            suffix=".tmp",
            prefix=".dsm_state_",
            dir=str(dir_path)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            # Atomic rename (POSIX guarantees atomicity on same filesystem)
            os.replace(temp_path, self.state_file)
        except Exception as e:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            logger.error(f"Failed to save DSM state: {e}")
            raise

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
