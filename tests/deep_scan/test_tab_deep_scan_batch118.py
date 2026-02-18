"""Deep scan batch 118: Heuristic checks layer.

Batch 118 findings: 9 total, 0 confirmed fixes, 9 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


# ── Backfill detection defense ──────────────


class TestBackfillDetectionDefense:
    """Verify _is_backfilled_session heuristic handles edge cases."""

    def test_cc_session_skipped(self):
        """CC sessions are always treated as backfilled (use JSONL, not MCP)."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session

        assert _is_backfilled_session({"session_id": "SESSION-2026-02-15-CC-abc123"}) is True

    def test_backfill_description_detected(self):
        """Sessions with 'backfill' in description are detected."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session

        assert _is_backfilled_session({
            "session_id": "SESSION-2026-02-15-X",
            "description": "Backfilled from evidence file",
        }) is True

    def test_test_agent_detected(self):
        """Agents ending with -test are detected."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session

        assert _is_backfilled_session({
            "session_id": "SESSION-2026-02-15-X",
            "agent_id": "code-agent-test",
        }) is True

    def test_agent1_placeholder_detected(self):
        """agent-1 placeholder is detected as test artifact."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session

        assert _is_backfilled_session({
            "session_id": "SESSION-2026-02-15-X",
            "agent_id": "agent-1",
        }) is True

    def test_chat_test_pattern_detected(self):
        """CHAT-TEST pattern in session ID is detected."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session

        assert _is_backfilled_session({
            "session_id": "SESSION-2026-02-15-CHAT-TEST-001",
        }) is True

    def test_real_session_not_flagged(self):
        """Real sessions with agent and recent date are NOT flagged."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session

        result = _is_backfilled_session({
            "session_id": "SESSION-2026-02-15-REAL-SESSION",
            "agent_id": "code-agent",
            "description": "Working on feature",
        })
        assert result is False


# ── Evidence check API response defense ──────────────


class TestEvidenceCheckAPIResponseDefense:
    """Verify H-SESSION-002 handles API response shapes correctly."""

    @patch("governance.routes.tests.heuristic_checks_session.httpx")
    def test_skip_when_no_completed(self, mock_httpx):
        """Returns SKIP when no completed sessions."""
        from governance.routes.tests.heuristic_checks_session import check_session_evidence_files

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_httpx.get.return_value = mock_resp

        result = check_session_evidence_files("http://localhost:8082")
        assert result["status"] == "SKIP"

    def test_api_get_extracts_items(self):
        """_api_get extracts 'items' from dict responses."""
        from governance.routes.tests.heuristic_checks_session import _api_get

        with patch("governance.routes.tests.heuristic_checks_session.httpx") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"items": [{"id": "s1"}], "total": 1}
            mock_httpx.get.return_value = mock_resp

            result = _api_get("http://localhost:8082", "/api/sessions")
            assert result == [{"id": "s1"}]

    def test_api_get_returns_list_directly(self):
        """_api_get returns list responses directly."""
        from governance.routes.tests.heuristic_checks_session import _api_get

        with patch("governance.routes.tests.heuristic_checks_session.httpx") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{"id": "s1"}, {"id": "s2"}]
            mock_httpx.get.return_value = mock_resp

            result = _api_get("http://localhost:8082", "/api/sessions")
            assert len(result) == 2


# ── Exploratory check pagination defense ──────────────


class TestExploratoryCheckPaginationDefense:
    """Verify H-EXPLR-001 uses direct httpx for pagination."""

    def test_self_referential_skipped(self):
        """Self-referential API URL returns SKIP."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )

        result = check_chat_session_count_accuracy("http://localhost:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx")
    def test_pagination_extraction(self, mock_httpx):
        """Direct httpx call extracts pagination total."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [],
            "pagination": {"total": 42, "page": 1},
        }
        mock_httpx.get.return_value = mock_resp

        result = check_chat_session_count_accuracy("http://external:9999")
        assert result["status"] == "PASS"


# ── Remediation state defense ──────────────


class TestRemediationStateDefense:
    """Verify remediate_violations handles state correctly."""

    def test_missing_run_returns_error(self):
        """Missing run_id returns error dict."""
        from governance.routes.tests.runner_exec import remediate_violations

        result = remediate_violations("NONEXISTENT-RUN")
        assert "error" in result

    def test_dry_run_does_not_apply(self):
        """dry_run=True counts fixes but does not call remediation."""
        from governance.routes.tests.runner_exec import remediate_violations, _test_results

        _test_results["TEST-RUN-001"] = {
            "checks": [
                {
                    "id": "H-TASK-003",
                    "status": "FAIL",
                    "violations": ["TASK-001"],
                },
            ],
        }
        try:
            result = remediate_violations("TEST-RUN-001", dry_run=True)
            assert result["dry_run"] is True
            assert result["fixes_applied"] == 1
            assert result["details"][0]["action"] == "planned"
        finally:
            _test_results.pop("TEST-RUN-001", None)


# ── Heuristic registry defense ──────────────


class TestHeuristicRegistryDefense:
    """Verify heuristic check registry is complete."""

    def test_all_domains_covered(self):
        """Registry covers TASK, SESSION, RULE, AGENT domains."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS

        domains = {c["domain"] for c in HEURISTIC_CHECKS}
        assert "TASK" in domains
        assert "SESSION" in domains
        assert "RULE" in domains
        assert "AGENT" in domains

    def test_all_checks_have_functions(self):
        """Every registered check has a callable check_fn."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS

        for check in HEURISTIC_CHECKS:
            assert callable(check["check_fn"]), f"{check['id']} missing callable"

    def test_no_duplicate_check_ids(self):
        """No duplicate check IDs in registry."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS

        ids = [c["id"] for c in HEURISTIC_CHECKS]
        assert len(ids) == len(set(ids)), f"Duplicates: {[i for i in ids if ids.count(i) > 1]}"
