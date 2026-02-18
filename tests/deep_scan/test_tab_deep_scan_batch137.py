"""Deep scan batch 137: Heuristic checks + context layer.

Batch 137 findings: 0 confirmed fixes.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


# ── Backfill detection defense ──────────────


class TestBackfillDetectionDefense:
    """Verify _is_backfilled_session handles all cases correctly."""

    def test_cc_session_skipped(self):
        """CC sessions are always skipped (use JSONL, not evidence/MCP)."""
        from governance.routes.tests.heuristic_checks_session import (
            _is_backfilled_session,
        )
        session = {"session_id": "SESSION-2026-02-15-CC-abc123", "agent_id": "code-agent"}
        assert _is_backfilled_session(session) is True

    def test_backfill_description_detected(self):
        """Sessions with 'backfill' in description are detected."""
        from governance.routes.tests.heuristic_checks_session import (
            _is_backfilled_session,
        )
        session = {
            "session_id": "SESSION-2026-02-15-TEST",
            "description": "Backfilled from evidence file",
            "agent_id": "",
        }
        assert _is_backfilled_session(session) is True

    def test_test_agent_detected(self):
        """Agent IDs ending with '-test' are detected."""
        from governance.routes.tests.heuristic_checks_session import (
            _is_backfilled_session,
        )
        session = {"session_id": "SESSION-2026-02-15-X", "agent_id": "code-test"}
        assert _is_backfilled_session(session) is True

    def test_real_session_not_flagged(self):
        """Recent sessions with real agent_id are NOT flagged."""
        from governance.routes.tests.heuristic_checks_session import (
            _is_backfilled_session,
        )
        today = datetime.now().strftime("%Y-%m-%d")
        session = {
            "session_id": f"SESSION-{today}-REAL-WORK",
            "agent_id": "code-agent",
            "description": "Working on feature X",
        }
        assert _is_backfilled_session(session) is False

    def test_dynamic_30_day_cutoff(self):
        """Uses dynamic 30-day window, not hardcoded date."""
        from governance.routes.tests.heuristic_checks_session import (
            _is_backfilled_session,
        )
        # Session from 60 days ago with no agent → backfilled
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        session = {
            "session_id": f"SESSION-{old_date}-OLD",
            "agent_id": "",
            "description": "",
        }
        assert _is_backfilled_session(session) is True

    def test_agent1_test_artifact(self):
        """agent-1 (common test placeholder) is detected."""
        from governance.routes.tests.heuristic_checks_session import (
            _is_backfilled_session,
        )
        session = {
            "session_id": "SESSION-2026-02-15-TEST",
            "agent_id": "agent-1",
        }
        assert _is_backfilled_session(session) is True

    def test_chat_test_patterns(self):
        """CHAT-TEST, CHAT-CVP, etc. patterns are detected."""
        from governance.routes.tests.heuristic_checks_session import (
            _is_backfilled_session,
        )
        for pattern in ["CHAT-TEST", "CHAT-CVP", "CHAT-FALLBACK"]:
            session = {
                "session_id": f"SESSION-2026-02-15-{pattern}",
                "agent_id": "code-agent",
            }
            assert _is_backfilled_session(session) is True, f"Failed for {pattern}"


# ── API response shape defense ──────────────


class TestHeuristicAPIResponseDefense:
    """Verify _api_get handles different response shapes."""

    @patch("governance.routes.tests.heuristic_checks_session.httpx")
    def test_dict_response_extracts_items(self, mock_httpx):
        """Dict response with 'items' key extracts the items list."""
        from governance.routes.tests.heuristic_checks_session import _api_get

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": [{"id": 1}], "total": 1}
        mock_httpx.get.return_value = mock_resp

        result = _api_get("http://localhost:8082", "/api/sessions")
        assert result == [{"id": 1}]

    @patch("governance.routes.tests.heuristic_checks_session.httpx")
    def test_list_response_passed_through(self, mock_httpx):
        """List response is passed through directly."""
        from governance.routes.tests.heuristic_checks_session import _api_get

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"id": 1}, {"id": 2}]
        mock_httpx.get.return_value = mock_resp

        result = _api_get("http://localhost:8082", "/api/tasks")
        assert result == [{"id": 1}, {"id": 2}]

    @patch("governance.routes.tests.heuristic_checks_session.httpx")
    def test_error_returns_empty_list(self, mock_httpx):
        """Connection errors return empty list (not crash)."""
        from governance.routes.tests.heuristic_checks_session import _api_get

        mock_httpx.get.side_effect = ConnectionError("refused")
        result = _api_get("http://localhost:8082", "/api/sessions")
        assert result == []

    @patch("governance.routes.tests.heuristic_checks_session.httpx")
    def test_non_200_returns_empty(self, mock_httpx):
        """Non-200 status returns empty list."""
        from governance.routes.tests.heuristic_checks_session import _api_get

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_httpx.get.return_value = mock_resp

        result = _api_get("http://localhost:8082", "/api/sessions")
        assert result == []


# ── Session evidence check defense ──────────────


class TestSessionEvidenceCheckDefense:
    """Verify H-SESSION-002 evidence file check logic."""

    @patch("governance.routes.tests.heuristic_checks_session._get_completed_sessions")
    def test_no_sessions_returns_skip(self, mock_get):
        """No completed sessions returns SKIP status."""
        from governance.routes.tests.heuristic_checks_session import (
            check_session_evidence_files,
        )
        mock_get.return_value = []
        result = check_session_evidence_files("http://localhost:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_session._api_get")
    @patch("governance.routes.tests.heuristic_checks_session._get_completed_sessions")
    @patch("governance.routes.tests.heuristic_checks_session._is_backfilled_session")
    def test_all_backfilled_returns_skip(self, mock_backfill, mock_get, mock_api):
        """All sessions being backfilled returns SKIP."""
        from governance.routes.tests.heuristic_checks_session import (
            check_session_evidence_files,
        )
        mock_get.return_value = [
            {"session_id": "S1", "status": "COMPLETED"},
            {"session_id": "S2", "status": "COMPLETED"},
        ]
        mock_backfill.return_value = True
        result = check_session_evidence_files("http://localhost:8082")
        assert result["status"] == "SKIP"


# ── Stale active session defense ──────────────


class TestStaleActiveSessionDefense:
    """Verify H-SESSION-003 stale active detection."""

    @patch("governance.routes.tests.heuristic_checks_session._api_get")
    def test_no_active_returns_pass(self, mock_api):
        """No active sessions returns PASS."""
        from governance.routes.tests.heuristic_checks_session import (
            check_session_stale_active,
        )
        mock_api.return_value = [
            {"session_id": "S1", "status": "COMPLETED"},
        ]
        result = check_session_stale_active("http://localhost:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_session._api_get")
    def test_recent_active_passes(self, mock_api):
        """Recently started active session passes."""
        from governance.routes.tests.heuristic_checks_session import (
            check_session_stale_active,
        )
        now_str = datetime.now().isoformat()
        mock_api.return_value = [
            {"session_id": "S1", "status": "ACTIVE", "start_time": now_str},
        ]
        result = check_session_stale_active("http://localhost:8082")
        assert result["status"] == "PASS"


# ── Check registry defense ──────────────


class TestSessionCheckRegistryDefense:
    """Verify session check registry is complete."""

    def test_registry_has_4_checks(self):
        """SESSION_EVIDENCE_CHECKS registry has 4 entries."""
        from governance.routes.tests.heuristic_checks_session import (
            SESSION_EVIDENCE_CHECKS,
        )
        assert len(SESSION_EVIDENCE_CHECKS) == 4

    def test_each_check_has_required_keys(self):
        """Each registry entry has id, domain, name, check_fn."""
        from governance.routes.tests.heuristic_checks_session import (
            SESSION_EVIDENCE_CHECKS,
        )
        for check in SESSION_EVIDENCE_CHECKS:
            assert "id" in check
            assert "domain" in check
            assert "name" in check
            assert "check_fn" in check
            assert callable(check["check_fn"])

    def test_check_ids_are_h_session(self):
        """All check IDs start with H-SESSION-."""
        from governance.routes.tests.heuristic_checks_session import (
            SESSION_EVIDENCE_CHECKS,
        )
        for check in SESSION_EVIDENCE_CHECKS:
            assert check["id"].startswith("H-SESSION-"), f"Bad ID: {check['id']}"
