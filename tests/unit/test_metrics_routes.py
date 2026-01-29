"""
TDD Test Spec: Session Metrics API Routes
==========================================
Per GAP-SESSION-METRICS-UI Phase 1: REST API endpoints for session metrics.

Tests written BEFORE implementation per TEST-TDD-01-v1.
Run: pytest tests/unit/test_metrics_routes.py -v
"""

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create test client for the governance API."""
    from governance.api import app
    return TestClient(app)


@pytest.fixture
def mock_metrics_result():
    """Sample MetricsResult.to_dict() output."""
    return {
        "totals": {
            "active_minutes": 120,
            "session_count": 5,
            "message_count": 200,
            "tool_calls": 80,
            "mcp_calls": 15,
            "thinking_chars": 50000,
            "days_covered": 3,
            "api_errors": 2,
            "error_rate": 0.01,
        },
        "days": [
            {
                "date": "2026-01-27",
                "active_minutes": 45,
                "session_count": 2,
                "message_count": 70,
                "tool_calls": 30,
                "mcp_calls": 5,
                "api_errors": 1,
            },
            {
                "date": "2026-01-28",
                "active_minutes": 75,
                "session_count": 3,
                "message_count": 130,
                "tool_calls": 50,
                "mcp_calls": 10,
                "api_errors": 1,
            },
        ],
        "tool_breakdown": {
            "Read": 25,
            "Edit": 20,
            "Bash": 15,
            "mcp__gov-core__health_check": 10,
        },
        "correlation": {
            "total_correlated": 40,
            "avg_latency_ms": 250,
            "by_tool": {"Read": {"count": 15, "avg_ms": 200}},
        },
        "agents": {
            "agent_files": 2,
            "total_entries": 50,
        },
        "metadata": {
            "log_dir": "/home/user/.claude/projects/-home-user-project",
            "log_files": ["main.jsonl"],
            "total_entries_parsed": 500,
        },
    }


@pytest.fixture
def mock_search_result():
    """Sample session search output."""
    return {
        "results": [
            {
                "timestamp": "2026-01-28T10:15:00Z",
                "entry_type": "assistant",
                "text_content": "Fixing auth bug in login module.",
                "session_id": "sess-A",
                "git_branch": "main",
                "tool_names": ["Read"],
            }
        ],
        "total_matches": 1,
        "metadata": {
            "total_entries_searched": 500,
            "query": "auth bug",
        },
    }


@pytest.fixture
def mock_timeline_result():
    """Sample activity timeline output."""
    return [
        {
            "date": "2026-01-27",
            "entry_count": 5,
            "tools_used": ["Edit", "Read"],
            "branches": ["main"],
            "snippets": ["Fixing auth bug"],
        },
        {
            "date": "2026-01-28",
            "entry_count": 3,
            "tools_used": ["Bash"],
            "branches": ["main"],
            "snippets": ["Running tests"],
        },
    ]


# ---------------------------------------------------------------------------
# Tests: GET /api/metrics/summary
# ---------------------------------------------------------------------------

class TestMetricsSummary:
    """Test the metrics summary endpoint."""

    @patch("governance.routes.metrics._get_session_metrics")
    def test_summary_returns_200(self, mock_fn, client, mock_metrics_result):
        """GET /api/metrics/summary returns 200."""
        mock_fn.return_value = mock_metrics_result
        response = client.get("/api/metrics/summary")
        assert response.status_code == 200

    @patch("governance.routes.metrics._get_session_metrics")
    def test_summary_has_totals(self, mock_fn, client, mock_metrics_result):
        """Response includes totals dict."""
        mock_fn.return_value = mock_metrics_result
        response = client.get("/api/metrics/summary")
        data = response.json()
        assert "totals" in data
        assert data["totals"]["session_count"] == 5

    @patch("governance.routes.metrics._get_session_metrics")
    def test_summary_has_days(self, mock_fn, client, mock_metrics_result):
        """Response includes per-day breakdown."""
        mock_fn.return_value = mock_metrics_result
        response = client.get("/api/metrics/summary")
        data = response.json()
        assert "days" in data
        assert len(data["days"]) == 2

    @patch("governance.routes.metrics._get_session_metrics")
    def test_summary_has_tool_breakdown(self, mock_fn, client, mock_metrics_result):
        """Response includes tool usage breakdown."""
        mock_fn.return_value = mock_metrics_result
        response = client.get("/api/metrics/summary")
        data = response.json()
        assert "tool_breakdown" in data
        assert "Read" in data["tool_breakdown"]

    @patch("governance.routes.metrics._get_session_metrics")
    def test_summary_accepts_days_param(self, mock_fn, client, mock_metrics_result):
        """Days query parameter is passed through."""
        mock_fn.return_value = mock_metrics_result
        client.get("/api/metrics/summary?days=14")
        mock_fn.assert_called_once_with(days=14, idle_threshold_min=30)

    @patch("governance.routes.metrics._get_session_metrics")
    def test_summary_error_returns_error_dict(self, mock_fn, client):
        """When metrics engine fails, returns error response."""
        mock_fn.return_value = {"error": "No log files found"}
        response = client.get("/api/metrics/summary")
        data = response.json()
        assert "error" in data


# ---------------------------------------------------------------------------
# Tests: GET /api/metrics/search
# ---------------------------------------------------------------------------

class TestMetricsSearch:
    """Test the metrics search endpoint."""

    @patch("governance.routes.metrics._search_session_content")
    def test_search_returns_200(self, mock_fn, client, mock_search_result):
        """GET /api/metrics/search returns 200."""
        mock_fn.return_value = mock_search_result
        response = client.get("/api/metrics/search?query=auth")
        assert response.status_code == 200

    @patch("governance.routes.metrics._search_session_content")
    def test_search_returns_results(self, mock_fn, client, mock_search_result):
        """Search response has results list."""
        mock_fn.return_value = mock_search_result
        response = client.get("/api/metrics/search?query=auth")
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1

    @patch("governance.routes.metrics._search_session_content")
    def test_search_passes_branch_filter(self, mock_fn, client, mock_search_result):
        """Git branch filter is passed through."""
        mock_fn.return_value = mock_search_result
        client.get("/api/metrics/search?query=test&git_branch=main")
        mock_fn.assert_called_once_with(
            query="test", session_id=None, git_branch="main", max_results=50
        )

    @patch("governance.routes.metrics._search_session_content")
    def test_search_empty_query(self, mock_fn, client):
        """Empty query returns results (match all)."""
        mock_fn.return_value = {"results": [], "total_matches": 0, "metadata": {}}
        response = client.get("/api/metrics/search")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests: GET /api/metrics/timeline
# ---------------------------------------------------------------------------

class TestMetricsTimeline:
    """Test the activity timeline endpoint."""

    @patch("governance.routes.metrics._get_activity_timeline")
    def test_timeline_returns_200(self, mock_fn, client, mock_timeline_result):
        """GET /api/metrics/timeline returns 200."""
        mock_fn.return_value = mock_timeline_result
        response = client.get("/api/metrics/timeline")
        assert response.status_code == 200

    @patch("governance.routes.metrics._get_activity_timeline")
    def test_timeline_is_list(self, mock_fn, client, mock_timeline_result):
        """Timeline response is a list of day dicts."""
        mock_fn.return_value = mock_timeline_result
        response = client.get("/api/metrics/timeline")
        data = response.json()
        assert "timeline" in data
        assert isinstance(data["timeline"], list)
        assert len(data["timeline"]) == 2

    @patch("governance.routes.metrics._get_activity_timeline")
    def test_timeline_sorted_by_date(self, mock_fn, client, mock_timeline_result):
        """Timeline entries are sorted by date."""
        mock_fn.return_value = mock_timeline_result
        response = client.get("/api/metrics/timeline")
        data = response.json()
        dates = [t["date"] for t in data["timeline"]]
        assert dates == sorted(dates)

    @patch("governance.routes.metrics._get_activity_timeline")
    def test_timeline_has_entry_count(self, mock_fn, client, mock_timeline_result):
        """Each timeline entry has entry_count."""
        mock_fn.return_value = mock_timeline_result
        response = client.get("/api/metrics/timeline")
        data = response.json()
        for t in data["timeline"]:
            assert "entry_count" in t
            assert t["entry_count"] > 0
