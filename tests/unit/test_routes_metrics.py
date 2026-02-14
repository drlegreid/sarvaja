"""Tests for governance/routes/metrics.py — Session metrics routes.

Covers: _get_session_metrics, _search_session_content, _get_activity_timeline.
Tests the internal helpers which are called by the async endpoints.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from governance.routes.metrics import (
    _get_session_metrics,
    _search_session_content,
    _get_activity_timeline,
)


class TestGetSessionMetrics(unittest.TestCase):
    """Tests for _get_session_metrics helper."""

    @patch("governance.routes.metrics._get_session_metrics.__module__", "governance.routes.metrics")
    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_missing_dir(self, mock_resolve):
        mock_resolve.return_value = Path("/nonexistent/dir")
        result = _get_session_metrics()
        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    @patch("governance.session_metrics.parser.discover_log_files", return_value=[])
    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_no_log_files(self, mock_resolve, mock_discover):
        mock_resolve.return_value = Path("/tmp")
        with patch.object(Path, "is_dir", return_value=True):
            result = _get_session_metrics()
        self.assertIn("error", result)
        self.assertIn("No JSONL", result["error"])

    @patch("governance.session_metrics.agents.calculate_agent_metrics", return_value={})
    @patch("governance.session_metrics.correlation.summarize_correlation", return_value={})
    @patch("governance.session_metrics.correlation.correlate_tool_calls", return_value=[])
    @patch("governance.session_metrics.calculator.calculate_metrics")
    @patch("governance.session_metrics.calculator.filter_entries_by_days")
    @patch("governance.session_metrics.parser.parse_log_file")
    @patch("governance.session_metrics.parser.discover_log_files")
    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_success(self, mock_resolve, mock_discover, mock_parse,
                     mock_filter, mock_calc, mock_corr, mock_summ, mock_agents):
        mock_resolve.return_value = Path("/tmp")
        mock_discover.return_value = [Path("/tmp/log.jsonl")]

        entry = MagicMock()
        mock_parse.return_value = iter([entry])
        mock_filter.return_value = [entry]

        metrics_obj = MagicMock()
        metrics_obj.to_dict.return_value = {"total_sessions": 1}
        mock_calc.return_value = metrics_obj

        with patch.object(Path, "is_dir", return_value=True):
            result = _get_session_metrics(days=5, idle_threshold_min=30)

        self.assertIn("total_sessions", result)
        self.assertIn("metadata", result)
        self.assertEqual(result["metadata"]["days_requested"], 5)

    @patch("governance.session_metrics.parser.parse_log_file")
    @patch("governance.session_metrics.parser.discover_log_files")
    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_no_entries(self, mock_resolve, mock_discover, mock_parse):
        mock_resolve.return_value = Path("/tmp")
        mock_discover.return_value = [Path("/tmp/log.jsonl")]
        mock_parse.return_value = iter([])

        with patch.object(Path, "is_dir", return_value=True):
            result = _get_session_metrics()

        self.assertIn("error", result)
        self.assertIn("No parseable", result["error"])


class TestSearchSessionContent(unittest.TestCase):
    """Tests for _search_session_content helper."""

    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_missing_dir(self, mock_resolve):
        mock_resolve.return_value = Path("/nonexistent/dir")
        result = _search_session_content(query="test")
        self.assertIn("error", result)

    @patch("governance.session_metrics.search.results_to_dicts", return_value=[])
    @patch("governance.session_metrics.search.search_entries", return_value=[])
    @patch("governance.session_metrics.parser.parse_log_file_extended")
    @patch("governance.session_metrics.parser.discover_log_files")
    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_success(self, mock_resolve, mock_discover, mock_parse,
                     mock_search, mock_to_dicts):
        mock_resolve.return_value = Path("/tmp")
        mock_discover.return_value = [Path("/tmp/log.jsonl")]
        mock_parse.return_value = iter([MagicMock()])

        with patch.object(Path, "is_dir", return_value=True):
            result = _search_session_content(query="test")

        self.assertIn("results", result)
        self.assertIn("total_matches", result)
        self.assertEqual(result["metadata"]["query"], "test")


class TestGetActivityTimeline(unittest.TestCase):
    """Tests for _get_activity_timeline helper."""

    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_missing_dir(self, mock_resolve):
        mock_resolve.return_value = Path("/nonexistent/dir")
        result = _get_activity_timeline()
        self.assertEqual(result, [])

    @patch("governance.session_metrics.parser.discover_log_files", return_value=[])
    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_no_files(self, mock_resolve, mock_discover):
        mock_resolve.return_value = Path("/tmp")
        with patch.object(Path, "is_dir", return_value=True):
            result = _get_activity_timeline()
        self.assertEqual(result, [])

    @patch("governance.session_metrics.temporal.activity_timeline", return_value=[{"date": "2026-02-13"}])
    @patch("governance.session_metrics.calculator.filter_entries_by_days")
    @patch("governance.session_metrics.parser.parse_log_file_extended")
    @patch("governance.session_metrics.parser.discover_log_files")
    @patch("governance.mcp_tools.session_metrics._resolve_project_dir")
    def test_success(self, mock_resolve, mock_discover, mock_parse,
                     mock_filter, mock_timeline):
        mock_resolve.return_value = Path("/tmp")
        mock_discover.return_value = [Path("/tmp/log.jsonl")]
        mock_parse.return_value = iter([MagicMock()])
        mock_filter.return_value = [MagicMock()]

        with patch.object(Path, "is_dir", return_value=True):
            result = _get_activity_timeline(days=30)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2026-02-13")


if __name__ == "__main__":
    unittest.main()
