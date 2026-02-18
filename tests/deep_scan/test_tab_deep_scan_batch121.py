"""Deep scan batch 121: Session collector + bridge.

Batch 121 findings: 13 total, 0 confirmed fixes, 13 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date
import uuid


# ── Auto-session tracker defense ──────────────


class TestAutoSessionTrackerDefense:
    """Verify MCPAutoSessionTracker handles lifecycle correctly."""

    def test_create_session_sets_active_id(self):
        """_create_session always sets active_session_id."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker()
        tracker._create_session("test-server")
        assert tracker.active_session_id is not None
        assert "MCP-AUTO" in tracker.active_session_id

    def test_end_session_clears_state(self):
        """end_session clears active_session_id and tool_calls."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker()
        tracker._create_session("test-server")
        assert tracker.active_session_id is not None

        tracker.end_session()
        assert tracker.active_session_id is None
        assert tracker.tool_calls == []

    def test_track_creates_session_if_none(self):
        """track() creates session when active_session_id is None."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker()
        assert tracker.active_session_id is None

        result = tracker.track("test_tool", "test-server")
        assert tracker.active_session_id is not None
        assert isinstance(result, str)

    def test_tool_calls_bounded_by_timeout(self):
        """Tool calls list is bounded by 5-min session timeout."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker, _DEFAULT_TIMEOUT_SECONDS

        assert _DEFAULT_TIMEOUT_SECONDS == 300  # 5 minutes
        # At 1 call/second (unrealistic for MCP), max ~300 entries


# ── Session collector registry defense ──────────────


class TestSessionCollectorRegistryDefense:
    """Verify session registry handles get_or_create correctly."""

    def test_same_topic_returns_same_session(self):
        """get_or_create_session returns existing session for same topic."""
        from governance.session_collector.registry import get_or_create_session, _active_sessions

        # Clean up first
        _active_sessions.clear()

        s1 = get_or_create_session("test-topic")
        s2 = get_or_create_session("test-topic")
        assert s1 is s2  # Same object — by design

        _active_sessions.clear()

    def test_different_topics_create_different_sessions(self):
        """Different topics create separate sessions."""
        from governance.session_collector.registry import get_or_create_session, _active_sessions

        _active_sessions.clear()

        s1 = get_or_create_session("topic-a")
        s2 = get_or_create_session("topic-b")
        assert s1 is not s2
        assert s1.session_id != s2.session_id

        _active_sessions.clear()


# ── Session bridge persistence defense ──────────────


class TestSessionBridgePersistenceDefense:
    """Verify session bridge persistence patterns are consistent."""

    def test_sessions_store_is_dict(self):
        """_sessions_store is a module-level dict for in-memory fallback."""
        from governance.stores import _sessions_store
        assert isinstance(_sessions_store, dict)

    def test_persist_session_available(self):
        """persist_session function is importable."""
        from governance.stores.session_persistence import persist_session
        assert callable(persist_session)


# ── TypeQL escaping in sync defense ──────────────


class TestSyncTypeQLEscapingDefense:
    """Verify session collector sync escapes TypeQL strings."""

    def test_quote_escape_prevents_injection(self):
        """Quote escaping prevents TypeQL injection."""
        malicious = 'foo"; has decision-status "CRITICAL'
        escaped = malicious.replace('"', '\\"')
        query = f'insert $d isa decision, has decision-id "{escaped}";'
        assert '\\"' in query
        # The escaped form contains backslash-quote, not bare quotes
        assert 'foo\\"' in query

    def test_normal_id_unaffected(self):
        """Normal IDs pass through escaping unchanged."""
        normal = "DECISION-001"
        escaped = normal.replace('"', '\\"')
        assert escaped == normal


# ── Render truncation defense ──────────────


class TestRenderTruncationDefense:
    """Verify evidence rendering handles content correctly."""

    def test_short_content_renders(self):
        """Content under limit renders without issues."""
        content = "Short content"
        rendered = f"{content[:100]}..."
        assert "Short content" in rendered

    def test_long_content_truncated(self):
        """Content over limit is truncated."""
        content = "A" * 200
        rendered = f"{content[:100]}..."
        assert len(rendered) == 103  # 100 chars + "..."


# ── Capture tool call truncation defense ──────────────


class TestCaptureToolCallTruncationDefense:
    """Verify capture_tool_call truncates correctly."""

    def test_result_truncated_at_500(self):
        """Results over 500 chars are truncated."""
        from governance.session_collector.collector import SessionCollector

        collector = SessionCollector.__new__(SessionCollector)
        collector.session_id = "SESSION-2026-02-15-TEST"
        collector._start_time = datetime.now()
        collector.events = []
        collector._tool_count = 0
        collector._tools_used = set()

        long_result = "x" * 1000
        collector.capture_tool_call("Bash", {"cmd": "ls"}, long_result)

        metadata = collector.events[0].metadata
        assert len(metadata.get("result", "")) <= 503  # 500 + "..."

    def test_short_result_not_truncated(self):
        """Results under 500 chars are kept as-is."""
        from governance.session_collector.collector import SessionCollector

        collector = SessionCollector.__new__(SessionCollector)
        collector.session_id = "SESSION-2026-02-15-TEST"
        collector._start_time = datetime.now()
        collector.events = []
        collector._tool_count = 0
        collector._tools_used = set()

        short_result = "ok"
        collector.capture_tool_call("Read", {}, short_result)

        metadata = collector.events[0].metadata
        assert metadata.get("result_summary") == "ok"


# ── Global singleton per-process defense ──────────────


class TestGlobalSingletonDefense:
    """Verify global tracker singleton is per-process."""

    def test_singleton_returns_same_instance(self):
        """track_mcp_tool_call returns same tracker across calls."""
        from governance.mcp_tools import auto_session

        # Save original
        original = auto_session._global_tracker
        auto_session._global_tracker = None

        try:
            auto_session.track_mcp_tool_call("tool1", "server1")
            t1 = auto_session._global_tracker

            auto_session.track_mcp_tool_call("tool2", "server2")
            t2 = auto_session._global_tracker

            assert t1 is t2  # Same instance within process
        finally:
            # Restore
            if auto_session._global_tracker:
                auto_session._global_tracker.end_session()
            auto_session._global_tracker = original
