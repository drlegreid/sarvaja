"""
Tests for MCP-First Enforcement Logic (Phase 8).

Per GOV-MCP-FIRST-01-v1: MCP usage checker upgrades from warn-only
to health-aware enforcement. When gov-tasks MCP is healthy, TodoWrite
without prior MCP usage gets a stronger warning. When MCP is down,
fallback mode suppresses warnings.

BDD Scenarios:
  - TodoWrite warns when MCP is available
  - Fallback mode when MCP is down (no warning)
  - Health check caches results
  - Enforcement respects existing thresholds
"""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import importlib.util

CHECKER_PATH = (
    Path(__file__).parent.parent.parent
    / ".claude" / "hooks" / "checkers" / "mcp_usage_checker.py"
)


def _load_checker():
    """Import the checker module fresh."""
    spec = importlib.util.spec_from_file_location(
        "mcp_usage_checker", str(CHECKER_PATH)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestMCPHealthCheck:
    """Tests for check_mcp_health() — API reachability probe."""

    def test_health_returns_true_when_api_responds(self):
        """MCP is healthy when API /api/health returns 200."""
        mod = _load_checker()
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.get", return_value=mock_resp):
            result = mod.check_mcp_health()
        assert result is True

    def test_health_returns_false_when_api_down(self):
        """MCP is unhealthy when API connection fails."""
        mod = _load_checker()
        import httpx
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            result = mod.check_mcp_health()
        assert result is False

    def test_health_returns_false_on_non_200(self):
        """MCP is unhealthy when API returns non-200."""
        mod = _load_checker()
        mock_resp = MagicMock()
        mock_resp.status_code = 503

        with patch("httpx.get", return_value=mock_resp):
            result = mod.check_mcp_health()
        assert result is False

    def test_health_cached_within_interval(self):
        """Health check result is cached — no repeat API calls."""
        mod = _load_checker()
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            mod.check_mcp_health()
            mod.check_mcp_health()
            mod.check_mcp_health()
        # Should only call API once due to caching
        assert mock_get.call_count == 1

    def test_health_cache_expires(self):
        """Cache expires after HEALTH_CHECK_INTERVAL seconds."""
        mod = _load_checker()
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            mod.check_mcp_health()
            # Simulate cache expiry
            mod._health_cache["timestamp"] = time.time() - mod.HEALTH_CHECK_INTERVAL - 1
            mod.check_mcp_health()
        assert mock_get.call_count == 2

    def test_health_timeout_is_short(self):
        """Health check uses a short timeout to avoid blocking hooks."""
        mod = _load_checker()
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            mod.check_mcp_health()
        # Verify timeout kwarg is <= 2 seconds
        _, kwargs = mock_get.call_args
        assert kwargs.get("timeout", 999) <= 2.0


class TestEnforcementMode:
    """Tests for health-aware enforcement in track_tool()."""

    def test_warn_when_todowrite_and_mcp_healthy(self):
        """When MCP is up and TodoWrite used without gov-tasks → warning."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = mod.MIN_TOOL_COUNT
        state["todowrite_count"] = 2
        state["mcp_categories_used"] = {}

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                with patch.object(mod, "check_mcp_health", return_value=True):
                    result = mod.track_tool("SomeOtherTool")
        assert result is not None
        assert "MCP-FIRST" in result

    def test_no_warn_when_mcp_down_fallback(self):
        """When MCP is down, TodoWrite is legitimate — no warning."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = mod.MIN_TOOL_COUNT
        state["todowrite_count"] = 5
        state["mcp_categories_used"] = {}

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                with patch.object(mod, "check_mcp_health", return_value=False):
                    result = mod.track_tool("TodoWrite")
        assert result is None

    def test_warning_message_includes_enforcement_context(self):
        """Warning mentions MCP is available for stronger guidance."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = mod.MIN_TOOL_COUNT
        state["todowrite_count"] = 2
        state["mcp_categories_used"] = {}

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                with patch.object(mod, "check_mcp_health", return_value=True):
                    result = mod.track_tool("Read")
        assert "MANDATORY" in result or "mcp__gov-tasks__task_create()" in result

    def test_enforce_still_respects_min_tool_count(self):
        """Enforcement doesn't fire before MIN_TOOL_COUNT even if MCP healthy."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = 3  # Below MIN_TOOL_COUNT
        state["todowrite_count"] = 5
        state["mcp_categories_used"] = {}

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                with patch.object(mod, "check_mcp_health", return_value=True):
                    result = mod.track_tool("Read")
        assert result is None

    def test_enforce_still_respects_max_warnings(self):
        """Warning cap still applies in enforce mode."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = 20
        state["todowrite_count"] = 5
        state["mcp_categories_used"] = {}
        state["warnings_issued"] = mod.MAX_WARNINGS

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                with patch.object(mod, "check_mcp_health", return_value=True):
                    result = mod.track_tool("Read")
        assert result is None

    def test_no_warn_when_gov_tasks_already_used(self):
        """Gov-tasks usage suppresses enforcement even when MCP is healthy."""
        mod = _load_checker()
        state = mod._default_state()
        state["tool_count"] = mod.MIN_TOOL_COUNT
        state["todowrite_count"] = 10
        state["mcp_categories_used"] = {"gov-tasks": 3}

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state"):
                with patch.object(mod, "check_mcp_health", return_value=True):
                    result = mod.track_tool("TodoWrite")
        assert result is None


class TestFallbackMode:
    """Tests for is_fallback_mode() public API."""

    def test_is_fallback_mode_true_when_mcp_down(self):
        """is_fallback_mode() returns True when MCP is unhealthy."""
        mod = _load_checker()
        with patch.object(mod, "check_mcp_health", return_value=False):
            assert mod.is_fallback_mode() is True

    def test_is_fallback_mode_false_when_mcp_healthy(self):
        """is_fallback_mode() returns False when MCP is up."""
        mod = _load_checker()
        with patch.object(mod, "check_mcp_health", return_value=True):
            assert mod.is_fallback_mode() is False

    def test_fallback_mode_state_tracked(self):
        """Fallback mode is recorded in state for diagnostics."""
        mod = _load_checker()
        saved = {}

        def capture(s):
            saved.update(s)

        state = mod._default_state()
        state["tool_count"] = mod.MIN_TOOL_COUNT
        state["todowrite_count"] = 3
        state["mcp_categories_used"] = {}

        with patch.object(mod, "load_state", return_value=state):
            with patch.object(mod, "save_state", side_effect=capture):
                with patch.object(mod, "check_mcp_health", return_value=False):
                    mod.track_tool("TodoWrite")
        assert saved.get("mcp_healthy") is False


class TestEnforcementSummary:
    """Tests for get_summary() with health context."""

    def test_summary_includes_health_status(self):
        """get_summary() reports MCP health status."""
        mod = _load_checker()
        state = mod._default_state()
        state["mcp_healthy"] = True

        with patch.object(mod, "load_state", return_value=state):
            summary = mod.get_summary()
        assert "mcp_healthy" in summary

    def test_summary_includes_enforcement_mode(self):
        """get_summary() reports enforcement vs fallback mode."""
        mod = _load_checker()
        state = mod._default_state()
        state["mcp_healthy"] = True

        with patch.object(mod, "load_state", return_value=state):
            summary = mod.get_summary()
        assert "mode" in summary
        assert summary["mode"] in ("enforce", "fallback")


class TestResetWithHealth:
    """Tests that reset clears health cache too."""

    def test_reset_clears_health_cache(self):
        """reset() clears the health cache for fresh session."""
        mod = _load_checker()
        # Prime the cache
        mod._health_cache["healthy"] = True
        mod._health_cache["timestamp"] = time.time()

        saved = {}

        def capture(s):
            saved.update(s)

        with patch.object(mod, "save_state", side_effect=capture):
            mod.reset()
        assert mod._health_cache.get("timestamp", 0) == 0
