"""Tests for session content validation API endpoint.

TDD-first: Validates the /sessions/{id}/validate endpoint that runs
deep content integrity checks against real CC session JSONL data.

Per TEST-E2E-01-v1: Tier 1 unit tests for validation API.
"""

from unittest.mock import patch, MagicMock
import pytest

from governance.services.session_content_validator import (
    ContentValidationResult,
    ValidationIssue,
)


class TestValidationEndpoint:
    """Tests for GET /sessions/{session_id}/validate."""

    @patch("governance.routes.sessions.validation.find_jsonl_for_session")
    @patch("governance.routes.sessions.validation.validate_session_content")
    def test_valid_session_returns_200(self, mock_validate, mock_find):
        from governance.routes.sessions.validation import validate_session
        mock_find.return_value = "/tmp/test.jsonl"
        mock_validate.return_value = ContentValidationResult(
            valid=True, entry_count=100, tool_calls_total=20, tool_results_total=20,
        )
        result = validate_session("SESSION-2026-02-20-CC-TEST")
        assert result["valid"] is True
        assert result["entry_count"] == 100

    @patch("governance.routes.sessions.validation.find_jsonl_for_session")
    def test_no_jsonl_returns_404(self, mock_find):
        from fastapi import HTTPException
        from governance.routes.sessions.validation import validate_session
        mock_find.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            validate_session("SESSION-2026-02-20-CC-MISSING")
        assert exc_info.value.status_code == 404

    @patch("governance.routes.sessions.validation.find_jsonl_for_session")
    @patch("governance.routes.sessions.validation.validate_session_content")
    def test_validation_issues_included(self, mock_validate, mock_find):
        from governance.routes.sessions.validation import validate_session
        mock_find.return_value = "/tmp/test.jsonl"
        mock_validate.return_value = ContentValidationResult(
            valid=True, entry_count=50, orphaned_tool_calls=2,
            issues=[
                ValidationIssue(check="tool_call_result_pairing", severity="warning",
                                message="Tool call t1 has no result"),
                ValidationIssue(check="tool_call_result_pairing", severity="warning",
                                message="Tool call t2 has no result"),
            ],
        )
        result = validate_session("SESSION-2026-02-20-CC-TEST")
        assert len(result["issues"]) == 2
        assert result["orphaned_tool_calls"] == 2

    @patch("governance.routes.sessions.validation.find_jsonl_for_session")
    @patch("governance.routes.sessions.validation.validate_session_content")
    def test_mcp_distribution_included(self, mock_validate, mock_find):
        from governance.routes.sessions.validation import validate_session
        mock_find.return_value = "/tmp/test.jsonl"
        mock_validate.return_value = ContentValidationResult(
            valid=True, entry_count=50,
            mcp_calls_total=5, mcp_calls_with_server=4, mcp_calls_without_server=1,
            mcp_server_distribution={"gov-core": 3, "gov-tasks": 1},
        )
        result = validate_session("SESSION-2026-02-20-CC-TEST")
        assert result["mcp_server_distribution"] == {"gov-core": 3, "gov-tasks": 1}


