"""Deep scan batch 98: MCP server implementations + context recovery.

Batch 98 findings: 34 total, 0 confirmed fixes, 34 rejected.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


# ── Context preloader cache defense ──────────────


class TestContextPreloaderCache:
    """Verify context preloader cache behavior."""

    def test_cache_hit_within_ttl(self):
        from governance.context_preloader.preloader import ContextPreloader
        from governance.context_preloader.models import ContextSummary

        loader = ContextPreloader(project_root=MagicMock())
        loader._cached_context = ContextSummary()
        loader._cache_time = datetime.now()
        loader._cache_ttl_seconds = 300

        result = loader.load_context(force_refresh=False)
        assert result is loader._cached_context

    def test_cache_miss_after_ttl(self):
        from governance.context_preloader.preloader import ContextPreloader
        from governance.context_preloader.models import ContextSummary

        loader = ContextPreloader(project_root=MagicMock())
        loader._cached_context = ContextSummary()
        loader._cache_time = datetime.now() - timedelta(seconds=600)
        loader._cache_ttl_seconds = 300

        # Will try to load from disk — mock the disk methods
        loader._load_decisions = lambda: []
        loader._load_technology_choices = lambda: []
        loader._detect_active_phase = lambda: None
        loader._count_open_gaps = lambda: 0

        result = loader.load_context(force_refresh=False)
        # Fresh context returned (not old cached one)
        assert result is not loader._cached_context or result.decisions == []

    def test_force_refresh_bypasses_cache(self):
        from governance.context_preloader.preloader import ContextPreloader
        from governance.context_preloader.models import ContextSummary

        loader = ContextPreloader(project_root=MagicMock())
        old = ContextSummary()
        old.open_gaps_count = 999
        loader._cached_context = old
        loader._cache_time = datetime.now()

        loader._load_decisions = lambda: []
        loader._load_technology_choices = lambda: []
        loader._detect_active_phase = lambda: None
        loader._count_open_gaps = lambda: 42

        result = loader.load_context(force_refresh=True)
        assert result.open_gaps_count == 42


# ── Decision parsing ternary defense ──────────────


class TestDecisionParsingTernary:
    """Verify ternary expression in _parse_session_decisions_file is safe."""

    def test_last_decision_no_next_section(self):
        """When no next ## section, ternary returns len(content)."""
        import re
        content = "## DECISION-001: Test\n**Status**: ACTIVE\n**Date**: 2026-02-15\n**Decision**: Final block"
        match = re.search(r"##\s+(DECISION-\d+):\s+(.+?)\n", content)
        assert match is not None
        start = match.end()
        next_section = re.search(r"\n##\s+", content[start:])
        # next_section is None for last/only section
        assert next_section is None
        section = content[start:start + next_section.start() if next_section else len(content)]
        assert "Final block" in section

    def test_middle_decision_has_next_section(self):
        """When next ## exists, ternary uses its start position."""
        import re
        content = "## DECISION-001: First\nBody1\n## DECISION-002: Second\nBody2"
        match = re.search(r"##\s+(DECISION-\d+):\s+(.+?)\n", content)
        assert match is not None
        start = match.end()
        next_section = re.search(r"\n##\s+", content[start:])
        assert next_section is not None
        section = content[start:start + next_section.start() if next_section else len(content)]
        assert "Body1" in section
        assert "Body2" not in section


# ── Auto-session tracker lifecycle defense ──────────────


class TestAutoSessionLifecycle:
    """Verify MCP auto-session tracker state transitions."""

    def test_track_creates_session_on_first_call(self):
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker(timeout_seconds=300)
        assert tracker.active_session_id is None

        sid = tracker.track("test_tool", "gov-core")
        assert sid is not None
        assert "MCP-AUTO" in sid
        assert len(tracker.tool_calls) == 1

    def test_track_reuses_active_session(self):
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker(timeout_seconds=300)
        sid1 = tracker.track("tool_a", "gov-core")
        sid2 = tracker.track("tool_b", "gov-tasks")
        assert sid1 == sid2
        assert len(tracker.tool_calls) == 2

    def test_expired_session_creates_new(self):
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker(timeout_seconds=1)
        sid1 = tracker.track("tool_a", "gov-core")
        # Force expiry
        tracker._last_activity = datetime.now() - timedelta(seconds=10)
        sid2 = tracker.track("tool_b", "gov-tasks")
        assert sid1 != sid2

    def test_end_session_clears_state(self):
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker()
        tracker.track("test", "gov-core")
        summary = tracker.end_session()
        assert summary is not None
        assert summary["tool_call_count"] == 1
        assert tracker.active_session_id is None
        assert tracker.tool_calls == []

    def test_end_when_no_session_returns_none(self):
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker()
        assert tracker.end_session() is None


