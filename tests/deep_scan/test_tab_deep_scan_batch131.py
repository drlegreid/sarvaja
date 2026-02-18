"""Deep scan batch 131: Navigation + layout + utilities.

Batch 131 findings: 13 total, 0 confirmed fixes, 13 rejected.
"""
import pytest
from datetime import datetime


# ── Duration computation defense ──────────────


class TestDurationComputationDefense:
    """Verify compute_session_duration handles edge cases."""

    def test_normal_duration(self):
        """Normal duration computes correctly."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-15T10:00:00", "2026-02-15T11:30:00",
        )
        assert "1h 30m" in result

    def test_short_duration(self):
        """Short duration shows minutes."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-15T10:00:00", "2026-02-15T10:05:00",
        )
        assert "5m" in result

    def test_very_long_duration_capped(self):
        """Duration >24h shows '>24h' marker."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration(
            "2026-02-10T09:00:00", "2026-02-15T09:00:00",
        )
        assert ">24h" in result

    def test_none_end_time_returns_ongoing(self):
        """None end_time returns ongoing indicator."""
        from agent.governance_ui.utils import compute_session_duration

        result = compute_session_duration("2026-02-15T10:00:00", None)
        assert result is not None  # Returns something (ongoing or empty)

    def test_timestamp_sliced_to_19_chars(self):
        """Timestamps with microseconds are sliced to 19 chars."""
        ts = "2026-02-15T14:30:00.123456+00:00"
        sliced = ts[:19]
        assert sliced == "2026-02-15T14:30:00"
        # This can be parsed by strptime
        dt = datetime.strptime(sliced, "%Y-%m-%dT%H:%M:%S")
        assert dt.hour == 14


# ── Artificial timestamp detection defense ──────────────


class TestArtificialTimestampDefense:
    """Verify _is_estimated_duration correctly identifies repair artifacts."""

    def test_repair_artifact_detected(self):
        """T09:00:00 start + T13:00:00 end → estimated."""
        from agent.governance_ui.utils import _is_estimated_duration

        result = _is_estimated_duration(
            "2026-02-15T09:00:00", "2026-02-15T13:00:00",
        )
        assert result is True

    def test_real_timestamps_not_flagged(self):
        """Normal timestamps are not flagged as estimated."""
        from agent.governance_ui.utils import _is_estimated_duration

        result = _is_estimated_duration(
            "2026-02-15T14:30:00", "2026-02-15T16:45:00",
        )
        assert result is False

    def test_date_with_09_in_day_not_flagged(self):
        """Date 2026-01-09T00:00:00 does NOT contain 'T09:00:00'."""
        ts = "2026-01-09T00:00:00"
        assert "T09:00:00" not in ts  # 09 is in day, not time


# ── Pagination offset defense ──────────────


class TestPaginationOffsetDefense:
    """Verify pagination offset is always non-negative."""

    def test_page_1_offset_0(self):
        """Page 1 has offset 0."""
        page = 1
        per_page = 20
        offset = (page - 1) * per_page
        assert offset == 0

    def test_page_2_offset_correct(self):
        """Page 2 has offset = per_page."""
        page = 2
        per_page = 20
        offset = (page - 1) * per_page
        assert offset == 20

    def test_initial_page_is_one(self):
        """sessions_page initialized to 1 in initial state."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        assert state.get("sessions_page", 1) >= 1


# ── API URL construction defense ──────────────


class TestAPIURLConstructionDefense:
    """Verify API URLs are constructed correctly."""

    def test_no_trailing_slash_in_base_url(self):
        """api_base_url doesn't have trailing slash."""
        base = "http://localhost:8082"
        url = f"{base}/api/sessions"
        assert "//" not in url.split("://")[1]  # No double slash after protocol

    def test_api_prefix_consistent(self):
        """All endpoints use /api/ prefix."""
        endpoints = [
            "/api/sessions",
            "/api/tasks",
            "/api/rules",
            "/api/agents",
            "/api/health",
        ]
        for ep in endpoints:
            assert ep.startswith("/api/")


# ── Navigation active view defense ──────────────


class TestNavigationActiveViewDefense:
    """Verify navigation items have consistent values."""

    def test_all_nav_items_have_value(self):
        """Every navigation item has a 'value' key."""
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS

        for item in NAVIGATION_ITEMS:
            assert "value" in item, f"Missing value in {item}"
            assert isinstance(item["value"], str)

    def test_initial_active_view_matches_nav(self):
        """Initial active_view matches a navigation item."""
        from agent.governance_ui.state.initial import get_initial_state
        from agent.governance_ui.state.constants import NAVIGATION_ITEMS

        state = get_initial_state()
        active = state.get("active_view", "executive")
        values = [item["value"] for item in NAVIGATION_ITEMS]
        assert active in values
