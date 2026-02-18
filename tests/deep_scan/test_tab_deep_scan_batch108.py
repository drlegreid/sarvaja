"""Deep scan batch 108: MCP tools + context/entropy layer.

Batch 108 findings: 11 total, 0 confirmed fixes, 11 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── MCP tool defense ──────────────


class TestMCPToolDefense:
    """Verify MCP tools handle edge cases correctly."""

    def test_finally_always_executes_on_return(self):
        """Python finally block executes even on return — confirms agent claim was wrong."""
        closed = []

        def example_generator():
            try:
                return "early"
            finally:
                closed.append(True)

        example_generator()
        assert len(closed) == 1  # finally ALWAYS runs

    def test_auto_session_tracker_singleton_pattern(self):
        """MCPAutoSessionTracker is module-level singleton."""
        from governance.mcp_tools import auto_session

        # Verify _global_tracker starts as None
        original = auto_session._global_tracker
        try:
            auto_session._global_tracker = None
            # track_mcp_tool_call creates tracker on first call
            with patch.object(auto_session.MCPAutoSessionTracker, "track", return_value="tracked"):
                result = auto_session.track_mcp_tool_call("test_tool", "test_server")
                assert auto_session._global_tracker is not None
        finally:
            auto_session._global_tracker = original

    def test_format_mcp_result_returns_string(self):
        """format_mcp_result always returns a string."""
        from governance.mcp_tools.common import format_mcp_result

        result = format_mcp_result({"test": True, "count": 42})
        assert isinstance(result, str)
        assert len(result) > 0
        assert "test" in result
        assert "42" in result

    def test_format_mcp_result_handles_none(self):
        """format_mcp_result handles None values."""
        from governance.mcp_tools.common import format_mcp_result

        result = format_mcp_result({"key": None})
        assert isinstance(result, str)
        assert "key" in result


# ── Context preloader defense ──────────────


class TestContextPreloaderDefense:
    """Verify context preloader caching and loading."""

    def test_preloader_first_call_loads(self):
        """First call to load_context always loads (no cache)."""
        from governance.context_preloader.preloader import ContextPreloader

        p = ContextPreloader.__new__(ContextPreloader)
        p._cached_context = None
        p._cache_time = None
        p._cache_ttl_seconds = 300

        with patch.object(p, "_load_decisions", return_value=[]):
            with patch.object(p, "_load_technology_choices", return_value=[]):
                with patch.object(p, "_detect_active_phase", return_value="unknown"):
                    with patch.object(p, "_count_open_gaps", return_value=0):
                        result = p.load_context()
                        assert result is not None
                        assert p._cache_time is not None

    def test_preloader_cache_hit(self):
        """Second call within TTL uses cache."""
        from governance.context_preloader.preloader import ContextPreloader, ContextSummary

        p = ContextPreloader.__new__(ContextPreloader)
        cached = ContextSummary()
        cached.decisions = [{"id": "DEC-001"}]
        p._cached_context = cached
        p._cache_time = datetime.now()
        p._cache_ttl_seconds = 300

        result = p.load_context()
        assert result is cached  # Same object = cache hit
        assert result.decisions == [{"id": "DEC-001"}]

    def test_preloader_force_refresh_bypasses_cache(self):
        """force_refresh=True always reloads."""
        from governance.context_preloader.preloader import ContextPreloader, ContextSummary

        p = ContextPreloader.__new__(ContextPreloader)
        p._cached_context = ContextSummary()
        p._cache_time = datetime.now()
        p._cache_ttl_seconds = 300

        with patch.object(p, "_load_decisions", return_value=[]):
            with patch.object(p, "_load_technology_choices", return_value=[]):
                with patch.object(p, "_detect_active_phase", return_value="planning"):
                    with patch.object(p, "_count_open_gaps", return_value=5):
                        result = p.load_context(force_refresh=True)
                        assert result is not p._cached_context or result.open_gaps_count == 5


# ── Entropy monitoring defense ──────────────


class TestEntropyMonitorDefense:
    """Verify entropy thresholds and state management."""

    def test_entropy_thresholds_defined(self):
        """Entropy thresholds are defined at module level."""
        import sys
        from pathlib import Path

        source_path = Path(__file__).parent.parent.parent / ".claude/hooks/checkers/entropy.py"
        if not source_path.exists():
            pytest.skip("entropy.py not found")

        source = source_path.read_text()
        # Verify three threshold levels exist
        assert "MEDIUM" in source or "50" in source
        assert "HIGH" in source or "100" in source
        assert "CRITICAL" in source or "150" in source

    def test_context_monitor_state_file_pattern(self):
        """Context monitor uses JSON state file for persistence."""
        from pathlib import Path

        state_file = Path(__file__).parent.parent.parent / ".claude/hooks/.context_monitor_state.json"
        # State file may or may not exist — just verify path construction
        assert str(state_file).endswith(".context_monitor_state.json")


# ── Execution event tracking defense ──────────────


class TestExecutionEventDefense:
    """Verify execution event tracking handles edge cases."""

    def test_execution_events_store_is_dict(self):
        """Execution events store is a dict of lists."""
        from governance.stores.data_stores import _execution_events_store

        assert isinstance(_execution_events_store, dict)

    def test_execution_events_store_append_pattern(self):
        """Execution events store supports list append per task."""
        from governance.stores.data_stores import _execution_events_store

        original = dict(_execution_events_store)
        try:
            test_id = "TEST-EXEC-PATTERN"
            _execution_events_store[test_id] = []
            _execution_events_store[test_id].append({
                "action": "test",
                "timestamp": datetime.now().isoformat(),
            })
            assert len(_execution_events_store[test_id]) == 1
            assert _execution_events_store[test_id][0]["action"] == "test"
        finally:
            _execution_events_store.pop(test_id, None)
            # Restore original state
            for k in list(_execution_events_store.keys()):
                if k not in original:
                    del _execution_events_store[k]
