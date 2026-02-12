"""
Unit tests for Compat - Session Collector Exports.

Per DOC-SIZE-01-v1: Tests for compat/sessions.py module.
Tests: session_start, session_decision, session_task, session_end, session_list.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestSessionStart:
    """Tests for session_start()."""

    @patch("governance.compat.sessions._SESSION_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.sessions import session_start
        result = json.loads(session_start("test"))
        assert "error" in result

    @patch("governance.compat.sessions._SESSION_AVAILABLE", True)
    @patch("governance.compat.sessions.get_or_create_session")
    def test_success(self, mock_get):
        mock_collector = MagicMock()
        mock_collector.session_id = "SESSION-2026-02-11-TEST"
        mock_collector.start_time.isoformat.return_value = "2026-02-11T10:00:00"
        mock_get.return_value = mock_collector

        from governance.compat.sessions import session_start
        result = json.loads(session_start("test", "chat"))
        assert result["session_id"] == "SESSION-2026-02-11-TEST"
        assert result["topic"] == "test"
        assert result["session_type"] == "chat"


class TestSessionDecision:
    """Tests for session_decision()."""

    @patch("governance.compat.sessions._SESSION_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.sessions import session_decision
        result = json.loads(session_decision("D-1", "test", "ctx", "reason"))
        assert "error" in result

    @patch("governance.compat.sessions._SESSION_AVAILABLE", True)
    @patch("governance.compat.sessions.list_active_sessions", return_value=[])
    def test_no_session_no_topic(self, mock_list):
        from governance.compat.sessions import session_decision
        result = json.loads(session_decision("D-1", "test", "ctx", "reason"))
        assert "error" in result

    @patch("governance.compat.sessions._SESSION_AVAILABLE", True)
    @patch("governance.compat.sessions.get_or_create_session")
    @patch("governance.compat.sessions.list_active_sessions", return_value=[])
    def test_with_topic(self, mock_list, mock_get):
        mock_collector = MagicMock()
        mock_collector.session_id = "SESSION-2026-02-11-TEST"
        mock_collector.capture_decision.return_value = MagicMock()
        mock_get.return_value = mock_collector

        from governance.compat.sessions import session_decision
        result = json.loads(session_decision("D-1", "test", "ctx", "reason", topic="test"))
        assert result["decision_id"] == "D-1"


class TestSessionTask:
    """Tests for session_task()."""

    @patch("governance.compat.sessions._SESSION_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.sessions import session_task
        result = json.loads(session_task("T-1", "test", "desc"))
        assert "error" in result

    @patch("governance.compat.sessions._SESSION_AVAILABLE", True)
    @patch("governance.compat.sessions.get_or_create_session")
    @patch("governance.compat.sessions.list_active_sessions", return_value=[])
    def test_with_topic(self, mock_list, mock_get):
        mock_collector = MagicMock()
        mock_collector.session_id = "SESSION-2026-02-11-TEST"
        mock_collector.capture_task.return_value = MagicMock()
        mock_get.return_value = mock_collector

        from governance.compat.sessions import session_task
        result = json.loads(session_task("T-1", "test", "desc", topic="test"))
        assert result["task_id"] == "T-1"


class TestSessionEnd:
    """Tests for session_end()."""

    @patch("governance.compat.sessions._SESSION_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.sessions import session_end
        result = json.loads(session_end("test"))
        assert "error" in result

    @patch("governance.compat.sessions._SESSION_AVAILABLE", True)
    @patch("governance.compat.sessions._end_session", return_value="/path/to/log.md")
    def test_success(self, mock_end):
        from governance.compat.sessions import session_end
        result = json.loads(session_end("test"))
        assert result["log_path"] == "/path/to/log.md"

    @patch("governance.compat.sessions._SESSION_AVAILABLE", True)
    @patch("governance.compat.sessions._end_session", return_value=None)
    def test_not_found(self, mock_end):
        from governance.compat.sessions import session_end
        result = json.loads(session_end("nonexistent"))
        assert "error" in result


class TestSessionList:
    """Tests for session_list()."""

    @patch("governance.compat.sessions._SESSION_AVAILABLE", False)
    def test_unavailable(self):
        from governance.compat.sessions import session_list
        result = json.loads(session_list())
        assert "error" in result

    @patch("governance.compat.sessions._SESSION_AVAILABLE", True)
    @patch("governance.compat.sessions.list_active_sessions", return_value=["S-1", "S-2"])
    def test_success(self, mock_list):
        from governance.compat.sessions import session_list
        result = json.loads(session_list())
        assert result["count"] == 2
        assert result["active_sessions"] == ["S-1", "S-2"]
