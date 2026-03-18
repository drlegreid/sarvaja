"""
Unit tests for CC Session & Project heuristic checks.

Per SESSION-CC-01-v1, GOV-PROJECT-01-v1.
"""
import pytest
from unittest.mock import patch, MagicMock

from governance.routes.tests.heuristic_checks_cc import (
    check_cc_session_uuid,
    check_cc_session_project_link,
    check_project_has_content,
    check_cc_ingestion_complete,
    check_cc_session_tool_pairing,
    check_cc_session_mcp_metadata,
    CC_PROJECT_CHECKS,
)


class TestCheckCCSessionUUID:
    """H-SESSION-CC-001: CC sessions must have cc_session_uuid."""

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_sessions_skips(self, mock_get):
        mock_get.return_value = []
        result = check_cc_session_uuid("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_cc_sessions_skips(self, mock_get):
        mock_get.return_value = [
            {"session_id": "SESSION-2026-02-11-CHAT-TEST", "status": "COMPLETED"},
        ]
        result = check_cc_session_uuid("http://test:8082")
        assert result["status"] == "SKIP"
        assert "No CC-ingested" in result["message"]

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_cc_session_with_uuid_passes(self, mock_get):
        mock_get.return_value = [
            {
                "session_id": "SESSION-2026-02-11-CC-MY-SESSION",
                "cc_session_uuid": "uuid-abc-123",
                "status": "COMPLETED",
            },
        ]
        result = check_cc_session_uuid("http://test:8082")
        assert result["status"] == "PASS"
        assert result["violations"] == []

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_cc_session_without_uuid_fails(self, mock_get):
        mock_get.return_value = [
            {
                "session_id": "SESSION-2026-02-11-CC-MISSING-UUID",
                "status": "COMPLETED",
            },
        ]
        result = check_cc_session_uuid("http://test:8082")
        assert result["status"] == "FAIL"
        assert "SESSION-2026-02-11-CC-MISSING-UUID" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_mixed_sessions(self, mock_get):
        mock_get.return_value = [
            {"session_id": "SESSION-2026-02-11-CC-GOOD", "cc_session_uuid": "uuid-1"},
            {"session_id": "SESSION-2026-02-11-CC-BAD"},
            {"session_id": "SESSION-2026-02-11-CHAT-NOT-CC"},
        ]
        result = check_cc_session_uuid("http://test:8082")
        assert result["status"] == "FAIL"
        assert len(result["violations"]) == 1
        assert "1/2" in result["message"]


class TestCheckCCSessionProjectLink:
    """H-SESSION-CC-002: CC sessions should be linked to a project."""

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_sessions_skips(self, mock_get):
        mock_get.return_value = []
        result = check_cc_session_project_link("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_cc_session_with_slug_passes(self, mock_get):
        mock_get.return_value = [
            {
                "session_id": "SESSION-2026-02-11-CC-MY-SESSION",
                "cc_project_slug": "sarvaja-platform",
            },
        ]
        result = check_cc_session_project_link("http://test:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_cc_session_without_slug_fails(self, mock_get):
        mock_get.return_value = [
            {"session_id": "SESSION-2026-02-11-CC-ORPHAN"},
        ]
        result = check_cc_session_project_link("http://test:8082")
        assert result["status"] == "FAIL"
        assert len(result["violations"]) == 1

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_non_cc_sessions_ignored(self, mock_get):
        mock_get.return_value = [
            {"session_id": "SESSION-2026-02-11-CHAT-HELLO"},
            {"session_id": "SESSION-2026-02-11-MCP-AUTO-abc"},
        ]
        result = check_cc_session_project_link("http://test:8082")
        assert result["status"] == "SKIP"


class TestCheckProjectHasContent:
    """H-PROJECT-001: Projects should have sessions or plans."""

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_projects_skips(self, mock_get):
        mock_get.return_value = []
        result = check_project_has_content("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_project_with_sessions_passes(self, mock_get):
        mock_get.return_value = [
            {"project_id": "PROJ-1", "session_count": 5, "plan_count": 0},
        ]
        result = check_project_has_content("http://test:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_project_with_plans_passes(self, mock_get):
        mock_get.return_value = [
            {"project_id": "PROJ-1", "session_count": 0, "plan_count": 2},
        ]
        result = check_project_has_content("http://test:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_empty_project_fails(self, mock_get):
        mock_get.return_value = [
            {"project_id": "PROJ-EMPTY", "session_count": 0, "plan_count": 0},
        ]
        result = check_project_has_content("http://test:8082")
        assert result["status"] == "FAIL"
        assert "PROJ-EMPTY" in result["violations"]

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_mixed_projects(self, mock_get):
        mock_get.return_value = [
            {"project_id": "PROJ-OK", "session_count": 3, "plan_count": 1},
            {"project_id": "PROJ-EMPTY", "session_count": 0, "plan_count": 0},
            {"project_id": "PROJ-PLANS", "session_count": 0, "plan_count": 1},
        ]
        result = check_project_has_content("http://test:8082")
        assert result["status"] == "FAIL"
        assert len(result["violations"]) == 1
        assert "1/3" in result["message"]


class TestCheckCCIngestionComplete:
    """H-INGESTION-001: CC sessions should have completed ingestion."""

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_sessions_skips(self, mock_get):
        mock_get.return_value = []
        result = check_cc_ingestion_complete("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_cc_sessions_skips(self, mock_get):
        mock_get.return_value = [
            {"session_id": "SESSION-2026-02-13-CHAT-HELLO"},
        ]
        result = check_cc_ingestion_complete("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_ingested_session_passes(self, mock_get):
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint:
                return [{"session_id": "SESSION-2026-02-13-CC-WORK"}]
            if "/api/ingestion/status/" in endpoint:
                return {"status": "complete", "chunks_indexed": 42, "links_created": 5}
            return []
        mock_get.side_effect = side_effect
        result = check_cc_ingestion_complete("http://test:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_not_ingested_session_fails(self, mock_get):
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint:
                return [{"session_id": "SESSION-2026-02-13-CC-WORK"}]
            if "/api/ingestion/status/" in endpoint:
                return {"status": "not_started"}
            return []
        mock_get.side_effect = side_effect
        result = check_cc_ingestion_complete("http://test:8082")
        assert result["status"] == "FAIL"
        assert "not ingested" in result["violations"][0]

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_partial_ingestion_fails(self, mock_get):
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint:
                return [{"session_id": "SESSION-2026-02-13-CC-PARTIAL"}]
            if "/api/ingestion/status/" in endpoint:
                return {"status": "content", "chunks_indexed": 10, "links_created": 0}
            return []
        mock_get.side_effect = side_effect
        result = check_cc_ingestion_complete("http://test:8082")
        assert result["status"] == "FAIL"
        assert "phase=content" in result["violations"][0]


class TestCCProjectChecksRegistry:
    """Verify registry structure."""

    def test_registry_has_6_checks(self):
        assert len(CC_PROJECT_CHECKS) == 6

    def test_check_ids(self):
        ids = [c["id"] for c in CC_PROJECT_CHECKS]
        assert "H-SESSION-CC-001" in ids
        assert "H-SESSION-CC-002" in ids
        assert "H-SESSION-CC-003" in ids
        assert "H-SESSION-CC-004" in ids
        assert "H-PROJECT-001" in ids
        assert "H-INGESTION-001" in ids

    def test_all_checks_callable(self):
        for check in CC_PROJECT_CHECKS:
            assert callable(check["check_fn"])

    def test_domains(self):
        domains = {c["id"]: c["domain"] for c in CC_PROJECT_CHECKS}
        assert domains["H-SESSION-CC-001"] == "SESSION"
        assert domains["H-SESSION-CC-002"] == "SESSION"
        assert domains["H-PROJECT-001"] == "PROJECT"
