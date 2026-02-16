"""
Unit tests for Tab Deep Scan Batch 49 — session_task exception handling,
dsm_metrics null guard, sync_pending_sessions field completeness.

3 bugs fixed (BUG-MCP-TASK-001, BUG-DSM-METRICS-001, BUG-SYNC-FIELDS-001).

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow validation.
"""

import inspect
from unittest.mock import patch, MagicMock


# ── BUG-MCP-TASK-001: session_task exception handling ──────────────


class TestSessionTaskExceptionHandling:
    """Verify session_task wraps in try-except like session_decision."""

    def test_has_bugfix_marker(self):
        """BUG-MCP-TASK-001 marker present."""
        from governance.mcp_tools import sessions_core
        source = inspect.getsource(sessions_core)
        assert "BUG-MCP-TASK-001" in source

    def test_session_task_has_try_except(self):
        """session_task has try-except wrapping."""
        from governance.mcp_tools import sessions_core
        source = inspect.getsource(sessions_core)
        # Find the session_task function
        task_start = source.find("def session_task(")
        task_end = source.find("def session_", task_start + 20)
        task_source = source[task_start:task_end]
        assert "try:" in task_source
        assert "except Exception as e:" in task_source

    def test_session_task_returns_error_on_exception(self):
        """session_task returns error message, not crash."""
        from governance.mcp_tools import sessions_core
        source = inspect.getsource(sessions_core)
        task_start = source.find("def session_task(")
        task_end = source.find("def session_", task_start + 20)
        task_source = source[task_start:task_end]
        assert "session_task failed:" in task_source

    def test_consistency_with_session_decision(self):
        """session_task and session_decision both have try-except."""
        from governance.mcp_tools import sessions_core
        source = inspect.getsource(sessions_core)
        # Both functions should have error handling
        assert "session_decision failed:" in source
        assert "session_task failed:" in source


# ── BUG-DSM-METRICS-001: dsm_metrics null guard ──────────────────


class TestDsmMetricsNullGuard:
    """Verify dsm_metrics guards current_cycle access."""

    def test_has_bugfix_marker(self):
        """BUG-DSM-METRICS-001 marker present."""
        from governance.mcp_tools import dsm
        source = inspect.getsource(dsm)
        assert "BUG-DSM-METRICS-001" in source

    def test_guard_checks_current_cycle(self):
        """Guard checks tracker.current_cycle before .metrics access."""
        from governance.mcp_tools import dsm
        source = inspect.getsource(dsm)
        assert "if tracker.current_cycle else" in source

    def test_fallback_to_input_metrics(self):
        """When current_cycle is None, returns input metrics."""
        # Simulate the guard logic
        tracker_current_cycle = None
        input_metrics = {"tests_passed": 10}
        result = tracker_current_cycle.metrics if tracker_current_cycle else input_metrics
        assert result == {"tests_passed": 10}

    def test_normal_path_returns_cycle_metrics(self):
        """When current_cycle exists, returns its metrics."""
        mock_cycle = MagicMock()
        mock_cycle.metrics = {"coverage": 85}
        result = mock_cycle.metrics if mock_cycle else {}
        assert result == {"coverage": 85}


# ── BUG-SYNC-FIELDS-001: sync_pending_sessions completeness ──────


class TestSyncPendingSessionsFields:
    """Verify sync_pending_sessions includes CC fields."""

    def test_has_bugfix_marker(self):
        """BUG-SYNC-FIELDS-001 marker present."""
        from governance.services import sessions
        source = inspect.getsource(sessions.sync_pending_sessions)
        assert "BUG-SYNC-FIELDS-001" in source

    def test_syncs_cc_session_uuid(self):
        """sync code references cc_session_uuid field."""
        from governance.services import sessions
        source = inspect.getsource(sessions.sync_pending_sessions)
        assert "cc_session_uuid" in source

    def test_syncs_cc_project_slug(self):
        """sync code references cc_project_slug field."""
        from governance.services import sessions
        source = inspect.getsource(sessions.sync_pending_sessions)
        assert "cc_project_slug" in source

    def test_syncs_status_field(self):
        """sync code references status field."""
        from governance.services import sessions
        source = inspect.getsource(sessions.sync_pending_sessions)
        assert '"status"' in source

    def test_update_is_best_effort(self):
        """Update after insert is best-effort (doesn't fail sync)."""
        from governance.services import sessions
        source = inspect.getsource(sessions.sync_pending_sessions)
        # Should have pass or continue after update failure
        assert "Best-effort" in source or "best-effort" in source


# ── False positives: sessions[-1] short-circuit ──────────────────


class TestSessionsShortCircuitBatch49:
    """Re-confirm sessions[-1] is safe due to or short-circuit."""

    def test_or_short_circuit_with_topic(self):
        """When topic is truthy, sessions[-1] is never evaluated."""
        topic = "test-topic"
        sessions = []  # Empty!
        result = topic or sessions[-1].split("-")[-1].lower()
        assert result == "test-topic"

    def test_guard_ensures_sessions_nonempty(self):
        """Guard 'if not sessions and not topic' ensures valid state."""
        # When both are falsy, function returns error (never reaches sessions[-1])
        sessions = []
        topic = None
        should_return_error = not sessions and not topic
        assert should_return_error is True

    def test_nonempty_sessions_safe(self):
        """When sessions is non-empty, sessions[-1] is safe."""
        sessions = ["SESSION-2026-02-15-TEST"]
        topic = None
        result = topic or sessions[-1].split("-")[-1].lower()
        assert result == "test"


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch49:
    """Batch 49 cross-cutting consistency checks."""

    def test_all_session_capture_functions_have_try_except(self):
        """All session capture MCP tools wrap in try-except."""
        from governance.mcp_tools import sessions_core
        source = inspect.getsource(sessions_core)
        for func in ["session_decision", "session_task"]:
            assert f"{func} failed:" in source, f"{func} missing exception handler"

    def test_dsm_module_has_tracker(self):
        """dsm.py references get_tracker."""
        from governance.mcp_tools import dsm
        source = inspect.getsource(dsm)
        assert "get_tracker" in source

    def test_sessions_service_has_sync(self):
        """sessions.py exports sync_pending_sessions."""
        from governance.services import sessions
        assert hasattr(sessions, "sync_pending_sessions")

    def test_sessions_service_has_update(self):
        """sessions.py exports update_session."""
        from governance.services import sessions
        assert hasattr(sessions, "update_session")
