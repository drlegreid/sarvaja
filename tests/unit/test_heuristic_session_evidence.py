"""
Tests for session evidence heuristic checks.

Per D.4: Validates session evidence integrity checks.
Verifies H-SESSION-002, H-SESSION-003, H-SESSION-005, H-SESSION-006.

Created: 2026-02-01
"""
from unittest.mock import patch, MagicMock

import httpx
import pytest


# ===== H-SESSION-002: Evidence files =====


class TestSessionEvidenceFiles:
    """H-SESSION-002: Ended sessions must have evidence files."""

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_pass_when_sessions_have_evidence(self, mock_get):
        """Sessions with file_path or evidence_files should pass."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"session_id": "S-001", "status": "COMPLETED", "file_path": "evidence/S-001.md",
                 "evidence_files": [], "end_time": "2026-01-01T00:00:00", "agent_id": "code-agent"},
                {"session_id": "S-002", "status": "COMPLETED", "file_path": None,
                 "evidence_files": ["ev1.md"], "end_time": "2026-01-01T00:00:00", "agent_id": "code-agent"},
            ],
        )
        from governance.routes.tests.heuristic_checks_session import check_session_evidence_files
        result = check_session_evidence_files("http://localhost:8082")
        assert result["status"] == "PASS"
        assert len(result["violations"]) == 0

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_fail_when_sessions_lack_evidence(self, mock_get):
        """Sessions without file_path or evidence should fail."""
        def side_effect(url, **kwargs):
            resp = MagicMock(status_code=200)
            if "/evidence" in url:
                resp.json = lambda: {"evidence_count": 0, "evidence_files": []}
            else:
                resp.json = lambda: [
                    {"session_id": "S-001", "status": "COMPLETED", "file_path": None,
                     "evidence_files": None, "end_time": "2026-01-01T00:00:00", "agent_id": "code-agent"},
                ]
            return resp

        mock_get.side_effect = side_effect
        from governance.routes.tests.heuristic_checks_session import check_session_evidence_files
        result = check_session_evidence_files("http://localhost:8082")
        assert result["status"] == "FAIL"
        assert "S-001" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_skip_when_no_completed_sessions(self, mock_get):
        """Should SKIP when no completed sessions exist."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"session_id": "S-001", "status": "ACTIVE"}],
        )
        from governance.routes.tests.heuristic_checks_session import check_session_evidence_files
        result = check_session_evidence_files("http://localhost:8082")
        assert result["status"] == "SKIP"


# ===== H-SESSION-003: Stale active sessions =====


class TestStaleActiveSessions:
    """H-SESSION-003: Sessions >24h should not be ACTIVE."""

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_pass_when_active_sessions_are_recent(self, mock_get):
        """Active sessions started within 24h should pass."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"session_id": "S-001", "status": "ACTIVE", "start_time": now}],
        )
        from governance.routes.tests.heuristic_checks_session import check_session_stale_active
        result = check_session_stale_active("http://localhost:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_fail_when_session_stale(self, mock_get):
        """Active sessions older than 24h should fail."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"session_id": "S-OLD", "status": "ACTIVE", "start_time": "2025-01-01T00:00:00"},
            ],
        )
        from governance.routes.tests.heuristic_checks_session import check_session_stale_active
        result = check_session_stale_active("http://localhost:8082")
        assert result["status"] == "FAIL"
        assert "S-OLD" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_pass_when_no_active_sessions(self, mock_get):
        """No active sessions should pass."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"session_id": "S-001", "status": "COMPLETED"}],
        )
        from governance.routes.tests.heuristic_checks_session import check_session_stale_active
        result = check_session_stale_active("http://localhost:8082")
        assert result["status"] == "PASS"


# ===== H-SESSION-005: Tool call records =====


class TestSessionToolCalls:
    """H-SESSION-005: Ended sessions should have MCP tool call records."""

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_pass_when_sessions_have_tool_calls(self, mock_get):
        """Sessions with tool_call records should pass."""
        def side_effect(url, **kwargs):
            resp = MagicMock(status_code=200)
            if "/tool_calls" in url:
                resp.json = lambda: {"tool_call_count": 5, "tool_calls": [{"tool": "x"}] * 5}
            else:
                resp.json = lambda: [
                    {"session_id": "S-001", "status": "COMPLETED", "end_time": "2026-01-01T00:00:00", "agent_id": "test-agent"},
                ]
            return resp

        mock_get.side_effect = side_effect
        from governance.routes.tests.heuristic_checks_session import check_session_tool_calls
        result = check_session_tool_calls("http://localhost:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_fail_when_sessions_lack_tool_calls(self, mock_get):
        """Sessions without tool_call records should fail."""
        def side_effect(url, **kwargs):
            resp = MagicMock(status_code=200)
            if "/tool_calls" in url:
                resp.json = lambda: {"tool_call_count": 0, "tool_calls": []}
            else:
                resp.json = lambda: [
                    {"session_id": "S-001", "status": "COMPLETED", "end_time": "2026-01-01T00:00:00", "agent_id": "test-agent"},
                ]
            return resp

        mock_get.side_effect = side_effect
        from governance.routes.tests.heuristic_checks_session import check_session_tool_calls
        result = check_session_tool_calls("http://localhost:8082")
        assert result["status"] == "FAIL"
        assert "S-001" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_skip_when_no_completed_sessions(self, mock_get):
        """Should SKIP when no completed sessions exist."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [],
        )
        from governance.routes.tests.heuristic_checks_session import check_session_tool_calls
        result = check_session_tool_calls("http://localhost:8082")
        assert result["status"] == "SKIP"


