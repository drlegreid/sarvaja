"""
Robot Framework Library for DSM Tracker Evidence Generation Tests.

Per: RULE-012 (DSP), DOC-SIZE-01-v1.
Split from tests/test_dsm_tracker_integration.py
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerIntegrationEvidenceLibrary:
    """Library for DSM Tracker evidence generation tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # Evidence Generation Tests
    # =========================================================================

    @keyword("Evidence File Created")
    def evidence_file_created(self):
        """Evidence markdown file created on complete."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                tracker.start_cycle("EVIDENCE-TEST")
                tracker.advance_phase()
                evidence_path = tracker.complete_cycle()

                return {
                    "file_created": Path(evidence_path).exists()
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Evidence Contains Summary")
    def evidence_contains_summary(self):
        """Evidence file contains summary section."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                tracker.start_cycle("SUMMARY-TEST")
                tracker.advance_phase()
                evidence_path = tracker.complete_cycle()

                with open(evidence_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_summary_section": "## Summary" in content,
                    "has_batch_id": "SUMMARY-TEST" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Evidence Contains Findings")
    def evidence_contains_findings(self):
        """Evidence file contains findings."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                tracker.start_cycle()
                tracker.advance_phase()
                tracker.add_finding("gap", "Missing coverage for X")
                evidence_path = tracker.complete_cycle()

                with open(evidence_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_findings_section": "## Findings" in content,
                    "has_finding_text": "Missing coverage" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Evidence Contains Checkpoints")
    def evidence_contains_checkpoints(self):
        """Evidence file contains checkpoints."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                tracker.start_cycle()
                tracker.advance_phase()
                tracker.checkpoint("Audited 5 modules")
                evidence_path = tracker.complete_cycle()

                with open(evidence_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_checkpoints_section": "## Checkpoints" in content,
                    "has_checkpoint_text": "Audited 5 modules" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Evidence Contains Metrics")
    def evidence_contains_metrics(self):
        """Evidence file contains metrics."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                tracker.start_cycle()
                tracker.advance_phase()
                tracker.update_metrics({"tests_passed": 150, "coverage": 85})
                evidence_path = tracker.complete_cycle()

                with open(evidence_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "has_metrics_section": "## Metrics" in content,
                    "has_metric_key": "tests_passed" in content,
                    "has_metric_value": "150" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
