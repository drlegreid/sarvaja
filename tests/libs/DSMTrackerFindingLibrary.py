"""
Robot Framework Library for DSMTracker - Finding & Status Tests.

Per RULE-012: Deep Sleep Protocol.
Split from DSMTrackerPhasesLibrary.py per DOC-SIZE-01-v1.

Covers: Finding management, status reporting.
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerFindingLibrary:
    """Library for testing DSMTracker findings and status."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Finding Tests
    # =========================================================================

    @keyword("Add Finding Creates Finding")
    def add_finding_creates_finding(self):
        """add_finding creates finding dict."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                finding = tracker.add_finding(finding_type="gap", description="Missing test coverage")
                return {
                    "type_gap": finding["type"] == "gap",
                    "description_correct": finding["description"] == "Missing test coverage",
                    "added_to_list": len(tracker.current_cycle.findings) == 1
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Add Finding Assigns Sequential Id")
    def add_finding_assigns_sequential_id(self):
        """add_finding assigns sequential ID."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                f1 = tracker.add_finding("gap", "Finding 1")
                f2 = tracker.add_finding("orphan", "Finding 2")
                return {
                    "first_id": f1["id"] == "FINDING-001",
                    "second_id": f2["id"] == "FINDING-002"
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Add Finding With Severity")
    def add_finding_with_severity(self):
        """add_finding accepts severity."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                finding = tracker.add_finding("conflict", "Critical conflict", severity="CRITICAL")
                return {"severity_correct": finding["severity"] == "CRITICAL"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Add Finding With Related Rules")
    def add_finding_with_related_rules(self):
        """add_finding accepts related rules."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()
                finding = tracker.add_finding("improvement", "Enhance RULE-001", related_rules=["RULE-001", "RULE-012"])
                return {
                    "has_rule_001": "RULE-001" in finding["related_rules"],
                    "has_rule_012": "RULE-012" in finding["related_rules"]
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Status Tests
    # =========================================================================

    @keyword("Get Status When Idle")
    def get_status_when_idle(self):
        """get_status when no cycle."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                status = tracker.get_status()
                return {
                    "not_active": status["active"] is False,
                    "has_message": "No cycle in progress" in status.get("message", "")
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Status When Active")
    def get_status_when_active(self):
        """get_status when cycle active."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle("TEST")
                tracker.checkpoint("Audit checkpoint")
                tracker.advance_phase()  # AUDIT
                tracker.checkpoint("Hypothesize checkpoint")
                tracker.advance_phase()  # HYPOTHESIZE
                status = tracker.get_status()
                return {
                    "is_active": status["active"] is True,
                    "batch_correct": status.get("batch_id") == "TEST",
                    "phase_correct": status.get("current_phase") == "hypothesize",
                    "has_progress": "1/7" in status.get("progress", "")
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Status Includes Required MCPs")
    def get_status_includes_required_mcps(self):
        """get_status includes required MCPs for current phase."""
        try:
            from governance.dsm_tracker import DSMTracker
            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )
                tracker.start_cycle()
                tracker.advance_phase()  # AUDIT
                status = tracker.get_status()
                mcps = status.get("required_mcps", [])
                return {
                    "has_claude_mem": "claude-mem" in mcps,
                    "has_governance": "governance" in mcps
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