# ===== H-SESSION-006: Thought records =====


class TestSessionThoughts:
    """H-SESSION-006: Ended sessions should have thought/reasoning records."""

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_pass_when_sessions_have_thoughts(self, mock_get):
        """Sessions with thought records should pass."""
        def side_effect(url, **kwargs):
            resp = MagicMock(status_code=200)
            if "/thoughts" in url:
                resp.json = lambda: {"thought_count": 3, "thoughts": [{"t": "x"}] * 3}
            else:
                resp.json = lambda: [
                    {"session_id": "S-001", "status": "COMPLETED", "end_time": "2026-01-01T00:00:00", "agent_id": "test-agent"},
                ]
            return resp

        mock_get.side_effect = side_effect
        from governance.routes.tests.heuristic_checks_session import check_session_thoughts
        result = check_session_thoughts("http://localhost:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_session.httpx.get")
    def test_fail_when_sessions_lack_thoughts(self, mock_get):
        """Sessions without thought records should fail."""
        def side_effect(url, **kwargs):
            resp = MagicMock(status_code=200)
            if "/thoughts" in url:
                resp.json = lambda: {"thought_count": 0, "thoughts": []}
            else:
                resp.json = lambda: [
                    {"session_id": "S-001", "status": "COMPLETED", "end_time": "2026-01-01T00:00:00", "agent_id": "test-agent"},
                ]
            return resp

        mock_get.side_effect = side_effect
        from governance.routes.tests.heuristic_checks_session import check_session_thoughts
        result = check_session_thoughts("http://localhost:8082")
        assert result["status"] == "FAIL"
        assert "S-001" in result["violations"]


# ===== Registry integration =====


class TestSessionChecksRegistry:
    """Verify session evidence checks are registered."""

    def test_session_evidence_checks_importable(self):
        """Session evidence checks module should be importable."""
        from governance.routes.tests.heuristic_checks_session import SESSION_EVIDENCE_CHECKS
        assert len(SESSION_EVIDENCE_CHECKS) == 4

    def test_session_checks_in_main_registry(self):
        """Session evidence checks should be in main HEURISTIC_CHECKS."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        ids = [c["id"] for c in HEURISTIC_CHECKS]
        assert "H-SESSION-002" in ids
        assert "H-SESSION-003" in ids
        assert "H-SESSION-005" in ids
        assert "H-SESSION-006" in ids

    def test_total_checks_increased(self):
        """Total checks should now be at least 18 (14 + 4 new)."""
        from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS
        assert len(HEURISTIC_CHECKS) >= 18
