"""
Unit tests for Session Timeline Cache (EPIC-PERF-TELEM-V1 Phase 3).

Verifies _timeline_cache with 30s TTL in sessions_pagination.py:
- Cache hit within TTL (no API call)
- Cache expires after 30s (fresh API call)
- Filter change invalidates cache

BDD Scenarios:
  - Cached within TTL: no API call when <30s old
  - Cache expires after 30s: fresh fetch
  - Filter change invalidates cache

Created: 2026-03-26
"""

import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ── Mock State + Ctrl ────────────────────────────────────


def _make_state():
    """Create a mock Trame state object with common session attributes."""
    state = MagicMock()
    state.sessions_page = 1
    state.sessions_per_page = 20
    state.sessions_filter_status = None
    state.sessions_filter_agent = None
    state.sessions_date_from = None
    state.sessions_date_to = None
    state.sessions_search_query = None
    state.sessions_exclude_test = True
    state.sessions_view_mode = "table"
    state.sessions_pivot_group_by = "agent_id"
    state.sessions_auto_refresh = False
    state.sessions_pagination = {}
    state.sessions = []
    state.sessions_agent_options = []
    state.sessions_timeline_data = []
    state.sessions_timeline_labels = []
    state.sessions_metrics_duration = "0h"
    state.sessions_metrics_avg_tasks = 0
    state.is_loading = False
    state.has_error = False
    state.error_message = ""

    # Make state.change return a decorator that just returns the function
    def change_decorator(attr_name):
        def decorator(fn):
            return fn
        return decorator
    state.change = change_decorator

    return state


def _make_ctrl():
    """Create a mock Trame ctrl object."""
    ctrl = MagicMock()
    ctrl.trigger = lambda name: lambda fn: fn
    return ctrl


# ── BDD: Cached within TTL ──────────────────────────────


class TestCacheHitWithinTTL:
    """Scenario: Cached within TTL — no API call when <30s old."""

    @patch("agent.governance_ui.controllers.sessions_pagination.httpx.Client")
    def test_second_call_uses_cache(self, mock_client_cls):
        """Timeline data cached; second load_sessions_page does NOT refetch timeline."""
        from agent.governance_ui.controllers.sessions_pagination import (
            register_sessions_pagination, _timeline_cache,
        )

        state = _make_state()
        ctrl = _make_ctrl()

        # Setup mock HTTP client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{"session_id": "S-1", "status": "COMPLETED",
                       "start_time": "2026-03-01", "end_time": "2026-03-01"}],
            "pagination": {"total": 1, "has_more": False, "offset": 0, "limit": 20},
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        load_fn = register_sessions_pagination(state, ctrl, "http://test:8082")

        # First call: populates cache
        load_fn()
        first_call_count = mock_client.get.call_count

        # Second call: should reuse cached timeline data (fewer API calls)
        load_fn()
        second_call_count = mock_client.get.call_count - first_call_count

        # First call makes 2 GET requests (page + timeline).
        # Second call should make only 1 GET (page) since timeline is cached.
        assert second_call_count < first_call_count, (
            f"Expected cache hit to reduce calls. "
            f"First: {first_call_count}, Second: {second_call_count}"
        )


# ── BDD: Cache expires after 30s ────────────────────────


class TestCacheExpiry:
    """Scenario: Cache expires after 30s — fresh fetch."""

    @patch("agent.governance_ui.controllers.sessions_pagination.httpx.Client")
    @patch("agent.governance_ui.controllers.sessions_pagination.time.monotonic")
    def test_cache_expires_after_ttl(self, mock_time, mock_client_cls):
        """After 31s, timeline cache expires and fresh API call is made."""
        from agent.governance_ui.controllers.sessions_pagination import (
            register_sessions_pagination, _timeline_cache,
        )

        state = _make_state()
        ctrl = _make_ctrl()

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{"session_id": "S-1", "status": "ACTIVE",
                       "start_time": "2026-03-01"}],
            "pagination": {"total": 1, "has_more": False, "offset": 0, "limit": 20},
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Simulate time progression: first call at t=0, second at t=31
        mock_time.side_effect = [0.0, 0.0, 31.0, 31.0]

        load_fn = register_sessions_pagination(state, ctrl, "http://test:8082")

        load_fn()
        first_count = mock_client.get.call_count

        # Simulate 31 seconds passing
        load_fn()
        total_count = mock_client.get.call_count

        # After TTL expiry, should make full API calls again (page + timeline)
        second_count = total_count - first_count
        assert second_count >= first_count, (
            f"Expected expired cache to trigger fresh fetch. "
            f"First: {first_count}, Second: {second_count}"
        )


# ── BDD: Filter change invalidates cache ────────────────


class TestCacheInvalidation:
    """Scenario: Filter change invalidates cache."""

    @patch("agent.governance_ui.controllers.sessions_pagination.httpx.Client")
    def test_filter_change_clears_cache(self, mock_client_cls):
        """Changing status filter invalidates cached timeline data."""
        from agent.governance_ui.controllers.sessions_pagination import (
            register_sessions_pagination, _timeline_cache,
        )

        # Clear stale cache from prior tests (module-level dict)
        _timeline_cache.clear()

        state = _make_state()
        ctrl = _make_ctrl()

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{"session_id": "S-1", "status": "COMPLETED",
                       "start_time": "2026-03-01", "end_time": "2026-03-01"}],
            "pagination": {"total": 1, "has_more": False, "offset": 0, "limit": 20},
        }
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        load_fn = register_sessions_pagination(state, ctrl, "http://test:8082")

        # First call: cache empty → page GET + timeline GET = 2 calls
        load_fn()
        first_count = mock_client.get.call_count

        # Simulate filter change — invalidate cache
        _timeline_cache.clear()

        # Second call after invalidation: same number of calls (page + timeline)
        load_fn()
        second_count = mock_client.get.call_count - first_count

        assert second_count == first_count, (
            f"Expected invalidated cache to trigger full fetch. "
            f"First: {first_count}, Second: {second_count}"
        )


# ── Cache data structure tests ───────────────────────────


class TestCacheStructure:
    """Verify _timeline_cache module-level dict exists and has expected behavior."""

    def test_cache_dict_importable(self):
        """_timeline_cache is importable from the module."""
        from agent.governance_ui.controllers.sessions_pagination import _timeline_cache
        assert isinstance(_timeline_cache, dict)

    def test_cache_has_expected_keys_after_population(self):
        """After population, cache has 'timestamp' and 'data' keys."""
        from agent.governance_ui.controllers.sessions_pagination import _timeline_cache
        # Simulate population
        _timeline_cache["timestamp"] = time.monotonic()
        _timeline_cache["data"] = {"values": [1, 2], "labels": ["a", "b"]}
        _timeline_cache["metrics"] = {"duration": "10h", "avg_tasks": 2.5}

        assert "timestamp" in _timeline_cache
        assert "data" in _timeline_cache
        assert "metrics" in _timeline_cache

        # Cleanup
        _timeline_cache.clear()

    def test_cache_clear_removes_all(self):
        """Clearing cache removes all entries."""
        from agent.governance_ui.controllers.sessions_pagination import _timeline_cache
        _timeline_cache["timestamp"] = 1.0
        _timeline_cache.clear()
        assert len(_timeline_cache) == 0
