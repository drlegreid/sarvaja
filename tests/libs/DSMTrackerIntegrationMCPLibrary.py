"""
Robot Framework Library for DSM Tracker MCP Tools Tests.

Per: RULE-012 (DSP), DOC-SIZE-01-v1.
Split from tests/test_dsm_tracker_integration.py
"""
import json
import tempfile
import uuid
from pathlib import Path
from robot.api.deco import keyword


class DSMTrackerIntegrationMCPLibrary:
    """Library for DSM Tracker MCP tools tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    def _setup_clean_tracker(self):
        """Set up a clean DSM tracker for testing."""
        import governance.dsm.tracker as dt
        from governance.dsm import reset_tracker, DSMTracker

        # Create a fresh tracker with a unique temp state file
        temp_state = Path(tempfile.gettempdir()) / f".dsm_state_test_{uuid.uuid4().hex}.json"
        reset_tracker()
        dt._tracker = DSMTracker(state_file=str(temp_state))
        return temp_state

    def _cleanup_tracker(self, original_tracker, temp_state):
        """Restore original tracker and clean up."""
        import governance.dsm.tracker as dt
        dt._tracker = original_tracker
        if temp_state.exists():
            temp_state.unlink()

    # =========================================================================
    # MCP Tool Existence Tests
    # =========================================================================

    @keyword("DSM Start Tool Exists")
    def dsm_start_tool_exists(self):
        """dsm_start MCP tool exists."""
        try:
            from governance.compat import dsm_start
            return {
                "exists": dsm_start is not None,
                "callable": callable(dsm_start)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Advance Tool Exists")
    def dsm_advance_tool_exists(self):
        """dsm_advance MCP tool exists."""
        try:
            from governance.compat import dsm_advance
            return {
                "exists": dsm_advance is not None,
                "callable": callable(dsm_advance)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Checkpoint Tool Exists")
    def dsm_checkpoint_tool_exists(self):
        """dsm_checkpoint MCP tool exists."""
        try:
            from governance.compat import dsm_checkpoint
            return {
                "exists": dsm_checkpoint is not None,
                "callable": callable(dsm_checkpoint)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Status Tool Exists")
    def dsm_status_tool_exists(self):
        """dsm_status MCP tool exists."""
        try:
            from governance.compat import dsm_status
            return {
                "exists": dsm_status is not None,
                "callable": callable(dsm_status)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Complete Tool Exists")
    def dsm_complete_tool_exists(self):
        """dsm_complete MCP tool exists."""
        try:
            from governance.compat import dsm_complete
            return {
                "exists": dsm_complete is not None,
                "callable": callable(dsm_complete)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Finding Tool Exists")
    def dsm_finding_tool_exists(self):
        """dsm_finding MCP tool exists."""
        try:
            from governance.compat import dsm_finding
            return {
                "exists": dsm_finding is not None,
                "callable": callable(dsm_finding)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("DSM Metrics Tool Exists")
    def dsm_metrics_tool_exists(self):
        """dsm_metrics MCP tool exists."""
        try:
            from governance.compat import dsm_metrics
            return {
                "exists": dsm_metrics is not None,
                "callable": callable(dsm_metrics)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # MCP Tool Functionality Tests
    # =========================================================================

    @keyword("DSM Start Returns JSON")
    def dsm_start_returns_json(self):
        """dsm_start returns valid JSON."""
        try:
            import governance.dsm.tracker as dt
            from governance.compat import dsm_start

            original_tracker = dt._tracker
            temp_state = self._setup_clean_tracker()

            try:
                result = dsm_start("MCP-TEST")
                parsed = json.loads(result)

                return {
                    "valid_json": True,
                    "has_cycle_id": "cycle_id" in parsed,
                    "batch_id_correct": parsed.get("batch_id") == "MCP-TEST"
                }
            finally:
                self._cleanup_tracker(original_tracker, temp_state)
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("DSM Advance Returns JSON")
    def dsm_advance_returns_json(self):
        """dsm_advance returns valid JSON."""
        try:
            import governance.dsm.tracker as dt
            from governance.compat import dsm_start, dsm_advance

            original_tracker = dt._tracker
            temp_state = self._setup_clean_tracker()

            try:
                dsm_start("MCP-TEST")
                result = dsm_advance()
                parsed = json.loads(result)

                return {
                    "valid_json": True,
                    "new_phase_audit": parsed.get("new_phase") == "audit",
                    "has_required_mcps": "required_mcps" in parsed
                }
            finally:
                self._cleanup_tracker(original_tracker, temp_state)
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("DSM Status Returns JSON")
    def dsm_status_returns_json(self):
        """dsm_status returns valid JSON."""
        try:
            import governance.dsm.tracker as dt
            from governance.compat import dsm_start, dsm_status

            original_tracker = dt._tracker
            temp_state = self._setup_clean_tracker()

            try:
                dsm_start("STATUS-TEST")
                result = dsm_status()
                parsed = json.loads(result)

                return {
                    "valid_json": True,
                    "has_active": "active" in parsed,
                    "active_is_true": parsed.get("active") is True
                }
            finally:
                self._cleanup_tracker(original_tracker, temp_state)
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("DSM Checkpoint Returns JSON")
    def dsm_checkpoint_returns_json(self):
        """dsm_checkpoint returns valid JSON."""
        try:
            import governance.dsm.tracker as dt
            from governance.compat import dsm_start, dsm_advance, dsm_checkpoint

            original_tracker = dt._tracker
            temp_state = self._setup_clean_tracker()

            try:
                dsm_start("CHECKPOINT-TEST")
                dsm_advance()
                result = dsm_checkpoint("Test checkpoint")
                parsed = json.loads(result)

                return {
                    "valid_json": True,
                    "description_correct": parsed.get("description") == "Test checkpoint",
                    "has_timestamp": "timestamp" in parsed
                }
            finally:
                self._cleanup_tracker(original_tracker, temp_state)
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("DSM Finding Returns JSON")
    def dsm_finding_returns_json(self):
        """dsm_finding returns valid JSON."""
        try:
            import governance.dsm.tracker as dt
            from governance.compat import dsm_start, dsm_advance, dsm_finding

            original_tracker = dt._tracker
            temp_state = self._setup_clean_tracker()

            try:
                dsm_start("FINDING-TEST")
                dsm_advance()
                result = dsm_finding("gap", "Missing tests", "HIGH", "RULE-004")
                parsed = json.loads(result)

                return {
                    "valid_json": True,
                    "has_finding_id": "finding_id" in parsed,
                    "finding_type_correct": parsed.get("finding_type") == "gap",
                    "has_rule_reference": "RULE-004" in parsed.get("related_rules", [])
                }
            finally:
                self._cleanup_tracker(original_tracker, temp_state)
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}
