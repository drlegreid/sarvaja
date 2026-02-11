"""
Unit tests for Workflow Compliance API Client.

Per DOC-SIZE-01-v1: Tests for extracted api_client.py module.
Tests: fetch_tasks, fetch_rules, fetch_sessions.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.workflow_compliance.api_client import (
    fetch_tasks,
    fetch_rules,
    fetch_sessions,
    API_BASE,
)


# ---------------------------------------------------------------------------
# fetch_tasks
# ---------------------------------------------------------------------------
class TestFetchTasks:
    """Tests for fetch_tasks()."""

    @patch("httpx.get")
    def test_returns_items_from_dict(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [{"id": "T-1"}, {"id": "T-2"}]}
        mock_get.return_value = resp

        result = fetch_tasks()
        assert len(result) == 2
        assert result[0]["id"] == "T-1"

    @patch("httpx.get")
    def test_returns_tasks_key_from_dict(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"tasks": [{"id": "T-1"}]}
        mock_get.return_value = resp

        result = fetch_tasks()
        assert len(result) == 1

    @patch("httpx.get")
    def test_returns_list_directly(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": "T-1"}, {"id": "T-2"}]
        mock_get.return_value = resp

        result = fetch_tasks()
        assert len(result) == 2

    @patch("httpx.get")
    def test_non_200_returns_empty(self, mock_get):
        resp = MagicMock()
        resp.status_code = 500
        mock_get.return_value = resp

        assert fetch_tasks() == []

    def test_import_error_returns_empty(self):
        with patch.dict("sys.modules", {"httpx": None}):
            assert fetch_tasks() == []

    @patch("httpx.get")
    def test_exception_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        assert fetch_tasks() == []

    @patch("httpx.get")
    def test_uses_correct_url(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = []
        mock_get.return_value = resp

        fetch_tasks()
        call_url = mock_get.call_args[0][0]
        assert "/api/tasks" in call_url

    @patch("httpx.get")
    def test_dict_without_items_or_tasks_returns_empty(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"other_key": "value"}
        mock_get.return_value = resp

        result = fetch_tasks()
        assert result == []


# ---------------------------------------------------------------------------
# fetch_rules
# ---------------------------------------------------------------------------
class TestFetchRules:
    """Tests for fetch_rules()."""

    @patch("httpx.get")
    def test_returns_list_directly(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"rule_id": "R-1"}]
        mock_get.return_value = resp

        result = fetch_rules()
        assert len(result) == 1
        assert result[0]["rule_id"] == "R-1"

    @patch("httpx.get")
    def test_returns_rules_from_dict(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"rules": [{"rule_id": "R-1"}, {"rule_id": "R-2"}]}
        mock_get.return_value = resp

        result = fetch_rules()
        assert len(result) == 2

    @patch("httpx.get")
    def test_returns_items_from_dict(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [{"rule_id": "R-1"}]}
        mock_get.return_value = resp

        result = fetch_rules()
        assert len(result) == 1

    @patch("httpx.get")
    def test_non_200_returns_empty(self, mock_get):
        resp = MagicMock()
        resp.status_code = 404
        mock_get.return_value = resp

        assert fetch_rules() == []

    @patch("httpx.get")
    def test_exception_returns_empty(self, mock_get):
        mock_get.side_effect = ConnectionError("timeout")
        assert fetch_rules() == []

    @patch("httpx.get")
    def test_uses_correct_url(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = []
        mock_get.return_value = resp

        fetch_rules()
        call_url = mock_get.call_args[0][0]
        assert "/api/rules" in call_url


# ---------------------------------------------------------------------------
# fetch_sessions
# ---------------------------------------------------------------------------
class TestFetchSessions:
    """Tests for fetch_sessions()."""

    @patch("httpx.get")
    def test_returns_sessions_from_dict(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"sessions": [{"id": "S-1"}]}
        mock_get.return_value = resp

        result = fetch_sessions()
        assert len(result) == 1
        assert result[0]["id"] == "S-1"

    @patch("httpx.get")
    def test_returns_list_directly(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": "S-1"}, {"id": "S-2"}]
        mock_get.return_value = resp

        result = fetch_sessions()
        assert len(result) == 2

    @patch("httpx.get")
    def test_non_200_returns_empty(self, mock_get):
        resp = MagicMock()
        resp.status_code = 503
        mock_get.return_value = resp

        assert fetch_sessions() == []

    @patch("httpx.get")
    def test_exception_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("DNS fail")
        assert fetch_sessions() == []

    @patch("httpx.get")
    def test_uses_correct_url_with_limit(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"sessions": []}
        mock_get.return_value = resp

        fetch_sessions()
        call_url = mock_get.call_args[0][0]
        assert "/api/sessions" in call_url
        assert "limit=100" in call_url


# ---------------------------------------------------------------------------
# API_BASE constant
# ---------------------------------------------------------------------------
class TestApiBase:
    """Tests for API_BASE constant."""

    def test_default_value(self):
        assert "localhost" in API_BASE or "8082" in API_BASE
