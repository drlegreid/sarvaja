"""Tests for governance/routes/reports.py — Executive report generation.

Covers: _generate_recommendations, _generate_objectives, _generate_executive_report,
get_executive_report, get_session_executive_report.
"""

import unittest
from unittest.mock import patch, MagicMock

from governance.routes.reports import (
    _generate_recommendations,
    _generate_objectives,
    _generate_executive_report,
)


class TestGenerateRecommendations(unittest.TestCase):
    """Tests for _generate_recommendations helper."""

    def test_high_pending_tasks(self):
        result = _generate_recommendations(pending_tasks=15, avg_trust=0.9, active_rules=30)
        self.assertIn("backlog reduction", result)

    def test_low_trust(self):
        result = _generate_recommendations(pending_tasks=5, avg_trust=0.5, active_rules=30)
        self.assertIn("trust scores", result)

    def test_few_active_rules(self):
        result = _generate_recommendations(pending_tasks=5, avg_trust=0.9, active_rules=10)
        self.assertIn("governance rules", result)

    def test_all_good(self):
        result = _generate_recommendations(pending_tasks=5, avg_trust=0.9, active_rules=30)
        self.assertIn("normal parameters", result)

    def test_multiple_issues(self):
        result = _generate_recommendations(pending_tasks=20, avg_trust=0.5, active_rules=10)
        self.assertIn("backlog", result)
        self.assertIn("trust", result)
        self.assertIn("rules", result)

    def test_ends_with_period(self):
        result = _generate_recommendations(pending_tasks=5, avg_trust=0.9, active_rules=30)
        self.assertTrue(result.endswith("."))


class TestGenerateObjectives(unittest.TestCase):
    """Tests for _generate_objectives helper."""

    def test_with_pending_tasks(self):
        result = _generate_objectives(pending_tasks=5, completed_tasks=3)
        self.assertIn("priority tasks", result)
        self.assertIn("DSP cycle", result)

    def test_no_pending_tasks(self):
        result = _generate_objectives(pending_tasks=0, completed_tasks=3)
        self.assertNotIn("priority tasks", result)
        self.assertIn("DSP cycle", result)

    def test_archive_suggestion(self):
        result = _generate_objectives(pending_tasks=1, completed_tasks=10)
        self.assertIn("Archive", result)

    def test_no_archive_for_few_completed(self):
        result = _generate_objectives(pending_tasks=1, completed_tasks=3)
        self.assertNotIn("Archive", result)

    def test_caps_pending_at_three(self):
        result = _generate_objectives(pending_tasks=100, completed_tasks=0)
        self.assertIn("top 3", result)

    def test_ends_with_period(self):
        result = _generate_objectives(pending_tasks=1, completed_tasks=0)
        self.assertTrue(result.endswith("."))


class TestGenerateExecutiveReport(unittest.TestCase):
    """Tests for _generate_executive_report."""

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {
        "a1": {"status": "ACTIVE", "trust_score": 0.9, "tasks_executed": 10},
    })
    @patch("governance.routes.reports._sessions_store", {
        "s1": {"status": "ACTIVE"},
    })
    @patch("governance.routes.reports._tasks_store", {
        "t1": {"status": "DONE"},
        "t2": {"status": "TODO"},
    })
    def test_report_structure(self, mock_client):
        mock_client.return_value = None  # No TypeDB
        report = _generate_executive_report()
        self.assertTrue(report.report_id.startswith("EXEC-"))
        self.assertEqual(len(report.sections), 7)
        self.assertIsNotNone(report.overall_status)
        self.assertIsNotNone(report.metrics_summary)

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {
        "a1": {"status": "ACTIVE", "trust_score": 0.95, "tasks_executed": 5},
    })
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {
        "t1": {"status": "DONE"},
    })
    def test_healthy_status(self, mock_client):
        mock_client.return_value = None
        report = _generate_executive_report()
        self.assertEqual(report.overall_status, "healthy")

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {
        "a1": {"status": "STOPPED", "trust_score": 0.4, "tasks_executed": 0},
    })
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {
        "t1": {"status": "TODO"},
        "t2": {"status": "TODO"},
    })
    def test_critical_status(self, mock_client):
        mock_client.return_value = None
        report = _generate_executive_report()
        self.assertEqual(report.overall_status, "critical")

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_empty_stores(self, mock_client):
        mock_client.return_value = None
        report = _generate_executive_report()
        self.assertEqual(report.metrics_summary["tasks_total"], 0)

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_session_id_period(self, mock_client):
        mock_client.return_value = None
        report = _generate_executive_report(session_id="SESSION-2026-02-13-TEST")
        self.assertEqual(report.period, "SESSION-2026-02-13-TEST")

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_date_range_period(self, mock_client):
        mock_client.return_value = None
        report = _generate_executive_report(start_date="2026-02-01", end_date="2026-02-13")
        self.assertEqual(report.period, "2026-02-01 to 2026-02-13")

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_with_typedb_rules(self, mock_client):
        client = MagicMock()
        rule1 = MagicMock(status="ACTIVE")
        rule2 = MagicMock(status="DEPRECATED")
        client.get_all_rules.return_value = [rule1, rule2]
        mock_client.return_value = client
        report = _generate_executive_report()
        self.assertEqual(report.metrics_summary["total_rules"], 2)
        self.assertEqual(report.metrics_summary["active_rules"], 1)

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_section_titles(self, mock_client):
        mock_client.return_value = None
        report = _generate_executive_report()
        titles = [s.title for s in report.sections]
        self.assertIn("Executive Summary", titles)
        self.assertIn("Compliance Status", titles)
        self.assertIn("Risk Assessment", titles)
        self.assertIn("Strategic Alignment", titles)
        self.assertIn("Resource Utilization", titles)
        self.assertIn("Recommendations", titles)
        self.assertIn("Next Session Objectives", titles)

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_metrics_summary_keys(self, mock_client):
        mock_client.return_value = None
        report = _generate_executive_report()
        expected_keys = {"tasks_total", "tasks_completed", "tasks_pending",
                         "sessions_total", "total_agents", "total_rules",
                         "active_rules", "compliance_rate", "avg_trust_score"}
        self.assertTrue(expected_keys.issubset(set(report.metrics_summary.keys())))


if __name__ == "__main__":
    unittest.main()
