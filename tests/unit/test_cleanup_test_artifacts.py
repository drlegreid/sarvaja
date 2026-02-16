"""TDD Tests: Post-test cleanup of TEST-* artifacts.

Per RELIABILITY-PLAN-01-v1 Priority 4:
Cleanup TEST-* tasks and sessions from in-memory stores after test runs.
"""
from unittest.mock import patch

import pytest


class TestCleanupFunctionExists:
    """cleanup_test_artifacts() can be imported."""

    def test_importable(self):
        from governance.services.test_cleanup import cleanup_test_artifacts
        assert callable(cleanup_test_artifacts)


class TestCleanupRemovesTasks:
    """TEST-* tasks are removed from _tasks_store."""

    def test_removes_test_tasks(self):
        from governance.services.test_cleanup import cleanup_test_artifacts
        from governance.stores.data_stores import _tasks_store

        _tasks_store["TEST-CLEAN-001"] = {"task_id": "TEST-CLEAN-001", "status": "DONE"}
        _tasks_store["REAL-TASK-001"] = {"task_id": "REAL-TASK-001", "status": "TODO"}

        try:
            result = cleanup_test_artifacts()
            assert "TEST-CLEAN-001" not in _tasks_store
            assert "REAL-TASK-001" in _tasks_store
            assert result["tasks_removed"] >= 1
        finally:
            _tasks_store.pop("TEST-CLEAN-001", None)
            _tasks_store.pop("REAL-TASK-001", None)


class TestCleanupRemovesSessions:
    """TEST-* sessions are removed from _sessions_store."""

    def test_removes_test_sessions(self):
        from governance.services.test_cleanup import cleanup_test_artifacts
        from governance.stores.data_stores import _sessions_store

        _sessions_store["SESSION-2026-02-15-TEST-CLEANUP"] = {"session_id": "SESSION-2026-02-15-TEST-CLEANUP"}
        _sessions_store["SESSION-2026-02-15-REAL"] = {"session_id": "SESSION-2026-02-15-REAL"}

        try:
            result = cleanup_test_artifacts()
            # TEST sessions should be removed
            test_keys = [k for k in _sessions_store if "TEST" in k.upper()]
            assert len(test_keys) == 0 or "SESSION-2026-02-15-TEST-CLEANUP" not in _sessions_store
            assert "SESSION-2026-02-15-REAL" in _sessions_store
            assert result["sessions_removed"] >= 0
        finally:
            _sessions_store.pop("SESSION-2026-02-15-TEST-CLEANUP", None)
            _sessions_store.pop("SESSION-2026-02-15-REAL", None)


class TestCleanupReturnsSummary:
    """cleanup returns a summary of what was cleaned."""

    def test_returns_summary_dict(self):
        from governance.services.test_cleanup import cleanup_test_artifacts

        result = cleanup_test_artifacts()
        assert isinstance(result, dict)
        assert "tasks_removed" in result
        assert "sessions_removed" in result
