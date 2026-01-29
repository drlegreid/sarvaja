"""
TDD Test Spec: Session Metrics Data Access Layer
=================================================
Per GAP-SESSION-METRICS-UI Phase 2: Data access functions for dashboard.

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_metrics_data_access.py -v
"""

from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Tests: get_session_metrics_summary
# ---------------------------------------------------------------------------

class TestGetSessionMetricsSummary:
    """Test the metrics summary data access function."""

    @patch("agent.governance_ui.data_access.metrics.httpx")
    def test_returns_dict(self, mock_httpx):
        """get_session_metrics_summary returns a dict."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"totals": {}, "days": []}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        from agent.governance_ui.data_access.metrics import get_session_metrics_summary
        result = get_session_metrics_summary()
        assert isinstance(result, dict)

    @patch("agent.governance_ui.data_access.metrics.httpx")
    def test_handles_api_error(self, mock_httpx):
        """Returns error dict on API failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        from agent.governance_ui.data_access.metrics import get_session_metrics_summary
        result = get_session_metrics_summary()
        assert "error" in result

    @patch("agent.governance_ui.data_access.metrics.httpx")
    def test_handles_connection_error(self, mock_httpx):
        """Returns error dict on connection failure."""
        mock_httpx.Client.side_effect = Exception("Connection refused")

        from agent.governance_ui.data_access.metrics import get_session_metrics_summary
        result = get_session_metrics_summary()
        assert "error" in result


# ---------------------------------------------------------------------------
# Tests: search_session_content
# ---------------------------------------------------------------------------

class TestSearchSessionContent:
    """Test the session search data access function."""

    @patch("agent.governance_ui.data_access.metrics.httpx")
    def test_returns_dict(self, mock_httpx):
        """search_session_content returns a dict."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [], "total_matches": 0}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        from agent.governance_ui.data_access.metrics import search_session_content
        result = search_session_content(query="test")
        assert isinstance(result, dict)
        assert "results" in result


# ---------------------------------------------------------------------------
# Tests: get_activity_timeline
# ---------------------------------------------------------------------------

class TestGetActivityTimeline:
    """Test the activity timeline data access function."""

    @patch("agent.governance_ui.data_access.metrics.httpx")
    def test_returns_dict(self, mock_httpx):
        """get_activity_timeline returns a dict."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"timeline": [], "metadata": {}}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        from agent.governance_ui.data_access.metrics import get_activity_timeline
        result = get_activity_timeline()
        assert isinstance(result, dict)

    @patch("agent.governance_ui.data_access.metrics.httpx")
    def test_handles_error(self, mock_httpx):
        """Returns error dict on failure."""
        mock_httpx.Client.side_effect = Exception("Connection refused")

        from agent.governance_ui.data_access.metrics import get_activity_timeline
        result = get_activity_timeline()
        assert "error" in result
