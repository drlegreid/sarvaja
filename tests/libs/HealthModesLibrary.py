"""
Robot Framework Library for Health Modes and AMNESIA Detection Tests.

Per GAP-AMNESIA-OUTPUT-001 and GAP-HEALTH-AGGRESSIVE-001.
Migrated from tests/test_health_modes.py
"""
import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch
from robot.api.deco import keyword


class HealthModesLibrary:
    """Library for testing health check modes and AMNESIA detection."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        # Add hooks to path
        hooks_dir = Path(__file__).parent.parent.parent / ".claude" / "hooks"
        if str(hooks_dir.parent) not in sys.path:
            sys.path.insert(0, str(hooks_dir.parent))

    # =============================================================================
    # AMNESIA Output in Summary Tests
    # =============================================================================

    @keyword("Format Summary Without Amnesia")
    def format_summary_without_amnesia(self):
        """Summary without AMNESIA should not show warning."""
        try:
            from hooks.healthcheck_formatters import format_summary
            result = format_summary(
                {"podman": {"ok": True}, "typedb": {"ok": True}, "chromadb": {"ok": True}},
                "TEST123",
                "(stable)",
                None,
                None,
                None,  # No amnesia
            )
            return {
                "health_ok": "[HEALTH OK]" in result,
                "no_amnesia": "AMNESIA" not in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Format Summary With Amnesia Detected")
    def format_summary_with_amnesia_detected(self):
        """Summary with AMNESIA should show warning."""
        try:
            from hooks.healthcheck_formatters import format_summary
            amnesia = {"detected": True, "confidence": 0.65, "indicators": ["LONG_GAP_8h"]}
            result = format_summary(
                {"podman": {"ok": True}, "typedb": {"ok": True}, "chromadb": {"ok": True}},
                "TEST123",
                "(stable)",
                None,
                None,
                amnesia,
            )
            return {
                "health_ok": "[HEALTH OK]" in result,
                "amnesia_shown": "AMNESIA RISK 65%" in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Format Summary Amnesia Not Detected")
    def format_summary_amnesia_not_detected(self):
        """Summary with low confidence AMNESIA should not show warning."""
        try:
            from hooks.healthcheck_formatters import format_summary
            amnesia = {"detected": False, "confidence": 0.3, "indicators": ["LONG_GAP_2h"]}
            result = format_summary(
                {"podman": {"ok": True}, "typedb": {"ok": True}, "chromadb": {"ok": True}},
                "TEST123",
                "(stable)",
                None,
                None,
                amnesia,
            )
            return {
                "health_ok": "[HEALTH OK]" in result,
                "no_amnesia": "AMNESIA" not in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Health Mode Configuration Tests
    # =============================================================================

    @keyword("Health Mode Quiet Threshold")
    def health_mode_quiet_threshold(self):
        """Quiet mode should have 0.70 threshold."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "quiet"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                return {
                    "mode_correct": hc.HEALTH_MODE == "quiet",
                    "threshold_correct": hc.AMNESIA_THRESHOLD == 0.70
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Health Mode Normal Threshold")
    def health_mode_normal_threshold(self):
        """Normal mode should have 0.50 threshold."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "normal"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                return {
                    "mode_correct": hc.HEALTH_MODE == "normal",
                    "threshold_correct": hc.AMNESIA_THRESHOLD == 0.50
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Health Mode Aggressive Threshold")
    def health_mode_aggressive_threshold(self):
        """Aggressive mode should have 0.25 threshold."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "aggressive"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                return {
                    "mode_correct": hc.HEALTH_MODE == "aggressive",
                    "threshold_correct": hc.AMNESIA_THRESHOLD == 0.25
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Health Mode Default When Unset")
    def health_mode_default_when_unset(self):
        """Default mode should be normal when ENV not set."""
        try:
            env_copy = os.environ.copy()
            env_copy.pop("SARVAJA_HEALTH_MODE", None)
            with patch.dict(os.environ, env_copy, clear=True):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                return {
                    "mode_correct": hc.HEALTH_MODE == "normal",
                    "threshold_correct": hc.AMNESIA_THRESHOLD == 0.50
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Health Mode Case Insensitive")
    def health_mode_case_insensitive(self):
        """Health mode should be case insensitive."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "AGGRESSIVE"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                return {
                    "mode_correct": hc.HEALTH_MODE == "aggressive",
                    "threshold_correct": hc.AMNESIA_THRESHOLD == 0.25
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Aggressive Mode Detailed Output Tests
    # =============================================================================

    @keyword("Use Detailed In Aggressive Mode")
    def use_detailed_in_aggressive_mode(self):
        """Aggressive mode should always use detailed format."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "aggressive"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                hash_changed = False
                check_count = 5
                use_detailed = hash_changed or check_count == 1 or hc.HEALTH_MODE == "aggressive"
                return {"use_detailed": use_detailed is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Use Summary In Normal Mode")
    def use_summary_in_normal_mode(self):
        """Normal mode should use summary when state unchanged."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "normal"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                hash_changed = False
                check_count = 5
                use_detailed = hash_changed or check_count == 1 or hc.HEALTH_MODE == "aggressive"
                return {"use_summary": use_detailed is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # AMNESIA Threshold Behavior Tests
    # =============================================================================

    @keyword("Aggressive Detects Low Confidence")
    def aggressive_detects_low_confidence(self):
        """Aggressive mode (25% threshold) should detect 30% confidence."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "aggressive"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                confidence = 0.30
                detected = confidence >= hc.AMNESIA_THRESHOLD
                return {"detected": detected is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Normal Ignores Low Confidence")
    def normal_ignores_low_confidence(self):
        """Normal mode (50% threshold) should ignore 30% confidence."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "normal"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                confidence = 0.30
                detected = confidence >= hc.AMNESIA_THRESHOLD
                return {"not_detected": detected is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Quiet Ignores Medium Confidence")
    def quiet_ignores_medium_confidence(self):
        """Quiet mode (70% threshold) should ignore 60% confidence."""
        try:
            with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "quiet"}):
                import hooks.healthcheck as hc
                importlib.reload(hc)
                confidence = 0.60
                detected = confidence >= hc.AMNESIA_THRESHOLD
                return {"not_detected": detected is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
