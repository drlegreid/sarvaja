"""
RF-004: Robot Framework Library for DSM Tracker.

Wraps governance/dsm_tracker.py for Robot Framework tests.
Per RULE-012: Deep Sleep Protocol (DSP) governance tracking.
"""

import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class DSMTrackerLibrary:
    """Robot Framework library for DSM Tracker functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._tmpdir = None
        self._tracker = None

    def create_temp_directory(self) -> str:
        """Create a temporary directory for testing."""
        self._tmpdir = tempfile.mkdtemp()
        return self._tmpdir

    def cleanup_temp_directory(self):
        """Clean up temporary directory."""
        import shutil
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None

    # DSPPhase enum tests
    def dsp_phase_exists(self) -> bool:
        """Check if DSPPhase enum exists."""
        try:
            from governance.dsm_tracker import DSPPhase
            return DSPPhase is not None
        except ImportError:
            return False

    def get_dsp_phase_value(self, phase_name: str) -> str:
        """Get the value of a DSPPhase enum member."""
        from governance.dsm_tracker import DSPPhase
        return getattr(DSPPhase, phase_name.upper()).value

    def get_phase_order(self) -> List[str]:
        """Get the phase order list."""
        from governance.dsm_tracker import DSPPhase
        return [p.value for p in DSPPhase.phase_order()]

    def get_phase_required_mcps(self, phase_name: str) -> List[str]:
        """Get required MCPs for a phase."""
        from governance.dsm_tracker import DSPPhase
        phase = getattr(DSPPhase, phase_name.upper())
        return phase.required_mcps

    # PhaseCheckpoint tests
    def create_phase_checkpoint(
        self,
        phase: str,
        timestamp: str,
        description: str,
        metrics: Dict = None,
        evidence: List = None
    ) -> Dict[str, Any]:
        """Create a PhaseCheckpoint and return as dict."""
        from governance.dsm_tracker import PhaseCheckpoint

        kwargs = {"phase": phase, "timestamp": timestamp, "description": description}
        if metrics:
            kwargs["metrics"] = metrics
        if evidence:
            kwargs["evidence"] = evidence

        cp = PhaseCheckpoint(**kwargs)
        return {
            "phase": cp.phase,
            "timestamp": cp.timestamp,
            "description": cp.description,
            "metrics": cp.metrics,
            "evidence": cp.evidence
        }

    # DSMCycle tests
    def create_dsm_cycle(
        self,
        cycle_id: str,
        batch_id: str = None,
        current_phase: str = "idle"
    ) -> Dict[str, Any]:
        """Create a DSMCycle and return as dict."""
        from governance.dsm_tracker import DSMCycle

        kwargs = {"cycle_id": cycle_id}
        if batch_id:
            kwargs["batch_id"] = batch_id
        if current_phase:
            kwargs["current_phase"] = current_phase

        cycle = DSMCycle(**kwargs)
        return cycle.to_dict()

    # DSMTracker tests
    def create_dsm_tracker(self, evidence_dir: str = None) -> bool:
        """Create a DSMTracker instance."""
        from governance.dsm_tracker import DSMTracker

        if not evidence_dir and self._tmpdir:
            evidence_dir = self._tmpdir

        state_file = str(Path(evidence_dir) / ".dsm_state.json")
        self._tracker = DSMTracker(evidence_dir=evidence_dir, state_file=state_file)
        return self._tracker is not None

    def tracker_has_no_active_cycle(self) -> bool:
        """Check if tracker has no active cycle."""
        return self._tracker.current_cycle is None

    def get_tracker_status(self) -> Dict[str, Any]:
        """Get tracker status."""
        return self._tracker.get_status()

    def tracker_to_dict(self) -> Dict[str, Any]:
        """Convert tracker to dictionary."""
        return self._tracker.to_dict()

    def tracker_to_json(self) -> str:
        """Convert tracker to JSON string."""
        return self._tracker.to_json()

    # Global tracker tests
    def get_global_tracker(self, evidence_dir: str = None) -> bool:
        """Get global tracker instance."""
        from governance.dsm_tracker import get_tracker, DSMTracker

        kwargs = {}
        if evidence_dir:
            kwargs["evidence_dir"] = evidence_dir
        elif self._tmpdir:
            kwargs["evidence_dir"] = self._tmpdir

        tracker = get_tracker(**kwargs)
        return isinstance(tracker, DSMTracker)

    def reset_global_tracker(self):
        """Reset the global tracker."""
        from governance.dsm_tracker import reset_tracker
        reset_tracker()

    def global_trackers_are_same_instance(self) -> bool:
        """Check if repeated get_tracker calls return same instance."""
        from governance.dsm_tracker import get_tracker
        tracker1 = get_tracker()
        tracker2 = get_tracker()
        return tracker1 is tracker2

    def global_trackers_are_different_after_reset(self) -> bool:
        """Check if tracker is different after reset."""
        from governance.dsm_tracker import get_tracker, reset_tracker
        tracker1 = get_tracker()
        reset_tracker()
        tracker2 = get_tracker()
        same = tracker1 is not tracker2
        reset_tracker()
        return same
