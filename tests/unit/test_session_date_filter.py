"""TDD Tests: Session date range filtering.

Validates that the sessions list API supports date_from and date_to
query parameters for histogram-driven filtering.
"""
from unittest.mock import patch, MagicMock

import pytest


class TestSessionDateFilterService:
    """Service layer correctly filters sessions by date range."""

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_date_from_filters_sessions(self, mock_get):
        from governance.services.sessions import list_sessions
        mock_get.return_value = [
            {"session_id": "S-1", "start_time": "2026-02-10T10:00:00", "status": "COMPLETED"},
            {"session_id": "S-2", "start_time": "2026-02-12T10:00:00", "status": "COMPLETED"},
            {"session_id": "S-3", "start_time": "2026-02-14T10:00:00", "status": "ACTIVE"},
        ]
        result = list_sessions(date_from="2026-02-12")
        ids = [s["session_id"] for s in result["items"]]
        assert "S-1" not in ids
        assert "S-2" in ids
        assert "S-3" in ids

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_date_to_filters_sessions(self, mock_get):
        from governance.services.sessions import list_sessions
        mock_get.return_value = [
            {"session_id": "S-1", "start_time": "2026-02-10T10:00:00", "status": "COMPLETED"},
            {"session_id": "S-2", "start_time": "2026-02-12T10:00:00", "status": "COMPLETED"},
            {"session_id": "S-3", "start_time": "2026-02-14T10:00:00", "status": "ACTIVE"},
        ]
        result = list_sessions(date_to="2026-02-12")
        ids = [s["session_id"] for s in result["items"]]
        assert "S-1" in ids
        assert "S-2" in ids
        assert "S-3" not in ids

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_date_range_filters_sessions(self, mock_get):
        from governance.services.sessions import list_sessions
        mock_get.return_value = [
            {"session_id": "S-1", "start_time": "2026-02-10T10:00:00", "status": "COMPLETED"},
            {"session_id": "S-2", "start_time": "2026-02-12T10:00:00", "status": "COMPLETED"},
            {"session_id": "S-3", "start_time": "2026-02-14T10:00:00", "status": "ACTIVE"},
        ]
        result = list_sessions(date_from="2026-02-11", date_to="2026-02-13")
        ids = [s["session_id"] for s in result["items"]]
        assert len(ids) == 1
        assert "S-2" in ids

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_no_date_filter_returns_all(self, mock_get):
        from governance.services.sessions import list_sessions
        mock_get.return_value = [
            {"session_id": "S-1", "start_time": "2026-02-10T10:00:00", "status": "COMPLETED"},
            {"session_id": "S-2", "start_time": "2026-02-14T10:00:00", "status": "ACTIVE"},
        ]
        result = list_sessions()
        assert len(result["items"]) == 2

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_sessions_missing_start_time_excluded_by_date_from(self, mock_get):
        from governance.services.sessions import list_sessions
        mock_get.return_value = [
            {"session_id": "S-1", "start_time": None, "status": "COMPLETED"},
            {"session_id": "S-2", "start_time": "2026-02-14T10:00:00", "status": "ACTIVE"},
        ]
        result = list_sessions(date_from="2026-02-01")
        ids = [s["session_id"] for s in result["items"]]
        assert "S-1" not in ids
        assert "S-2" in ids
