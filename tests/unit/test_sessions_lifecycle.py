"""
Unit tests for Session Lifecycle — end_session and delete_session operations.

Per DOC-SIZE-01-v1: Tests for extracted sessions_lifecycle.py module.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.services.sessions_lifecycle import (
    delete_session,
    end_session,
)
from governance.stores import _sessions_store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear session store between tests."""
    saved = dict(_sessions_store)
    yield
    _sessions_store.clear()
    _sessions_store.update(saved)


class TestDeleteSession:
    """Tests for delete_session()."""

    @patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_delete_from_memory(self, mock_mon, mock_log, mock_audit, mock_client):
        _sessions_store["S-DEL"] = {"session_id": "S-DEL", "status": "COMPLETED"}
        result = delete_session("S-DEL")
        assert result is True
        assert "S-DEL" not in _sessions_store
        mock_audit.assert_called_once()

    @patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_delete_nonexistent(self, mock_mon, mock_log, mock_audit, mock_client):
        result = delete_session("NOPE")
        assert result is False
        mock_audit.assert_not_called()

    @patch("governance.services.sessions_lifecycle.get_typedb_client")
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_delete_from_typedb(self, mock_mon, mock_log, mock_audit, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_session.return_value = MagicMock()
        mock_client.delete_session.return_value = True
        mock_client_fn.return_value = mock_client

        result = delete_session("S-TB")
        assert result is True
        mock_client.delete_session.assert_called_once_with("S-TB")

    @patch("governance.services.sessions_lifecycle.get_typedb_client")
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_delete_typedb_error_falls_back(self, mock_mon, mock_log, mock_audit, mock_client_fn):
        mock_client = MagicMock()
        mock_client.get_session.side_effect = Exception("DB error")
        mock_client_fn.return_value = mock_client

        _sessions_store["S-FB"] = {"session_id": "S-FB"}
        result = delete_session("S-FB")
        assert result is True
        assert "S-FB" not in _sessions_store


class TestEndSession:
    """Tests for end_session()."""

    @patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_end_active_session(self, mock_mon, mock_log, mock_audit, mock_client):
        _sessions_store["S-END"] = {
            "session_id": "S-END", "status": "ACTIVE",
        }
        result = end_session("S-END")
        assert result is not None
        assert result["status"] == "COMPLETED"
        assert "end_time" in result

    @patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_end_nonexistent(self, mock_mon, mock_log, mock_audit, mock_client):
        result = end_session("NOPE")
        assert result is None

    @patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_end_already_completed_raises(self, mock_mon, mock_log, mock_audit, mock_client):
        _sessions_store["S-DONE"] = {
            "session_id": "S-DONE", "status": "COMPLETED",
        }
        with pytest.raises(ValueError, match="already completed"):
            end_session("S-DONE")

    @patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_end_with_tasks_completed(self, mock_mon, mock_log, mock_audit, mock_client):
        _sessions_store["S-TC"] = {
            "session_id": "S-TC", "status": "ACTIVE",
        }
        result = end_session("S-TC", tasks_completed=5)
        assert result["tasks_completed"] == 5

    @patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_end_with_evidence_files(self, mock_mon, mock_log, mock_audit, mock_client):
        _sessions_store["S-EV"] = {
            "session_id": "S-EV", "status": "ACTIVE",
        }
        result = end_session("S-EV", evidence_files=["ev1.md", "ev2.md"])
        assert result["evidence_files"] == ["ev1.md", "ev2.md"]

    @patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None)
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_end_records_audit(self, mock_mon, mock_log, mock_audit, mock_client):
        _sessions_store["S-AUD"] = {
            "session_id": "S-AUD", "status": "ACTIVE",
        }
        end_session("S-AUD", source="mcp")
        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args
        assert call_kwargs[0][0] == "UPDATE"
        assert call_kwargs[0][1] == "session"

    @patch("governance.services.sessions_lifecycle.get_typedb_client")
    @patch("governance.services.sessions_lifecycle.record_audit")
    @patch("governance.services.sessions_lifecycle.log_event")
    @patch("governance.services.sessions_lifecycle._monitor")
    def test_end_via_typedb(self, mock_mon, mock_log, mock_audit, mock_client_fn):
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.get_session.return_value = mock_session
        mock_client.end_session.return_value = mock_session
        mock_client_fn.return_value = mock_client

        with patch("governance.services.sessions_lifecycle.session_to_response",
                    return_value={"session_id": "S-TB", "status": "COMPLETED"}):
            result = end_session("S-TB")

        assert result is not None
        assert result["status"] == "COMPLETED"
        mock_client.end_session.assert_called_once_with("S-TB")
