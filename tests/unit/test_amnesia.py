"""
Unit tests for AMNESIA Detection.

Per RULE-024: Tests for check_amnesia_indicators() and AmnesiaResult.
"""

import pytest
from datetime import datetime, timedelta

from governance.health.amnesia import (
    check_amnesia_indicators,
    AmnesiaResult,
    CORE_SERVICES,
)


# ---------------------------------------------------------------------------
# AmnesiaResult dataclass
# ---------------------------------------------------------------------------
class TestAmnesiaResult:
    """Tests for AmnesiaResult dataclass."""

    def test_defaults(self):
        r = AmnesiaResult(detected=False, confidence=0.0)
        assert r.indicators == []

    def test_with_indicators(self):
        r = AmnesiaResult(detected=True, confidence=0.7, indicators=["NO_PREVIOUS_STATE"])
        assert len(r.indicators) == 1


# ---------------------------------------------------------------------------
# CORE_SERVICES constant
# ---------------------------------------------------------------------------
class TestConstants:
    """Tests for module constants."""

    def test_core_services(self):
        assert "podman" in CORE_SERVICES
        assert "typedb" in CORE_SERVICES
        assert "chromadb" in CORE_SERVICES


# ---------------------------------------------------------------------------
# check_amnesia_indicators — Indicator 1: NO_PREVIOUS_STATE
# ---------------------------------------------------------------------------
class TestNoPreviousState:
    """Tests for NO_PREVIOUS_STATE indicator."""

    def test_empty_state(self):
        result = check_amnesia_indicators({})
        assert "NO_PREVIOUS_STATE" in result.indicators
        assert result.confidence >= 0.3

    def test_empty_hash(self):
        result = check_amnesia_indicators({"master_hash": ""})
        assert "NO_PREVIOUS_STATE" in result.indicators

    def test_with_hash_no_indicator(self):
        result = check_amnesia_indicators({"master_hash": "abc123"})
        assert "NO_PREVIOUS_STATE" not in result.indicators


# ---------------------------------------------------------------------------
# check_amnesia_indicators — Indicator 2: LONG_GAP
# ---------------------------------------------------------------------------
class TestLongGap:
    """Tests for LONG_GAP indicator."""

    def test_recent_check_no_gap(self):
        recent = (datetime.now() - timedelta(minutes=30)).isoformat()
        result = check_amnesia_indicators({"master_hash": "abc", "last_check": recent})
        gap_indicators = [i for i in result.indicators if i.startswith("LONG_GAP")]
        assert len(gap_indicators) == 0

    def test_old_check_triggers_gap(self):
        old = (datetime.now() - timedelta(hours=3)).isoformat()
        result = check_amnesia_indicators({"master_hash": "abc", "last_check": old})
        gap_indicators = [i for i in result.indicators if i.startswith("LONG_GAP")]
        assert len(gap_indicators) == 1
        assert "3h" in gap_indicators[0]

    def test_very_old_check(self):
        very_old = (datetime.now() - timedelta(hours=24)).isoformat()
        result = check_amnesia_indicators({"master_hash": "abc", "last_check": very_old})
        # Confidence capped at 0.4 for gap
        gap_indicators = [i for i in result.indicators if i.startswith("LONG_GAP")]
        assert len(gap_indicators) == 1

    def test_invalid_timestamp_ignored(self):
        result = check_amnesia_indicators({"master_hash": "abc", "last_check": "not-a-date"})
        gap_indicators = [i for i in result.indicators if i.startswith("LONG_GAP")]
        assert len(gap_indicators) == 0

    def test_no_last_check(self):
        result = check_amnesia_indicators({"master_hash": "abc"})
        gap_indicators = [i for i in result.indicators if i.startswith("LONG_GAP")]
        assert len(gap_indicators) == 0


