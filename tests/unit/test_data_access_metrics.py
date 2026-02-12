"""
Unit tests for Data Access Metrics Functions.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/data_access/metrics.py.
Tests: get_session_metrics_summary, search_session_content, get_activity_timeline.
"""

from unittest.mock import patch, MagicMock

from agent.governance_ui.data_access.metrics import (
    get_session_metrics_summary,
    search_session_content,
    get_activity_timeline,
)


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


# ── get_session_metrics_summary ───────────────────────


class TestGetSessionMetricsSummary:
    @patch("httpx.Client")
    def test_success(self, MockClient):
        data = {"totals": {"sessions": 10}, "days": [], "tool_breakdown": {}}
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, data)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = get_session_metrics_summary(days=5)
        assert result == data
        mc.get.assert_called_once()
        args = mc.get.call_args
        assert args[1]["params"]["days"] == 5

    @patch("httpx.Client")
    def test_non_200(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(500)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = get_session_metrics_summary()
        assert "error" in result
        assert result["totals"] == {}
        assert result["days"] == []

    @patch("httpx.Client")
    def test_exception(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("connection refused"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = get_session_metrics_summary()
        assert "error" in result
        assert "connection refused" in result["error"]

    @patch("httpx.Client")
    def test_custom_params(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        get_session_metrics_summary(days=10, idle_threshold_min=60)
        params = mc.get.call_args[1]["params"]
        assert params["days"] == 10
        assert params["idle_threshold_min"] == 60


# ── search_session_content ────────────────────────────


class TestSearchSessionContent:
    @patch("httpx.Client")
    def test_basic_search(self, MockClient):
        data = {"results": [{"match": "test"}], "total_matches": 1}
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, data)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = search_session_content(query="test")
        assert result["total_matches"] == 1

    @patch("httpx.Client")
    def test_with_filters(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"results": [], "total_matches": 0})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        search_session_content(
            query="fix", session_id="S-1", git_branch="master", max_results=10)
        params = mc.get.call_args[1]["params"]
        assert params["session_id"] == "S-1"
        assert params["git_branch"] == "master"
        assert params["max_results"] == 10

    @patch("httpx.Client")
    def test_non_200(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(404)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = search_session_content(query="test")
        assert "error" in result
        assert result["results"] == []
        assert result["total_matches"] == 0

    @patch("httpx.Client")
    def test_exception(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("timeout"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = search_session_content(query="test")
        assert "error" in result
        assert "timeout" in result["error"]

    @patch("httpx.Client")
    def test_optional_filters_excluded(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, {"results": [], "total_matches": 0})
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        search_session_content(query="test")
        params = mc.get.call_args[1]["params"]
        assert "session_id" not in params
        assert "git_branch" not in params


# ── get_activity_timeline ─────────────────────────────


class TestGetActivityTimeline:
    @patch("httpx.Client")
    def test_success(self, MockClient):
        data = {"timeline": [{"date": "2026-02-11", "count": 5}]}
        mc = MagicMock()
        mc.get.return_value = _mock_response(200, data)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = get_activity_timeline(days=30)
        assert result["timeline"][0]["count"] == 5

    @patch("httpx.Client")
    def test_non_200(self, MockClient):
        mc = MagicMock()
        mc.get.return_value = _mock_response(503)
        MockClient.return_value.__enter__ = MagicMock(return_value=mc)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = get_activity_timeline()
        assert "error" in result
        assert result["timeline"] == []

    @patch("httpx.Client")
    def test_exception(self, MockClient):
        MockClient.return_value.__enter__ = MagicMock(
            side_effect=Exception("dns failure"))
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = get_activity_timeline()
        assert "error" in result
        assert "dns failure" in result["error"]
