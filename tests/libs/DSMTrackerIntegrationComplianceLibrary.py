"""
Robot Framework Library for DSM Tracker Rule Compliance Tests.

Per: RULE-012 (DSP), DOC-SIZE-01-v1.
Split from tests/test_dsm_tracker_integration.py
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerIntegrationComplianceLibrary:
    """Library for DSM Tracker RULE-012 compliance tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # RULE-012 Compliance Tests
    # =========================================================================

    @keyword("Phases Match Rule 012")
    def phases_match_rule_012(self):
        """DSP phases match RULE-012 specification."""
        try:
            from governance.dsm_tracker import DSPPhase

            # Per RULE-012: AUDIT -> HYPOTHESIZE -> MEASURE -> OPTIMIZE -> VALIDATE -> DREAM -> REPORT
            order = DSPPhase.phase_order()

            return {
                "phase_0_audit": order[0] == DSPPhase.AUDIT,
                "phase_1_hypothesize": order[1] == DSPPhase.HYPOTHESIZE,
                "phase_2_measure": order[2] == DSPPhase.MEASURE,
                "phase_3_optimize": order[3] == DSPPhase.OPTIMIZE,
                "phase_4_validate": order[4] == DSPPhase.VALIDATE,
                "phase_5_dream": order[5] == DSPPhase.DREAM,
                "phase_6_report": order[6] == DSPPhase.REPORT
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Evidence References Rule 012")
    def evidence_references_rule_012(self):
        """Evidence file references RULE-012."""
        try:
            from governance.dsm_tracker import DSMTracker

            with tempfile.TemporaryDirectory() as tmpdir:
                tracker = DSMTracker(
                    evidence_dir=tmpdir,
                    state_file=str(Path(tmpdir) / ".dsm_state.json")
                )

                tracker.start_cycle()
                tracker.advance_phase()
                evidence_path = tracker.complete_cycle()

                with open(evidence_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "references_rule_012": "RULE-012" in content
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("MCPs Per Phase Per Rule 012")
    def mcps_per_phase_per_rule_012(self):
        """MCP requirements match RULE-012 specification."""
        try:
            from governance.dsm_tracker import DSPPhase

            # Per RULE-012 table
            expected = {
                DSPPhase.AUDIT: ["claude-mem", "governance"],
                DSPPhase.HYPOTHESIZE: ["sequential-thinking"],
                DSPPhase.MEASURE: ["powershell", "llm-sandbox"],
                DSPPhase.VALIDATE: ["pytest", "llm-sandbox"],
            }

            results = {}
            for phase, expected_mcps in expected.items():
                phase_results = []
                for mcp in expected_mcps:
                    has_mcp = mcp in phase.required_mcps
                    phase_results.append(has_mcp)
                results[f"{phase.value}_mcps_correct"] = all(phase_results)

            return results
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
