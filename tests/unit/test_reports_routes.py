"""
Unit tests for Reports Routes.

Per DOC-SIZE-01-v1: Tests for routes/reports.py module.
Tests: _generate_recommendations, _generate_objectives,
       _generate_executive_report, get_executive_report,
       get_session_executive_report.
"""

from unittest.mock import patch, MagicMock

import pytest

from governance.routes.reports import (
    _generate_recommendations,
    _generate_objectives,
    _generate_executive_report,
)


class TestGenerateRecommendations:
    def test_high_pending_tasks(self):
        result = _generate_recommendations(pending_tasks=15, avg_trust=0.9, active_rules=30)
        assert "backlog reduction" in result

    def test_low_trust(self):
        result = _generate_recommendations(pending_tasks=5, avg_trust=0.5, active_rules=30)
        assert "trust scores" in result

    def test_low_active_rules(self):
        result = _generate_recommendations(pending_tasks=5, avg_trust=0.9, active_rules=10)
        assert "governance rules" in result

    def test_all_good(self):
        result = _generate_recommendations(pending_tasks=5, avg_trust=0.9, active_rules=30)
        assert "normal parameters" in result

    def test_multiple_issues(self):
        result = _generate_recommendations(pending_tasks=15, avg_trust=0.5, active_rules=10)
        assert "backlog" in result
        assert "trust" in result
        assert "rules" in result


class TestGenerateObjectives:
    def test_with_pending(self):
        result = _generate_objectives(pending_tasks=5, completed_tasks=2)
        assert "priority tasks" in result
        assert "DSP cycle" in result

    def test_no_pending(self):
        result = _generate_objectives(pending_tasks=0, completed_tasks=2)
        assert "DSP cycle" in result

    def test_many_completed(self):
        result = _generate_objectives(pending_tasks=2, completed_tasks=10)
        assert "Archive" in result

    def test_few_completed(self):
        result = _generate_objectives(pending_tasks=2, completed_tasks=3)
        assert "Archive" not in result

    def test_caps_at_3(self):
        result = _generate_objectives(pending_tasks=100, completed_tasks=0)
        assert "top 3" in result


class TestGenerateExecutiveReport:
    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_empty_stores(self, mock_client):
        mock_client.return_value = None
        result = _generate_executive_report()
        assert result.report_id.startswith("EXEC-")
        assert len(result.sections) == 7
        assert result.overall_status in ("healthy", "warning", "critical")

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {
        "a1": {"status": "ACTIVE", "trust_score": 0.9, "tasks_executed": 5},
    })
    @patch("governance.routes.reports._sessions_store", {
        "s1": {"status": "ACTIVE"},
    })
    @patch("governance.routes.reports._tasks_store", {
        "t1": {"status": "DONE"},
        "t2": {"status": "TODO"},
    })
    def test_with_data(self, mock_client):
        mock_client.return_value = None
        result = _generate_executive_report()
        assert result.metrics_summary["tasks_total"] == 2
        assert result.metrics_summary["tasks_completed"] == 1
        assert result.metrics_summary["tasks_pending"] == 1
        assert result.metrics_summary["sessions_total"] == 1

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_with_session_id(self, mock_client):
        mock_client.return_value = None
        result = _generate_executive_report(session_id="SESSION-2026-01-01-TEST")
        assert result.session_id == "SESSION-2026-01-01-TEST"
        assert "SESSION-2026-01-01-TEST" in result.period

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_with_date_range(self, mock_client):
        mock_client.return_value = None
        result = _generate_executive_report(start_date="2026-01-01", end_date="2026-01-31")
        assert "2026-01-01" in result.period
        assert "2026-01-31" in result.period

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {
        "a1": {"status": "ACTIVE", "trust_score": 0.9, "tasks_executed": 5},
    })
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {
        "t1": {"status": "DONE"},
        "t2": {"status": "DONE"},
    })
    def test_healthy_status(self, mock_client):
        mock_client.return_value = None
        result = _generate_executive_report()
        assert result.overall_status == "healthy"

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {
        "a1": {"status": "ACTIVE", "trust_score": 0.3, "tasks_executed": 0},
    })
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {
        "t1": {"status": "TODO"},
        "t2": {"status": "TODO"},
    })
    def test_critical_status(self, mock_client):
        mock_client.return_value = None
        result = _generate_executive_report()
        assert result.overall_status == "critical"

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_typedb_rules_counted(self, mock_client):
        client = MagicMock()
        rule = MagicMock()
        rule.status = "ACTIVE"
        client.get_all_rules.return_value = [rule]
        mock_client.return_value = client
        result = _generate_executive_report()
        assert result.metrics_summary["total_rules"] == 1
        assert result.metrics_summary["active_rules"] == 1

    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    def test_typedb_error_handled(self, mock_client):
        client = MagicMock()
        client.get_all_rules.side_effect = Exception("db error")
        mock_client.return_value = client
        result = _generate_executive_report()
        assert result.metrics_summary["total_rules"] == 0


class TestGetExecutiveReport:
    @pytest.mark.asyncio
    @patch("governance.routes.reports.get_typedb_client", return_value=None)
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    async def test_default_call(self, _):
        from governance.routes.reports import get_executive_report
        result = await get_executive_report(
            session_id=None, start_date=None, end_date=None
        )
        assert result.report_id.startswith("EXEC-")


class TestGetSessionExecutiveReport:
    @pytest.mark.asyncio
    @patch("governance.routes.reports.get_typedb_client", return_value=None)
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {"S-1": {"status": "ACTIVE"}})
    @patch("governance.routes.reports._tasks_store", {})
    async def test_found_in_store(self, _):
        from governance.routes.reports import get_session_executive_report
        result = await get_session_executive_report("S-1")
        assert result.session_id == "S-1"

    @pytest.mark.asyncio
    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    async def test_not_found(self, mock_client):
        from fastapi import HTTPException
        mock_client.return_value = None
        from governance.routes.reports import get_session_executive_report
        with pytest.raises(HTTPException) as exc_info:
            await get_session_executive_report("NONEXISTENT")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    async def test_found_in_typedb(self, mock_client):
        client = MagicMock()
        client.get_session.return_value = MagicMock()
        mock_client.return_value = client
        from governance.routes.reports import get_session_executive_report
        result = await get_session_executive_report("S-TYPEDB")
        assert result.session_id == "S-TYPEDB"

    @pytest.mark.asyncio
    @patch("governance.routes.reports.get_typedb_client")
    @patch("governance.routes.reports._agents_store", {})
    @patch("governance.routes.reports._sessions_store", {})
    @patch("governance.routes.reports._tasks_store", {})
    async def test_typedb_returns_none(self, mock_client):
        from fastapi import HTTPException
        client = MagicMock()
        client.get_session.return_value = None
        mock_client.return_value = client
        from governance.routes.reports import get_session_executive_report
        with pytest.raises(HTTPException) as exc_info:
            await get_session_executive_report("S-MISSING")
        assert exc_info.value.status_code == 404