class TestHeuristicCheckCCToolPairing:
    """H-SESSION-CC-003: CC sessions should have matched tool call/result pairs."""

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_sessions_skips(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_tool_pairing
        mock_get.return_value = []
        result = check_cc_session_tool_pairing("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_cc_sessions_skips(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_tool_pairing
        mock_get.return_value = [
            {"session_id": "SESSION-2026-02-11-CHAT-HELLO"},
        ]
        result = check_cc_session_tool_pairing("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_all_paired_passes(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_tool_pairing
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint and "validate" not in endpoint:
                return [{"session_id": "SESSION-2026-02-20-CC-GOOD"}]
            if "/validate" in endpoint:
                return {
                    "valid": True,
                    "orphaned_tool_calls": 0,
                    "orphaned_tool_results": 0,
                    "tool_calls_total": 15,
                    "tool_results_total": 15,
                }
            return []
        mock_get.side_effect = side_effect
        result = check_cc_session_tool_pairing("http://test:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_orphaned_calls_fails(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_tool_pairing
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint and "validate" not in endpoint:
                return [{"session_id": "SESSION-2026-02-20-CC-BAD"}]
            if "/validate" in endpoint:
                return {
                    "valid": True,
                    "orphaned_tool_calls": 3,
                    "orphaned_tool_results": 0,
                    "tool_calls_total": 20,
                    "tool_results_total": 17,
                }
            return []
        mock_get.side_effect = side_effect
        result = check_cc_session_tool_pairing("http://test:8082")
        assert result["status"] == "FAIL"
        assert "SESSION-2026-02-20-CC-BAD" in result["violations"][0]

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_validation_api_unreachable_skips(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_tool_pairing
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint and "validate" not in endpoint:
                return [{"session_id": "SESSION-2026-02-20-CC-TEST"}]
            if "/validate" in endpoint:
                return []  # API call failed
            return []
        mock_get.side_effect = side_effect
        result = check_cc_session_tool_pairing("http://test:8082")
        assert result["status"] == "SKIP"


class TestHeuristicCheckCCMCPMetadata:
    """H-SESSION-CC-004: CC sessions MCP calls should have server metadata."""

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_sessions_skips(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_mcp_metadata
        mock_get.return_value = []
        result = check_cc_session_mcp_metadata("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_all_mcp_with_server_passes(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_mcp_metadata
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint and "validate" not in endpoint:
                return [{"session_id": "SESSION-2026-02-20-CC-GOOD"}]
            if "/validate" in endpoint:
                return {
                    "valid": True,
                    "mcp_calls_total": 10,
                    "mcp_calls_with_server": 10,
                    "mcp_calls_without_server": 0,
                    "mcp_server_distribution": {"gov-core": 5, "gov-tasks": 5},
                }
            return []
        mock_get.side_effect = side_effect
        result = check_cc_session_mcp_metadata("http://test:8082")
        assert result["status"] == "PASS"

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_missing_server_metadata_fails(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_mcp_metadata
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint and "validate" not in endpoint:
                return [{"session_id": "SESSION-2026-02-20-CC-NOMETA"}]
            if "/validate" in endpoint:
                return {
                    "valid": True,
                    "mcp_calls_total": 8,
                    "mcp_calls_with_server": 5,
                    "mcp_calls_without_server": 3,
                }
            return []
        mock_get.side_effect = side_effect
        result = check_cc_session_mcp_metadata("http://test:8082")
        assert result["status"] == "FAIL"
        assert "SESSION-2026-02-20-CC-NOMETA" in result["violations"][0]

    @patch("governance.routes.tests.heuristic_checks_cc._api_get")
    def test_no_mcp_calls_passes(self, mock_get):
        from governance.routes.tests.heuristic_checks_cc import check_cc_session_mcp_metadata
        def side_effect(url, endpoint):
            if "/api/sessions" in endpoint and "validate" not in endpoint:
                return [{"session_id": "SESSION-2026-02-20-CC-NOMCP"}]
            if "/validate" in endpoint:
                return {
                    "valid": True,
                    "mcp_calls_total": 0,
                    "mcp_calls_with_server": 0,
                    "mcp_calls_without_server": 0,
                }
            return []
        mock_get.side_effect = side_effect
        result = check_cc_session_mcp_metadata("http://test:8082")
        assert result["status"] == "PASS"


class TestRegistryUpdated:
    """Verify registry includes new checks."""

    def test_registry_has_6_checks(self):
        from governance.routes.tests.heuristic_checks_cc import CC_PROJECT_CHECKS
        assert len(CC_PROJECT_CHECKS) == 6

    def test_new_check_ids_present(self):
        from governance.routes.tests.heuristic_checks_cc import CC_PROJECT_CHECKS
        ids = [c["id"] for c in CC_PROJECT_CHECKS]
        assert "H-SESSION-CC-003" in ids
        assert "H-SESSION-CC-004" in ids

    def test_new_checks_callable(self):
        from governance.routes.tests.heuristic_checks_cc import CC_PROJECT_CHECKS
        for c in CC_PROJECT_CHECKS:
            if c["id"] in ("H-SESSION-CC-003", "H-SESSION-CC-004"):
                assert callable(c["check_fn"])
