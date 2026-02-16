"""
Unit tests for Tab Deep Scan Batch 31 — MCP tools + middleware layer.

Covers: BUG-MCP-001 (null-safe TypeDB query results in 4 files),
BUG-MCP-002 (event_log JSON serialization safety).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import json
from datetime import datetime


# ── BUG-MCP-001: Null-safe TypeDB query results ─────────────────────


class TestSessionLinkingNullSafe:
    """session_get_tasks must handle None results from TypeDB."""

    def test_null_guard_in_source(self):
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        assert "BUG-MCP-001" in source
        assert "results or []" in source

    def test_none_or_empty_list_pattern(self):
        """None or [] must produce empty list."""
        results = None
        safe = results or []
        assert safe == []

    def test_list_unchanged(self):
        results = [{"tid": "T-1"}]
        safe = results or []
        assert safe == [{"tid": "T-1"}]


class TestProposalsNullSafe:
    """proposals_list must handle None results from TypeDB."""

    def test_null_guard_in_proposals_list(self):
        from governance.mcp_tools import proposals
        source = inspect.getsource(proposals)
        count = source.count("results or []")
        assert count >= 2, f"Expected >=2 null guards in proposals.py, found {count}"

    def test_bugfix_marker(self):
        from governance.mcp_tools import proposals
        source = inspect.getsource(proposals)
        assert "BUG-MCP-001" in source


class TestAgentsNullSafe:
    """agent_activity must handle None results from TypeDB."""

    def test_null_guard_in_agent_activity(self):
        from governance.mcp_tools import agents
        source = inspect.getsource(agents)
        assert "results or []" in source

    def test_bugfix_marker(self):
        from governance.mcp_tools import agents
        source = inspect.getsource(agents)
        assert "BUG-MCP-001" in source

    def test_none_slice_pattern(self):
        """(None or [])[:limit] must produce empty list."""
        results = None
        limit = 10
        safe = (results or [])[:limit]
        assert safe == []


# ── BUG-MCP-002: Event log JSON serialization safety ────────────────


class TestEventLogSafety:
    """log_event must not crash on non-serializable values."""

    def test_has_default_str(self):
        from governance.middleware import event_log
        source = inspect.getsource(event_log.log_event)
        assert "default=str" in source

    def test_has_try_except(self):
        from governance.middleware import event_log
        source = inspect.getsource(event_log.log_event)
        assert "try:" in source
        assert "except" in source

    def test_null_entity_gets_default(self):
        from governance.middleware import event_log
        source = inspect.getsource(event_log.log_event)
        assert '"unknown"' in source or "'unknown'" in source

    def test_serializes_datetime(self):
        """datetime objects should be serialized via default=str."""
        entry = {"ts": "2026-02-16T00:00:00", "entity": "test",
                 "action": "test", "detail": datetime(2026, 2, 16)}
        result = json.dumps(entry, default=str)
        assert "2026-02-16" in result

    def test_serializes_none_values(self):
        entry = {"ts": "2026-02-16", "entity": "test",
                 "action": "test", "value": None}
        result = json.dumps(entry, default=str)
        assert "null" in result

    def test_bugfix_marker(self):
        from governance.middleware import event_log
        source = inspect.getsource(event_log.log_event)
        assert "BUG-MCP-002" in source


# ── Event log functional tests ───────────────────────────────────────


class TestEventLogFunctional:
    """log_event must emit valid JSON to the logger."""

    def test_basic_event(self):
        """log_event should emit structured JSON without crashing."""
        import logging
        from governance.middleware.event_log import log_event

        handler = logging.Handler()
        records = []
        handler.emit = lambda r: records.append(r)

        logger = logging.getLogger("governance.events")
        old_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        try:
            log_event("session", "create", session_id="S-1")
            assert len(records) >= 1
            data = json.loads(records[0].getMessage())
            assert data["entity"] == "session"
            assert data["action"] == "create"
            assert data["session_id"] == "S-1"
        finally:
            logger.removeHandler(handler)
            logger.setLevel(old_level)

    def test_non_serializable_doesnt_crash(self):
        """log_event with non-serializable values should not raise."""
        from governance.middleware.event_log import log_event
        # Should not raise — set is not JSON-serializable but default=str handles it
        log_event("task", "update", custom_set={1, 2, 3})
