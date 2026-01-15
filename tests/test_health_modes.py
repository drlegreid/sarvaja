"""
E2E tests for health check modes and AMNESIA detection.

Per GAP-AMNESIA-OUTPUT-001 and GAP-HEALTH-AGGRESSIVE-001.

Tests:
- format_summary includes AMNESIA warnings
- SARVAJA_HEALTH_MODE ENV affects threshold
- Aggressive mode always shows detailed output
"""

import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks to path
HOOKS_DIR = Path(__file__).parent.parent / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR.parent))


class TestAmnesiaOutputInSummary:
    """Test GAP-AMNESIA-OUTPUT-001: AMNESIA shown in summary mode."""

    def test_format_summary_without_amnesia(self):
        """Summary without AMNESIA should not show warning."""
        from hooks.healthcheck_formatters import format_summary

        result = format_summary(
            {"podman": {"ok": True}, "typedb": {"ok": True}, "chromadb": {"ok": True}},
            "TEST123",
            "(stable)",
            None,
            None,
            None,  # No amnesia
        )
        assert "[HEALTH OK]" in result
        assert "AMNESIA" not in result

    def test_format_summary_with_amnesia_detected(self):
        """Summary with AMNESIA should show warning."""
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
        assert "[HEALTH OK]" in result
        assert "AMNESIA RISK 65%" in result

    def test_format_summary_amnesia_not_detected(self):
        """Summary with low confidence AMNESIA should not show warning."""
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
        assert "[HEALTH OK]" in result
        assert "AMNESIA" not in result  # Not detected, no warning


class TestHealthModeConfiguration:
    """Test GAP-HEALTH-AGGRESSIVE-001: Health mode ENV configuration."""

    def test_health_mode_quiet_threshold(self):
        """Quiet mode should have 0.70 threshold."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "quiet"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)
            assert hc.HEALTH_MODE == "quiet"
            assert hc.AMNESIA_THRESHOLD == 0.70

    def test_health_mode_normal_threshold(self):
        """Normal mode should have 0.50 threshold."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "normal"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)
            assert hc.HEALTH_MODE == "normal"
            assert hc.AMNESIA_THRESHOLD == 0.50

    def test_health_mode_aggressive_threshold(self):
        """Aggressive mode should have 0.25 threshold."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "aggressive"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)
            assert hc.HEALTH_MODE == "aggressive"
            assert hc.AMNESIA_THRESHOLD == 0.25

    def test_health_mode_default_when_unset(self):
        """Default mode should be normal when ENV not set."""
        env_copy = os.environ.copy()
        env_copy.pop("SARVAJA_HEALTH_MODE", None)
        with patch.dict(os.environ, env_copy, clear=True):
            import hooks.healthcheck as hc
            importlib.reload(hc)
            assert hc.HEALTH_MODE == "normal"
            assert hc.AMNESIA_THRESHOLD == 0.50

    def test_health_mode_case_insensitive(self):
        """Health mode should be case insensitive."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "AGGRESSIVE"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)
            assert hc.HEALTH_MODE == "aggressive"
            assert hc.AMNESIA_THRESHOLD == 0.25


class TestAggressiveModeDetailedOutput:
    """Test aggressive mode always shows detailed output."""

    def test_use_detailed_in_aggressive_mode(self):
        """Aggressive mode should always use detailed format."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "aggressive"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)

            # Even when hash unchanged and not first check
            hash_changed = False
            check_count = 5

            use_detailed = hash_changed or check_count == 1 or hc.HEALTH_MODE == "aggressive"
            assert use_detailed is True

    def test_use_summary_in_normal_mode(self):
        """Normal mode should use summary when state unchanged."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "normal"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)

            hash_changed = False
            check_count = 5

            use_detailed = hash_changed or check_count == 1 or hc.HEALTH_MODE == "aggressive"
            assert use_detailed is False


class TestAmnesiaThresholdBehavior:
    """Test AMNESIA detection with different thresholds."""

    def test_aggressive_detects_low_confidence(self):
        """Aggressive mode (25% threshold) should detect 30% confidence."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "aggressive"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)

            # 30% confidence should be detected in aggressive mode
            confidence = 0.30
            detected = confidence >= hc.AMNESIA_THRESHOLD
            assert detected is True

    def test_normal_ignores_low_confidence(self):
        """Normal mode (50% threshold) should ignore 30% confidence."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "normal"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)

            confidence = 0.30
            detected = confidence >= hc.AMNESIA_THRESHOLD
            assert detected is False

    def test_quiet_ignores_medium_confidence(self):
        """Quiet mode (70% threshold) should ignore 60% confidence."""
        with patch.dict(os.environ, {"SARVAJA_HEALTH_MODE": "quiet"}):
            import hooks.healthcheck as hc
            importlib.reload(hc)

            confidence = 0.60
            detected = confidence >= hc.AMNESIA_THRESHOLD
            assert detected is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
