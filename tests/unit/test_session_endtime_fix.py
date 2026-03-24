"""
Tests for session end_time/duration + customTitle + auto-refresh (P2-10c).

Bug: insert_session() ignores start_time/end_time from CC JSONL ingestion.
Bug: ingest_single_session() skips existing sessions without updating end_time.
Bug: create_session() service layer doesn't pass start_time/end_time/status.

TDD: Tests define correct behavior; implementation follows.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helper: build a mock SessionCRUDOperations instance
# ---------------------------------------------------------------------------

def _make_crud_ops():
    """Build a mock-backed SessionCRUDOperations for testing insert_session.

    Patches typedb.driver.TransactionType since typedb isn't installed locally.
    """
    import sys
    # Ensure typedb.driver module exists for the lazy import inside insert_session
    mock_typedb = MagicMock()
    sys.modules.setdefault("typedb", mock_typedb)
    sys.modules.setdefault("typedb.driver", mock_typedb.driver)

    from governance.typedb.queries.sessions.crud import SessionCRUDOperations

    ops = SessionCRUDOperations.__new__(SessionCRUDOperations)
    mock_tx = MagicMock()
    mock_tx.query.return_value.resolve.return_value = None
    ops._driver = MagicMock()
    ops._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
    ops._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
    ops.database = "test"
    ops.get_session = MagicMock(side_effect=[None, MagicMock()])
    return ops, mock_tx


# ---------------------------------------------------------------------------
# 1. insert_session() should accept start_time, end_time, status
# ---------------------------------------------------------------------------


class TestInsertSessionTimestamps:
    """insert_session() must accept and persist start_time + end_time."""

    def test_insert_session_accepts_start_time(self):
        """insert_session should use provided start_time, not now()."""
        ops, mock_tx = _make_crud_ops()
        ops.insert_session(
            session_id="SESSION-2026-03-19-TEST",
            start_time="2026-03-19T10:00:00",
        )
        query = mock_tx.query.call_args[0][0]
        assert "2026-03-19T10:00:00" in query

    def test_insert_session_accepts_end_time(self):
        """insert_session should set completed-at when end_time provided."""
        ops, mock_tx = _make_crud_ops()
        ops.insert_session(
            session_id="SESSION-2026-03-19-TEST",
            end_time="2026-03-19T12:30:00",
        )
        query = mock_tx.query.call_args[0][0]
        assert "completed-at" in query
        assert "2026-03-19T12:30:00" in query

    def test_insert_session_uses_now_when_no_start_time(self):
        """insert_session should fall back to datetime.now() when no start_time."""
        ops, mock_tx = _make_crud_ops()
        ops.insert_session(session_id="SESSION-2026-03-19-TEST")
        query = mock_tx.query.call_args[0][0]
        assert "has started-at" in query

    def test_insert_session_accepts_status(self):
        """insert_session should set session-status when status provided."""
        ops, mock_tx = _make_crud_ops()
        ops.insert_session(
            session_id="SESSION-2026-03-19-TEST",
            status="COMPLETED",
        )
        query = mock_tx.query.call_args[0][0]
        assert "COMPLETED" in query

    def test_insert_session_no_completed_at_when_no_end_time(self):
        """insert_session should NOT set completed-at when end_time is absent."""
        ops, mock_tx = _make_crud_ops()
        ops.insert_session(session_id="SESSION-2026-03-19-TEST")
        query = mock_tx.query.call_args[0][0]
        assert "completed-at" not in query

    def test_insert_session_accepts_cc_external_name(self):
        """insert_session should set cc-external-name when provided."""
        ops, mock_tx = _make_crud_ops()
        ops.insert_session(
            session_id="SESSION-2026-03-19-TEST",
            cc_external_name="my-project",
        )
        query = mock_tx.query.call_args[0][0]
        assert 'cc-external-name' in query
        assert 'my-project' in query


# ---------------------------------------------------------------------------
# 2. create_session() service layer must pass timestamps through
# ---------------------------------------------------------------------------


class TestCreateSessionPassthrough:
    """create_session() service must forward start_time, end_time, status."""

    @patch("governance.services.sessions_crud.log_event")
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.session_to_response")
    @patch("governance.services.sessions_crud.get_typedb_client")
    def test_create_session_passes_start_time(
        self, mock_client_fn, mock_resp, mock_audit, mock_log
    ):
        from governance.services.sessions import create_session

        mock_client = MagicMock()
        mock_client.insert_session.return_value = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_resp.return_value = {"session_id": "TEST"}

        create_session(
            session_id="SESSION-TEST-START",
            description="test",
            start_time="2026-03-19T10:00:00",
        )
        _, kwargs = mock_client.insert_session.call_args
        assert kwargs["start_time"] == "2026-03-19T10:00:00"

    @patch("governance.services.sessions_crud.log_event")
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.session_to_response")
    @patch("governance.services.sessions_crud.get_typedb_client")
    def test_create_session_passes_end_time(
        self, mock_client_fn, mock_resp, mock_audit, mock_log
    ):
        from governance.services.sessions import create_session

        mock_client = MagicMock()
        mock_client.insert_session.return_value = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_resp.return_value = {"session_id": "TEST"}

        create_session(
            session_id="SESSION-TEST-END",
            description="test",
            end_time="2026-03-19T12:00:00",
        )
        _, kwargs = mock_client.insert_session.call_args
        assert kwargs["end_time"] == "2026-03-19T12:00:00"

    @patch("governance.services.sessions_crud.log_event")
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.session_to_response")
    @patch("governance.services.sessions_crud.get_typedb_client")
    def test_create_session_passes_status(
        self, mock_client_fn, mock_resp, mock_audit, mock_log
    ):
        from governance.services.sessions import create_session

        mock_client = MagicMock()
        mock_client.insert_session.return_value = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_resp.return_value = {"session_id": "TEST"}

        create_session(
            session_id="SESSION-TEST-STATUS",
            description="test",
            status="COMPLETED",
        )
        _, kwargs = mock_client.insert_session.call_args
        assert kwargs["status"] == "COMPLETED"

    @patch("governance.services.sessions_crud.log_event")
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.session_to_response")
    @patch("governance.services.sessions_crud.get_typedb_client")
    def test_create_session_passes_cc_external_name(
        self, mock_client_fn, mock_resp, mock_audit, mock_log
    ):
        from governance.services.sessions import create_session

        mock_client = MagicMock()
        mock_client.insert_session.return_value = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_resp.return_value = {"session_id": "TEST"}

        create_session(
            session_id="SESSION-TEST-NAME",
            description="test",
            cc_external_name="sarvaja1_P2-10",
        )
        _, kwargs = mock_client.insert_session.call_args
        assert kwargs["cc_external_name"] == "sarvaja1_P2-10"

    @patch("governance.services.sessions_crud._sessions_store", {})
    @patch("governance.services.sessions_crud.log_event")
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.get_typedb_client")
    def test_create_session_fallback_uses_provided_start_time(
        self, mock_client_fn, mock_audit, mock_log
    ):
        from governance.services.sessions import create_session
        mock_client_fn.return_value = None

        result = create_session(
            session_id="SESSION-TEST-FALLBACK",
            description="test",
            start_time="2026-01-15T08:00:00",
        )
        assert result["start_time"] == "2026-01-15T08:00:00"

    @patch("governance.services.sessions_crud._sessions_store", {})
    @patch("governance.services.sessions_crud.log_event")
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.get_typedb_client")
    def test_create_session_fallback_uses_provided_end_time(
        self, mock_client_fn, mock_audit, mock_log
    ):
        from governance.services.sessions import create_session
        mock_client_fn.return_value = None

        result = create_session(
            session_id="SESSION-TEST-FALLBACK-END",
            description="test",
            end_time="2026-01-15T12:00:00",
        )
        assert result["end_time"] == "2026-01-15T12:00:00"

    @patch("governance.services.sessions_crud._sessions_store", {})
    @patch("governance.services.sessions_crud.log_event")
    @patch("governance.services.sessions_crud.record_audit")
    @patch("governance.services.sessions_crud.get_typedb_client")
    def test_create_session_fallback_uses_provided_status(
        self, mock_client_fn, mock_audit, mock_log
    ):
        from governance.services.sessions import create_session
        mock_client_fn.return_value = None

        result = create_session(
            session_id="SESSION-TEST-FALLBACK-STATUS",
            description="test",
            status="COMPLETED",
        )
        assert result["status"] == "COMPLETED"


# ---------------------------------------------------------------------------
# 3. ingest_single_session() must update existing sessions
# ---------------------------------------------------------------------------


_INGEST_META = {
    "slug": "test-session",
    "session_uuid": "abc-123",
    "first_ts": "2026-03-19T10:00:00",
    "last_ts": "2026-03-19T14:00:00",
    "tool_use_count": 5,
    "thinking_chars": 100,
    "user_count": 3,
    "assistant_count": 3,
    "models": [],
    "file_size": 1000,
    "git_branch": None,
    "compaction_count": 0,
    "custom_title": None,
}


class TestIngestUpdateExisting:
    """ingest_single_session() should update end_time on existing sessions."""

    @patch("governance.services.claude_watcher.scan_jsonl_metadata")
    def test_ingest_updates_end_time_on_existing(self, mock_scan):
        """If session exists but end_time changed, should call update_session."""
        from governance.services.claude_watcher import ingest_single_session
        from pathlib import Path

        mock_scan.return_value = {**_INGEST_META, "last_ts": "2026-03-19T14:00:00"}

        with patch("governance.services.sessions.get_session") as mock_get, \
             patch("governance.services.sessions.update_session") as mock_update:
            mock_get.return_value = {
                "session_id": "SESSION-2026-03-19-CC-TEST-SESSION",
                "end_time": "2026-03-19T12:00:00",  # OLD end_time
            }
            ingest_single_session(Path("/tmp/test.jsonl"), "test-proj")
            mock_update.assert_called_once()
            assert mock_update.call_args[1]["end_time"] == "2026-03-19T14:00:00"

    @patch("governance.services.claude_watcher.scan_jsonl_metadata")
    def test_ingest_skips_update_when_end_time_unchanged(self, mock_scan):
        """Should NOT update if end_time is the same."""
        from governance.services.claude_watcher import ingest_single_session
        from pathlib import Path

        mock_scan.return_value = {**_INGEST_META, "last_ts": "2026-03-19T12:00:00"}

        with patch("governance.services.sessions.get_session") as mock_get, \
             patch("governance.services.sessions.update_session") as mock_update:
            mock_get.return_value = {
                "session_id": "SESSION-2026-03-19-CC-TEST-SESSION",
                "end_time": "2026-03-19T12:00:00",  # SAME end_time
            }
            ingest_single_session(Path("/tmp/test.jsonl"), "test-proj")
            mock_update.assert_not_called()


# ---------------------------------------------------------------------------
# 4. customTitle extraction from JSONL
# ---------------------------------------------------------------------------


class TestCustomTitleExtraction:
    """Scanner should extract customTitle from JSONL custom-title entries."""

    def test_scanner_extracts_custom_title(self, tmp_path):
        import json
        from governance.services.cc_session_scanner import scan_jsonl_metadata

        jsonl_file = tmp_path / "test-session.jsonl"
        lines = [
            json.dumps({"type": "user", "timestamp": "2026-03-19T10:00:00",
                         "sessionId": "abc-123"}),
            json.dumps({"type": "assistant", "timestamp": "2026-03-19T10:05:00",
                         "message": {"content": []}}),
            json.dumps({"type": "custom-title", "sessionId": "abc-123",
                         "customTitle": "sarvaja1_P2-10"}),
        ]
        jsonl_file.write_text("\n".join(lines))

        result = scan_jsonl_metadata(jsonl_file)
        assert result is not None
        assert result["custom_title"] == "sarvaja1_P2-10"

    def test_scanner_returns_none_when_no_custom_title(self, tmp_path):
        import json
        from governance.services.cc_session_scanner import scan_jsonl_metadata

        jsonl_file = tmp_path / "test-no-title.jsonl"
        lines = [
            json.dumps({"type": "user", "timestamp": "2026-03-19T10:00:00",
                         "sessionId": "abc-123"}),
        ]
        jsonl_file.write_text("\n".join(lines))

        result = scan_jsonl_metadata(jsonl_file)
        assert result is not None
        assert result.get("custom_title") is None

    def test_scanner_uses_last_custom_title(self, tmp_path):
        """If multiple custom-title entries, use the last one (rename)."""
        import json
        from governance.services.cc_session_scanner import scan_jsonl_metadata

        jsonl_file = tmp_path / "test-multi-title.jsonl"
        lines = [
            json.dumps({"type": "user", "timestamp": "2026-03-19T10:00:00",
                         "sessionId": "abc-123"}),
            json.dumps({"type": "custom-title", "sessionId": "abc-123",
                         "customTitle": "old-name"}),
            json.dumps({"type": "custom-title", "sessionId": "abc-123",
                         "customTitle": "new-name"}),
        ]
        jsonl_file.write_text("\n".join(lines))

        result = scan_jsonl_metadata(jsonl_file)
        assert result["custom_title"] == "new-name"


# ---------------------------------------------------------------------------
# 5. cc_external_name in models and API response
# ---------------------------------------------------------------------------


class TestExternalNameModel:
    """SessionResponse model should have cc_external_name field."""

    def test_session_response_has_external_name(self):
        from governance.models import SessionResponse

        resp = SessionResponse(
            session_id="TEST", start_time="2026-03-19T10:00:00",
            status="ACTIVE", cc_external_name="my-session-name",
        )
        assert resp.cc_external_name == "my-session-name"

    def test_session_response_external_name_optional(self):
        from governance.models import SessionResponse

        resp = SessionResponse(
            session_id="TEST", start_time="2026-03-19T10:00:00",
            status="ACTIVE",
        )
        assert resp.cc_external_name is None

    def test_session_entity_has_external_name(self):
        from governance.client import Session

        session = Session(id="TEST", cc_external_name="my-name")
        assert session.cc_external_name == "my-name"


class TestExternalNameHelpers:
    """Conversion helpers must include cc_external_name."""

    def test_session_to_response_includes_external_name(self):
        from governance.stores.helpers import session_to_response
        from governance.client import Session

        session = Session(id="TEST", status="ACTIVE", cc_external_name="my-project")
        result = session_to_response(session)
        assert result.cc_external_name == "my-project"


# ---------------------------------------------------------------------------
# 6. ingest_single_session passes cc_external_name
# ---------------------------------------------------------------------------


class TestIngestPassesExternalName:
    """ingest_single_session should pass custom_title as cc_external_name."""

    @patch("governance.services.claude_watcher.scan_jsonl_metadata")
    def test_ingest_passes_external_name(self, mock_scan):
        from governance.services.claude_watcher import ingest_single_session
        from pathlib import Path

        mock_scan.return_value = {
            **_INGEST_META,
            "custom_title": "sarvaja1_P2-10",
        }

        with patch("governance.services.sessions.get_session", return_value=None), \
             patch("governance.services.projects.get_project", side_effect=Exception), \
             patch("governance.services.sessions.create_session") as mock_create:
            mock_create.return_value = {"session_id": "SESSION-2026-03-19-CC-TEST"}
            ingest_single_session(Path("/tmp/test.jsonl"), "test-proj")
            _, kwargs = mock_create.call_args
            assert kwargs.get("cc_external_name") == "sarvaja1_P2-10"


# ---------------------------------------------------------------------------
# 7. Sessions auto-refresh polling
# ---------------------------------------------------------------------------


class TestSessionsAutoRefresh:
    """Sessions list should support auto-refresh polling."""

    def test_initial_state_has_auto_refresh_fields(self):
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        assert "sessions_auto_refresh" in state
        assert state["sessions_auto_refresh"] is False
        assert "sessions_refresh_interval" in state
        assert state["sessions_refresh_interval"] >= 5

    def test_auto_refresh_registered_as_trigger(self):
        state = MagicMock()
        ctrl = MagicMock()
        state.sessions_auto_refresh = False
        state.sessions_refresh_interval = 10
        state.active_view = "sessions"
        state.show_session_detail = False

        from agent.governance_ui.controllers.sessions_pagination import (
            register_sessions_pagination,
        )
        register_sessions_pagination(state, ctrl, "http://localhost:8082")

        trigger_names = [
            call.args[0] for call in ctrl.trigger.call_args_list
        ]
        assert "toggle_sessions_auto_refresh" in trigger_names

    def test_sessions_headers_include_name_column(self):
        """Sessions table should have a 'Name' column for cc_external_name."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        headers = state["sessions_headers"]
        name_cols = [h for h in headers if h["key"] == "cc_external_name"]
        assert len(name_cols) == 1
        assert name_cols[0]["title"] == "Name"