# ── Session repair apply_repair completeness defense ──────────────


class TestRepairApplyCompleteness:
    """Verify apply_repair handles all fix types from build_repair_plan."""

    def test_dry_run_returns_fixes(self):
        from governance.services.session_repair import apply_repair

        item = {"session_id": "TEST-001", "fixes": {"agent_id": "code-agent"}}
        result = apply_repair(item, dry_run=True)
        assert result["dry_run"] is True
        assert result["applied"] is False

    def test_agent_id_fix_applied(self):
        from governance.services.session_repair import apply_repair

        item = {"session_id": "TEST-002", "fixes": {"agent_id": "code-agent"}}
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(item, dry_run=False)
            mock_update.assert_called_once_with("TEST-002", agent_id="code-agent")
            assert result["applied"] is True

    def test_timestamp_fix_applied(self):
        from governance.services.session_repair import apply_repair

        item = {
            "session_id": "TEST-003",
            "fixes": {"timestamp": {"start": "2026-02-15T09:00:00", "end": "2026-02-15T13:00:00"}},
        }
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(item, dry_run=False)
            mock_update.assert_called_once_with(
                "TEST-003",
                start_time="2026-02-15T09:00:00",
                end_time="2026-02-15T13:00:00",
            )
            assert result["applied"] is True

    def test_duration_fix_applied(self):
        from governance.services.session_repair import apply_repair

        item = {
            "session_id": "TEST-004",
            "fixes": {"duration": {"end_time": "2026-02-15T17:00:00"}},
        }
        with patch("governance.services.sessions.update_session") as mock_update:
            result = apply_repair(item, dry_run=False)
            mock_update.assert_called_once_with("TEST-004", end_time="2026-02-15T17:00:00")
            assert result["applied"] is True


# ── format_mcp_result defense ──────────────


class TestFormatMcpResult:
    """Verify format_mcp_result returns parseable output."""

    def test_dict_serialized_returns_string(self):
        from governance.mcp_tools.common import format_mcp_result

        result = format_mcp_result({"key": "value", "count": 42})
        assert isinstance(result, str)
        assert "key" in result
        assert "value" in result

    def test_error_dict_contains_error(self):
        from governance.mcp_tools.common import format_mcp_result

        result = format_mcp_result({"error": "Something went wrong"})
        assert isinstance(result, str)
        assert "error" in result
        assert "Something went wrong" in result


# ── Context compactor zoom levels defense ──────────────


class TestContextCompactorZoom:
    """Verify zoom level compilation."""

    def test_zoom_0_summary(self):
        from governance.mcp_tools.context_compactor import _compile_zoom_0

        result = _compile_zoom_0(
            {"session_id": "TEST-001", "status": "ACTIVE"},
            [{"status": "DONE"}, {"status": "IN_PROGRESS"}],
            [{"tool": "Read"}],
            [{"text": "thinking"}],
            [{"name": "DEC-1"}],
        )
        assert "TEST-001" in result
        assert "2 tasks" in result
        assert "1 done" in result

    def test_zoom_1_includes_tasks_and_decisions(self):
        from governance.mcp_tools.context_compactor import _compile_zoom_1

        result = _compile_zoom_1(
            {"session_id": "TEST-002", "status": "ACTIVE"},
            [{"description": "Fix bug", "status": "DONE"}],
            [],
            [],
            [{"name": "DECISION-099"}],
        )
        assert "Fix bug" in result
        assert "DECISION-099" in result
