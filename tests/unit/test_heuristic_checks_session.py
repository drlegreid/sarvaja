"""
Unit tests for Heuristic Checks: Session Evidence Domain.

Per DOC-SIZE-01-v1: Tests for governance/routes/tests/heuristic_checks_session.py.
Tests: _api_get, _get_completed_sessions, _is_backfilled_session,
       check_session_evidence_files, check_session_stale_active,
       check_session_tool_calls, check_session_thoughts,
       SESSION_EVIDENCE_CHECKS registry.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from governance.routes.tests.heuristic_checks_session import (
    _api_get,
    _get_completed_sessions,
    _is_backfilled_session,
    check_session_evidence_files,
    check_session_stale_active,
    check_session_tool_calls,
    check_session_thoughts,
    SESSION_EVIDENCE_CHECKS,
)

_PATCH = "governance.routes.tests.heuristic_checks_session"
API = "http://localhost:8082"


def _mock_get(status=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data
    return resp


# ── _is_backfilled_session ────────────────────────────


class TestIsBackfilledSession:
    def test_backfill_in_description(self):
        assert _is_backfilled_session({"description": "Backfilled from evidence"}) is True

    def test_stale_in_description(self):
        assert _is_backfilled_session({"description": "stale session"}) is True

    def test_agent_test_suffix(self):
        assert _is_backfilled_session({"agent_id": "code-test"}) is True

    def test_agent_1(self):
        assert _is_backfilled_session({"agent_id": "agent-1"}) is True

    def test_chat_test_pattern(self):
        assert _is_backfilled_session(
            {"session_id": "SESSION-2026-02-11-CHAT-TEST", "agent_id": ""}) is True

    def test_chat_with_test_description(self):
        assert _is_backfilled_session(
            {"session_id": "SESSION-2026-02-11-CHAT-X",
             "agent_id": "", "description": "test session"}) is True

    def test_real_session(self):
        assert _is_backfilled_session(
            {"session_id": "SESSION-2026-02-11-BUGFIX",
             "agent_id": "code-agent", "description": "Fix bug"}) is False

    def test_no_agent_old_session(self):
        assert _is_backfilled_session(
            {"session_id": "SESSION-2025-12-01-OLD", "agent_id": ""}) is True

    def test_no_agent_recent_session(self):
        assert _is_backfilled_session(
            {"session_id": "SESSION-2026-02-11-RECENT", "agent_id": ""}) is False


# ── _api_get ──────────────────────────────────────────


class TestApiGet:
    @patch("httpx.get", return_value=_mock_get(200, [{"id": 1}]))
    def test_success_list(self, mock):
        result = _api_get(API, "/api/sessions")
        assert result == [{"id": 1}]

    @patch("httpx.get", return_value=_mock_get(200, {"items": [{"id": 1}]}))
    def test_success_dict_with_items(self, mock):
        result = _api_get(API, "/api/sessions")
        assert result == [{"id": 1}]

    @patch("httpx.get", return_value=_mock_get(500, None))
    def test_non_200(self, mock):
        result = _api_get(API, "/api/sessions")
        assert result == []

    @patch("httpx.get", side_effect=Exception("timeout"))
    def test_exception(self, mock):
        result = _api_get(API, "/api/sessions")
        assert result == []


# ── _get_completed_sessions ───────────────────────────


class TestGetCompletedSessions:
    @patch(f"{_PATCH}._api_get")
    def test_filters_completed(self, mock_api):
        mock_api.return_value = [
            {"session_id": "S-1", "status": "COMPLETED"},
            {"session_id": "S-2", "status": "ACTIVE"},
            {"session_id": "S-3", "end_time": "2026-02-11T10:00:00"},
        ]
        result = _get_completed_sessions(API)
        assert len(result) == 2

    @patch(f"{_PATCH}._api_get", return_value=[])
    def test_empty(self, mock_api):
        assert _get_completed_sessions(API) == []


# ── check_session_evidence_files ──────────────────────


class TestCheckSessionEvidenceFiles:
    @patch(f"{_PATCH}._get_completed_sessions", return_value=[])
    def test_skip_when_no_completed(self, mock):
        result = check_session_evidence_files(API)
        assert result["status"] == "SKIP"

    @patch(f"{_PATCH}._api_get")
    @patch(f"{_PATCH}._get_completed_sessions")
    def test_pass_with_evidence(self, mock_completed, mock_api):
        mock_completed.return_value = [
            {"session_id": "S-1", "agent_id": "code-agent",
             "file_path": "/evidence/S-1.md", "session_id": "SESSION-2026-02-11-WORK",
             "description": "real work"}
        ]
        result = check_session_evidence_files(API)
        assert result["status"] == "PASS"

    @patch(f"{_PATCH}._api_get", return_value=[])
    @patch(f"{_PATCH}._get_completed_sessions")
    def test_fail_without_evidence(self, mock_completed, mock_api):
        mock_completed.return_value = [
            {"session_id": "SESSION-2026-02-11-WORK", "agent_id": "code-agent",
             "description": "real work"}
        ]
        result = check_session_evidence_files(API)
        assert result["status"] == "FAIL"
        assert len(result["violations"]) == 1

    @patch(f"{_PATCH}._get_completed_sessions")
    def test_skip_all_backfilled(self, mock_completed):
        mock_completed.return_value = [
            {"session_id": "S-1", "agent_id": "agent-1", "description": "test"}
        ]
        result = check_session_evidence_files(API)
        assert result["status"] == "SKIP"


# ── check_session_stale_active ────────────────────────


class TestCheckSessionStaleActive:
    @patch(f"{_PATCH}._api_get", return_value=[])
    def test_pass_no_active(self, mock_api):
        result = check_session_stale_active(API)
        assert result["status"] == "PASS"

    @patch(f"{_PATCH}._api_get")
    def test_pass_recent_active(self, mock_api):
        recent_time = datetime.now(timezone.utc).isoformat()
        mock_api.return_value = [
            {"session_id": "S-1", "status": "ACTIVE", "start_time": recent_time}
        ]
        result = check_session_stale_active(API)
        assert result["status"] == "PASS"

    @patch(f"{_PATCH}._api_get")
    def test_fail_stale_active(self, mock_api):
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        mock_api.return_value = [
            {"session_id": "S-1", "status": "ACTIVE", "start_time": old_time}
        ]
        result = check_session_stale_active(API)
        assert result["status"] == "FAIL"
        assert "S-1" in result["violations"]


# ── check_session_tool_calls ──────────────────────────


class TestCheckSessionToolCalls:
    @patch(f"{_PATCH}._get_completed_sessions", return_value=[])
    def test_skip_when_no_completed(self, mock):
        result = check_session_tool_calls(API)
        assert result["status"] == "SKIP"

    @patch(f"{_PATCH}._api_get")
    @patch(f"{_PATCH}._get_completed_sessions")
    def test_pass_with_tool_calls(self, mock_completed, mock_api):
        mock_completed.return_value = [
            {"session_id": "SESSION-2026-02-11-WORK", "agent_id": "code-agent",
             "description": "real work"}
        ]
        mock_api.return_value = {"tool_call_count": 5}
        result = check_session_tool_calls(API)
        assert result["status"] == "PASS"

    @patch(f"{_PATCH}._api_get", return_value={"tool_call_count": 0})
    @patch(f"{_PATCH}._get_completed_sessions")
    def test_fail_no_tool_calls(self, mock_completed, mock_api):
        mock_completed.return_value = [
            {"session_id": "SESSION-2026-02-11-WORK", "agent_id": "code-agent",
             "description": "real work"}
        ]
        result = check_session_tool_calls(API)
        assert result["status"] == "FAIL"


# ── check_session_thoughts ────────────────────────────


class TestCheckSessionThoughts:
    @patch(f"{_PATCH}._get_completed_sessions", return_value=[])
    def test_skip_when_no_completed(self, mock):
        result = check_session_thoughts(API)
        assert result["status"] == "SKIP"

    @patch(f"{_PATCH}._api_get")
    @patch(f"{_PATCH}._get_completed_sessions")
    def test_pass_with_thoughts(self, mock_completed, mock_api):
        mock_completed.return_value = [
            {"session_id": "SESSION-2026-02-11-WORK", "agent_id": "code-agent",
             "description": "real work"}
        ]
        mock_api.return_value = {"thought_count": 3}
        result = check_session_thoughts(API)
        assert result["status"] == "PASS"

    @patch(f"{_PATCH}._api_get", return_value=[])
    @patch(f"{_PATCH}._get_completed_sessions")
    def test_fail_no_thoughts(self, mock_completed, mock_api):
        mock_completed.return_value = [
            {"session_id": "SESSION-2026-02-11-WORK", "agent_id": "code-agent",
             "description": "real work"}
        ]
        result = check_session_thoughts(API)
        assert result["status"] == "FAIL"


# ── SESSION_EVIDENCE_CHECKS registry ─────────────────


class TestRegistry:
    def test_has_four_checks(self):
        assert len(SESSION_EVIDENCE_CHECKS) == 4

    def test_all_have_required_fields(self):
        for check in SESSION_EVIDENCE_CHECKS:
            assert "id" in check
            assert "domain" in check
            assert "name" in check
            assert "check_fn" in check
            assert callable(check["check_fn"])

    def test_ids(self):
        ids = [c["id"] for c in SESSION_EVIDENCE_CHECKS]
        assert "H-SESSION-002" in ids
        assert "H-SESSION-003" in ids
        assert "H-SESSION-005" in ids
        assert "H-SESSION-006" in ids

    def test_all_session_domain(self):
        for check in SESSION_EVIDENCE_CHECKS:
            assert check["domain"] == "SESSION"