# ---------------------------------------------------------------------------
# check_amnesia_indicators — Indicator 3: SERVICE_RECOVERED
# ---------------------------------------------------------------------------
class TestServiceRecovered:
    """Tests for SERVICE_RECOVERED indicator."""

    def test_service_recovered(self):
        prev = {"master_hash": "abc", "components": {"typedb": "DOWN"}}
        current = {"typedb": {"ok": True}}
        result = check_amnesia_indicators(prev, current)
        recovered = [i for i in result.indicators if "SERVICE_RECOVERED" in i]
        assert len(recovered) == 1
        assert "typedb" in recovered[0]

    def test_service_still_down(self):
        prev = {"master_hash": "abc", "components": {"typedb": "DOWN"}}
        current = {"typedb": {"ok": False}}
        result = check_amnesia_indicators(prev, current)
        recovered = [i for i in result.indicators if "SERVICE_RECOVERED" in i]
        assert len(recovered) == 0

    def test_service_was_up_stays_up(self):
        prev = {"master_hash": "abc", "components": {"typedb": "UP"}}
        current = {"typedb": {"ok": True}}
        result = check_amnesia_indicators(prev, current)
        recovered = [i for i in result.indicators if "SERVICE_RECOVERED" in i]
        assert len(recovered) == 0

    def test_no_current_services(self):
        prev = {"master_hash": "abc", "components": {"typedb": "DOWN"}}
        result = check_amnesia_indicators(prev, None)
        recovered = [i for i in result.indicators if "SERVICE_RECOVERED" in i]
        assert len(recovered) == 0

    def test_podman_down_recovered(self):
        prev = {"master_hash": "abc", "components": {"podman": "PODMAN_DOWN"}}
        current = {"podman": {"ok": True}}
        result = check_amnesia_indicators(prev, current)
        recovered = [i for i in result.indicators if "podman" in i]
        assert len(recovered) == 1

    def test_multiple_services_recovered(self):
        prev = {"master_hash": "abc", "components": {
            "typedb": "DOWN", "chromadb": "DOWN", "podman": "DOWN"
        }}
        current = {
            "typedb": {"ok": True}, "chromadb": {"ok": True}, "podman": {"ok": True}
        }
        result = check_amnesia_indicators(prev, current)
        recovered = [i for i in result.indicators if "SERVICE_RECOVERED" in i]
        assert len(recovered) == 3
        assert result.confidence >= 0.6  # 3 * 0.2


# ---------------------------------------------------------------------------
# check_amnesia_indicators — detection threshold
# ---------------------------------------------------------------------------
class TestDetectionThreshold:
    """Tests for the 0.5 confidence threshold."""

    def test_below_threshold(self):
        result = check_amnesia_indicators({"master_hash": "abc"})
        assert result.detected is False
        assert result.confidence < 0.5

    def test_at_threshold(self):
        # NO_PREVIOUS_STATE (0.3) + SERVICE_RECOVERED (0.2) = 0.5
        prev = {"components": {"typedb": "DOWN"}}
        current = {"typedb": {"ok": True}}
        result = check_amnesia_indicators(prev, current)
        assert result.detected is True
        assert result.confidence >= 0.5

    def test_above_threshold(self):
        # NO_PREVIOUS_STATE (0.3) + multiple recoveries
        prev = {"components": {"typedb": "DOWN", "chromadb": "DOWN"}}
        current = {"typedb": {"ok": True}, "chromadb": {"ok": True}}
        result = check_amnesia_indicators(prev, current)
        assert result.detected is True

    def test_confidence_capped_at_one(self):
        # Everything triggered: no hash + long gap + 3 recoveries
        old = (datetime.now() - timedelta(hours=100)).isoformat()
        prev = {"last_check": old, "components": {
            "typedb": "DOWN", "chromadb": "DOWN", "podman": "DOWN"
        }}
        current = {"typedb": {"ok": True}, "chromadb": {"ok": True}, "podman": {"ok": True}}
        result = check_amnesia_indicators(prev, current)
        assert result.confidence <= 1.0

    def test_service_ok_as_bool(self):
        """Test when current_services value is a bool (not dict)."""
        prev = {"master_hash": "abc", "components": {"typedb": "DOWN"}}
        current = {"typedb": True}
        result = check_amnesia_indicators(prev, current)
        # Bool doesn't have .ok attr and is not dict → current_ok=False
        recovered = [i for i in result.indicators if "SERVICE_RECOVERED" in i]
        assert len(recovered) == 0
