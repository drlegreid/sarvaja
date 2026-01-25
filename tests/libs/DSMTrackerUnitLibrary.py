"""
Robot Framework Library for DSMTracker Unit Tests.

Per RULE-012: Deep Sleep Protocol.
Migrated from tests/test_dsm_tracker_unit.py
"""
import json
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerUnitLibrary:
    """Library for testing DSMTracker core classes."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # DSPPhase Enum Tests
    # =============================================================================

    @keyword("DSP Phase Enum Exists")
    def dsp_phase_enum_exists(self):
        """DSPPhase enum exists and is importable."""
        try:
            from governance.dsm_tracker import DSPPhase
            return {"exists": DSPPhase is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSP Phase Has All Phases")
    def dsp_phase_has_all_phases(self):
        """DSPPhase has all expected phases."""
        try:
            from governance.dsm_tracker import DSPPhase

            expected = ["idle", "audit", "hypothesize", "measure",
                        "optimize", "validate", "dream", "report", "complete"]

            all_present = True
            for phase_name in expected:
                try:
                    DSPPhase(phase_name)
                except ValueError:
                    all_present = False
                    break

            return {"all_present": all_present}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSP Phase Values Are Lowercase")
    def dsp_phase_values_are_lowercase(self):
        """DSPPhase values are lowercase strings."""
        try:
            from governance.dsm_tracker import DSPPhase

            return {
                "idle_correct": DSPPhase.IDLE.value == "idle",
                "audit_correct": DSPPhase.AUDIT.value == "audit",
                "hypothesize_correct": DSPPhase.HYPOTHESIZE.value == "hypothesize",
                "measure_correct": DSPPhase.MEASURE.value == "measure",
                "optimize_correct": DSPPhase.OPTIMIZE.value == "optimize",
                "validate_correct": DSPPhase.VALIDATE.value == "validate",
                "dream_correct": DSPPhase.DREAM.value == "dream",
                "report_correct": DSPPhase.REPORT.value == "report",
                "complete_correct": DSPPhase.COMPLETE.value == "complete"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Phase Order Returns List")
    def phase_order_returns_list(self):
        """phase_order returns list of phases."""
        try:
            from governance.dsm_tracker import DSPPhase

            order = DSPPhase.phase_order()

            return {
                "is_list": isinstance(order, list),
                "length_7": len(order) == 7,
                "no_idle": DSPPhase.IDLE not in order,
                "no_complete": DSPPhase.COMPLETE not in order
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Phase Order Is Correct Sequence")
    def phase_order_is_correct_sequence(self):
        """phase_order is in correct sequence."""
        try:
            from governance.dsm_tracker import DSPPhase

            order = DSPPhase.phase_order()

            return {
                "audit_first": order[0] == DSPPhase.AUDIT,
                "hypothesize_second": order[1] == DSPPhase.HYPOTHESIZE,
                "measure_third": order[2] == DSPPhase.MEASURE,
                "optimize_fourth": order[3] == DSPPhase.OPTIMIZE,
                "validate_fifth": order[4] == DSPPhase.VALIDATE,
                "dream_sixth": order[5] == DSPPhase.DREAM,
                "report_seventh": order[6] == DSPPhase.REPORT
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # PhaseCheckpoint Tests
    # =============================================================================

    @keyword("Checkpoint Creation Works")
    def checkpoint_creation_works(self):
        """PhaseCheckpoint creates with required fields."""
        try:
            from governance.dsm_tracker import PhaseCheckpoint

            cp = PhaseCheckpoint(
                phase="audit",
                timestamp="2024-12-24T12:00:00",
                description="Audited 5 modules"
            )

            return {
                "phase_correct": cp.phase == "audit",
                "timestamp_correct": cp.timestamp == "2024-12-24T12:00:00",
                "description_correct": cp.description == "Audited 5 modules"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Checkpoint Has Default Metrics")
    def checkpoint_has_default_metrics(self):
        """PhaseCheckpoint has default empty metrics."""
        try:
            from governance.dsm_tracker import PhaseCheckpoint

            cp = PhaseCheckpoint(
                phase="audit",
                timestamp="2024-12-24T12:00:00",
                description="Test"
            )

            return {"metrics_empty": cp.metrics == {}}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Checkpoint Has Default Evidence")
    def checkpoint_has_default_evidence(self):
        """PhaseCheckpoint has default empty evidence list."""
        try:
            from governance.dsm_tracker import PhaseCheckpoint

            cp = PhaseCheckpoint(
                phase="audit",
                timestamp="2024-12-24T12:00:00",
                description="Test"
            )

            return {"evidence_empty": cp.evidence == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # DSMCycle Tests
    # =============================================================================

    @keyword("Cycle Creation Works")
    def cycle_creation_works(self):
        """DSMCycle creates with cycle_id."""
        try:
            from governance.dsm_tracker import DSMCycle

            cycle = DSMCycle(cycle_id="DSM-2024-12-24-120000")

            return {
                "id_correct": cycle.cycle_id == "DSM-2024-12-24-120000",
                "phase_idle": cycle.current_phase == "idle"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Cycle Has Default Empty Lists")
    def cycle_has_default_empty_lists(self):
        """DSMCycle has default empty lists."""
        try:
            from governance.dsm_tracker import DSMCycle

            cycle = DSMCycle(cycle_id="TEST-001")

            return {
                "phases_empty": cycle.phases_completed == [],
                "checkpoints_empty": cycle.checkpoints == [],
                "findings_empty": cycle.findings == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Cycle To Dict Works")
    def cycle_to_dict_works(self):
        """DSMCycle converts to dictionary."""
        try:
            from governance.dsm_tracker import DSMCycle

            cycle = DSMCycle(
                cycle_id="TEST-001",
                batch_id="1001-1100",
                current_phase="audit"
            )

            d = cycle.to_dict()

            return {
                "id_correct": d["cycle_id"] == "TEST-001",
                "batch_correct": d["batch_id"] == "1001-1100",
                "phase_correct": d["current_phase"] == "audit",
                "checkpoints_is_list": isinstance(d["checkpoints"], list)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # DSMTracker Initialization Tests
    # =============================================================================

    @keyword("Tracker Class Exists")
    def tracker_class_exists(self):
        """DSMTracker class exists and is importable."""
        try:
            from governance.dsm_tracker import DSMTracker
            return {"exists": DSMTracker is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Tracker Creates With Defaults")
    def tracker_creates_with_defaults(self):
        """DSMTracker creates with default paths."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                return {
                    "no_cycle": tracker.current_cycle is None,
                    "completed_empty": tracker.completed_cycles == []
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Tracker Starts With No Active Cycle")
    def tracker_starts_with_no_active_cycle(self):
        """DSMTracker starts with no active cycle."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                status = tracker.get_status()
                return {
                    "no_cycle": tracker.current_cycle is None,
                    "not_active": status["active"] is False
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Serialization Tests
    # =============================================================================

    @keyword("Tracker To Dict Returns Dict")
    def tracker_to_dict_returns_dict(self):
        """to_dict returns dictionary."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                d = tracker.to_dict()

                return {
                    "is_dict": isinstance(d, dict),
                    "has_current_cycle": "current_cycle" in d,
                    "has_completed": "completed_cycles_count" in d
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Tracker To JSON Returns Valid JSON")
    def tracker_to_json_returns_valid_json(self):
        """to_json returns valid JSON string."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                json_str = tracker.to_json()
                parsed = json.loads(json_str)

                return {
                    "valid_json": True,
                    "no_cycle": parsed["current_cycle"] is None
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    # =============================================================================
    # Global Tracker Functions
    # =============================================================================

    @keyword("Get Tracker Returns Tracker")
    def get_tracker_returns_tracker(self):
        """get_tracker returns DSMTracker instance."""
        try:
            from governance.dsm_tracker import get_tracker, reset_tracker, DSMTracker

            reset_tracker()

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = get_tracker(evidence_dir=tmpdir)
                result = {"is_tracker": isinstance(tracker, DSMTracker)}
                reset_tracker()
                return result
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Tracker Returns Same Instance")
    def get_tracker_returns_same_instance(self):
        """get_tracker returns same instance on multiple calls."""
        try:
            from governance.dsm_tracker import get_tracker, reset_tracker

            reset_tracker()

            tracker1 = get_tracker()
            tracker2 = get_tracker()

            result = {"same_instance": tracker1 is tracker2}
            reset_tracker()
            return result
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Reset Tracker Clears Instance")
    def reset_tracker_clears_instance(self):
        """reset_tracker clears global instance."""
        try:
            from governance.dsm_tracker import get_tracker, reset_tracker

            reset_tracker()
            tracker1 = get_tracker()

            reset_tracker()
            tracker2 = get_tracker()

            result = {"different_instances": tracker1 is not tracker2}
            reset_tracker()
            return result
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
