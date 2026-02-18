"""
Tests for session limitation fixes (Lim 1, Lim 2).

Lim 1: end_session() must update _sessions_store even when TypeDB succeeds.
Lim 2: Startup cleanup for orphaned ACTIVE chat sessions.

Created: 2026-02-09
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestEndSessionUpdatesSessionsStore:
    """Lim 1: end_session() service must update _sessions_store even on TypeDB success."""

    def test_end_session_updates_store_on_typedb_success(self):
        """When TypeDB end succeeds, _sessions_store should also be updated."""
        from governance.stores import _sessions_store
        from governance.services.sessions import end_session

        sid = "SESSION-LIM1-TEST-001"
        _sessions_store[sid] = {
            "session_id": sid,
            "status": "ACTIVE",
            "tasks_completed": 0,
            "start_time": datetime.now().isoformat(),
        }

        mock_session = MagicMock()
        mock_session.id = sid
        mock_session.status = "ACTIVE"
        mock_updated = MagicMock()

        try:
            with patch("governance.services.sessions_lifecycle.get_typedb_client") as mock_client_fn:
                client = MagicMock()
                client.get_session.return_value = mock_session
                client.end_session.return_value = mock_updated
                mock_client_fn.return_value = client

                with patch("governance.services.sessions_lifecycle.session_to_response") as mock_resp:
                    mock_resp.return_value = {"session_id": sid, "status": "COMPLETED"}
                    end_session(sid, tasks_completed=5, source="test")

            assert _sessions_store[sid]["status"] == "COMPLETED"
            assert _sessions_store[sid]["tasks_completed"] == 5
            assert "end_time" in _sessions_store[sid]
        finally:
            _sessions_store.pop(sid, None)

    def test_end_session_stores_evidence_files_on_typedb_success(self):
        """When TypeDB end succeeds, evidence_files should be stored in _sessions_store."""
        from governance.stores import _sessions_store
        from governance.services.sessions import end_session

        sid = "SESSION-LIM1-TEST-002"
        _sessions_store[sid] = {
            "session_id": sid,
            "status": "ACTIVE",
            "tasks_completed": 0,
        }

        try:
            with patch("governance.services.sessions_lifecycle.get_typedb_client") as mock_client_fn:
                client = MagicMock()
                client.get_session.return_value = MagicMock()
                client.end_session.return_value = MagicMock()
                mock_client_fn.return_value = client

                with patch("governance.services.sessions_lifecycle.session_to_response") as mock_resp:
                    mock_resp.return_value = {"session_id": sid, "status": "COMPLETED"}
                    end_session(
                        sid,
                        tasks_completed=3,
                        evidence_files=["evidence/SESSION-TEST.md"],
                        source="test",
                    )

            assert _sessions_store[sid]["evidence_files"] == ["evidence/SESSION-TEST.md"]
        finally:
            _sessions_store.pop(sid, None)

    def test_end_session_no_store_update_when_session_not_in_store(self):
        """If session is not in _sessions_store, TypeDB-only end should still succeed."""
        from governance.stores import _sessions_store
        from governance.services.sessions import end_session

        sid = "SESSION-LIM1-TEST-003"
        # Don't add to _sessions_store — only in TypeDB

        try:
            with patch("governance.services.sessions_lifecycle.get_typedb_client") as mock_client_fn:
                client = MagicMock()
                client.get_session.return_value = MagicMock()
                client.end_session.return_value = MagicMock()
                mock_client_fn.return_value = client

                with patch("governance.services.sessions_lifecycle.session_to_response") as mock_resp:
                    mock_resp.return_value = {"session_id": sid, "status": "COMPLETED"}
                    result = end_session(sid, tasks_completed=1, source="test")

            assert result is not None
            assert sid not in _sessions_store
        finally:
            _sessions_store.pop(sid, None)

    def test_end_session_tasks_completed_none_skips_update(self):
        """When tasks_completed is None, should not overwrite existing value."""
        from governance.stores import _sessions_store
        from governance.services.sessions import end_session

        sid = "SESSION-LIM1-TEST-004"
        _sessions_store[sid] = {
            "session_id": sid,
            "status": "ACTIVE",
            "tasks_completed": 7,
        }

        try:
            with patch("governance.services.sessions_lifecycle.get_typedb_client") as mock_client_fn:
                client = MagicMock()
                client.get_session.return_value = MagicMock()
                client.end_session.return_value = MagicMock()
                mock_client_fn.return_value = client

                with patch("governance.services.sessions_lifecycle.session_to_response") as mock_resp:
                    mock_resp.return_value = {"session_id": sid, "status": "COMPLETED"}
                    end_session(sid, tasks_completed=None, source="test")

            # Should preserve original value
            assert _sessions_store[sid]["tasks_completed"] == 7
            assert _sessions_store[sid]["status"] == "COMPLETED"
        finally:
            _sessions_store.pop(sid, None)


class TestStartupOrphanCleanup:
    """Lim 2: Startup cleanup for orphaned ACTIVE chat sessions."""

    def _run_cleanup(self):
        """Helper to run async cleanup in tests."""
        from governance.api import cleanup_orphaned_chat_sessions
        import asyncio
        asyncio.get_event_loop().run_until_complete(cleanup_orphaned_chat_sessions())

    def test_cleanup_ends_active_chat_sessions_in_store(self):
        """Orphaned ACTIVE CHAT-* sessions in _sessions_store should be marked COMPLETED."""
        from governance.stores import _sessions_store

        chat_sid = "SESSION-2026-02-09-CHAT-STORE-ORPHAN"
        _sessions_store[chat_sid] = {
            "session_id": chat_sid,
            "status": "ACTIVE",
            "tasks_completed": 0,
        }

        try:
            with patch("governance.services.sessions.list_sessions", return_value={"items": []}):
                with patch("governance.services.sessions.end_session"):
                    self._run_cleanup()

            assert _sessions_store[chat_sid]["status"] == "COMPLETED"
            # BUG-213-ORPHAN-ENDTIME-001: end_time is now ISO timestamp, not literal string
            assert _sessions_store[chat_sid]["end_time"]  # Just verify it's set (ISO timestamp)
        finally:
            _sessions_store.pop(chat_sid, None)

    def test_cleanup_ends_typedb_chat_sessions(self):
        """Orphaned ACTIVE CHAT-* sessions in TypeDB should be ended via service."""
        from governance.stores import _sessions_store

        mock_sessions = [
            {"session_id": "SESSION-2026-02-09-CHAT-TYPEDB-ORPHAN", "status": "ACTIVE"},
            {"session_id": "SESSION-2026-02-09-REGULAR", "status": "ACTIVE"},
        ]

        try:
            with patch("governance.services.sessions.list_sessions", return_value={"items": mock_sessions}):
                with patch("governance.services.sessions.end_session") as mock_end:
                    self._run_cleanup()

            # Only the CHAT session should be ended
            mock_end.assert_called_once_with(
                "SESSION-2026-02-09-CHAT-TYPEDB-ORPHAN", source="orphan-cleanup"
            )
        finally:
            pass

    def test_cleanup_ignores_non_chat_sessions(self):
        """Non-CHAT sessions should not be affected by cleanup."""
        from governance.stores import _sessions_store

        regular_sid = "SESSION-2026-02-09-REGULAR"
        _sessions_store[regular_sid] = {
            "session_id": regular_sid,
            "status": "ACTIVE",
            "tasks_completed": 0,
        }

        try:
            with patch("governance.services.sessions.list_sessions", return_value={"items": []}):
                with patch("governance.services.sessions.end_session"):
                    self._run_cleanup()

            assert _sessions_store[regular_sid]["status"] == "ACTIVE"
        finally:
            _sessions_store.pop(regular_sid, None)

    def test_cleanup_ignores_completed_chat_sessions(self):
        """COMPLETED CHAT sessions should not be modified."""
        from governance.stores import _sessions_store

        chat_sid = "SESSION-2026-02-09-CHAT-DONE"
        _sessions_store[chat_sid] = {
            "session_id": chat_sid,
            "status": "COMPLETED",
            "end_time": "2026-02-09T10:00:00",
            "tasks_completed": 3,
        }

        mock_sessions = [
            {"session_id": chat_sid, "status": "COMPLETED"},
        ]

        try:
            with patch("governance.services.sessions.list_sessions", return_value={"items": mock_sessions}):
                with patch("governance.services.sessions.end_session") as mock_end:
                    self._run_cleanup()

            assert _sessions_store[chat_sid]["end_time"] == "2026-02-09T10:00:00"
            mock_end.assert_not_called()
        finally:
            _sessions_store.pop(chat_sid, None)

    def test_cleanup_handles_multiple_typedb_orphans(self):
        """Multiple orphaned CHAT sessions in TypeDB should all be cleaned up."""
        mock_sessions = [
            {"session_id": "SESSION-2026-02-09-CHAT-AAA", "status": "ACTIVE"},
            {"session_id": "SESSION-2026-02-09-CHAT-BBB", "status": "ACTIVE"},
            {"session_id": "SESSION-2026-02-09-CHAT-CCC", "status": "ACTIVE"},
        ]

        with patch("governance.services.sessions.list_sessions", return_value={"items": mock_sessions}):
            with patch("governance.services.sessions.end_session") as mock_end:
                self._run_cleanup()

        assert mock_end.call_count == 3

    def test_cleanup_resilient_to_typedb_errors(self):
        """Cleanup should not crash if TypeDB is unavailable."""
        from governance.stores import _sessions_store

        chat_sid = "SESSION-2026-02-09-CHAT-RESILIENT"
        _sessions_store[chat_sid] = {
            "session_id": chat_sid,
            "status": "ACTIVE",
            "tasks_completed": 0,
        }

        try:
            with patch("governance.services.sessions.list_sessions", side_effect=Exception("TypeDB down")):
                self._run_cleanup()

            # _sessions_store cleanup should still have run
            assert _sessions_store[chat_sid]["status"] == "COMPLETED"
        finally:
            _sessions_store.pop(chat_sid, None)
