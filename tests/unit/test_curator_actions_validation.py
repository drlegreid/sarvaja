"""
Unit tests for Rules Curator Validation & Proposal Actions.

Per DOC-SIZE-01-v1: Tests for agent/orchestrator/curator_actions_validation.py.
Tests: CuratorValidationMixin — check_dependencies, validate_rule, propose_change;
       _check_field helper.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.orchestrator.curator_actions_validation import (
    CuratorValidationMixin,
    _check_field,
)
from agent.orchestrator.curator_models import (
    CurationAction,
    CurationResult,
    IssueSeverity,
    RuleIssue,
)


class _TestCurator(CuratorValidationMixin):
    """Concrete class for testing the mixin."""

    def __init__(self, mcp_client=None, api_base="http://localhost:8082"):
        self._mcp_client = mcp_client
        self._api_base = api_base
        self._issues = []


# ── _check_field ──────────────────────────────────────────────


class TestCheckField:
    def test_missing_field_appends_issue(self):
        issues = []
        _check_field(issues, {}, "R-1", "name", IssueSeverity.HIGH)
        assert len(issues) == 1
        assert issues[0].rule_id == "R-1"
        assert issues[0].issue_type == "missing_name"
        assert issues[0].severity == IssueSeverity.HIGH

    def test_present_field_no_issue(self):
        issues = []
        _check_field(issues, {"name": "My Rule"}, "R-1", "name", IssueSeverity.HIGH)
        assert len(issues) == 0

    def test_empty_string_treated_as_missing(self):
        issues = []
        _check_field(issues, {"name": ""}, "R-1", "name", IssueSeverity.HIGH)
        assert len(issues) == 1

    def test_custom_recommendation(self):
        issues = []
        _check_field(
            issues, {}, "R-1", "category", IssueSeverity.MEDIUM,
            recommendation="Set a category",
        )
        assert issues[0].recommendation == "Set a category"

    def test_default_recommendation(self):
        issues = []
        _check_field(issues, {}, "R-1", "priority", IssueSeverity.LOW)
        assert "priority" in issues[0].recommendation

    def test_issue_id_increments(self):
        issues = [MagicMock()]  # pre-existing issue
        _check_field(issues, {}, "R-1", "name", IssueSeverity.HIGH)
        assert issues[1].issue_id == "VAL-002"


# ── check_dependencies ───────────────────────────────────────


class TestCheckDependencies:
    @pytest.mark.asyncio
    async def test_no_mcp_client(self):
        curator = _TestCurator(mcp_client=None)
        result = await curator.check_dependencies("R-1")
        assert result.success is True
        assert result.action == CurationAction.CHECK_DEPENDENCIES
        assert len(result.issues_found) == 0

    @pytest.mark.asyncio
    async def test_no_deps_found(self):
        mcp = AsyncMock()
        mcp.call_tool.return_value = []
        curator = _TestCurator(mcp_client=mcp)
        result = await curator.check_dependencies("R-1")
        assert result.success is True
        assert len(result.issues_found) == 0

    @pytest.mark.asyncio
    async def test_deprecated_dep_found(self):
        mcp = AsyncMock()
        mcp.call_tool.side_effect = [
            ["DEP-A"],  # get_dependencies returns one dep
            {"status": "DEPRECATED"},  # get_rule for DEP-A
        ]
        curator = _TestCurator(mcp_client=mcp)
        result = await curator.check_dependencies("R-1")
        assert result.success is True
        assert len(result.issues_found) == 1
        assert result.issues_found[0].issue_type == "deprecated_dependency"
        assert "DEP-A" in result.issues_found[0].description

    @pytest.mark.asyncio
    async def test_active_dep_no_issue(self):
        mcp = AsyncMock()
        mcp.call_tool.side_effect = [
            ["DEP-B"],
            {"status": "ACTIVE"},
        ]
        curator = _TestCurator(mcp_client=mcp)
        result = await curator.check_dependencies("R-1")
        assert len(result.issues_found) == 0

    @pytest.mark.asyncio
    async def test_non_list_deps_result(self):
        mcp = AsyncMock()
        mcp.call_tool.return_value = None  # not a list
        curator = _TestCurator(mcp_client=mcp)
        result = await curator.check_dependencies("R-1")
        assert result.success is True
        assert len(result.issues_found) == 0

    @pytest.mark.asyncio
    async def test_exception_returns_failure(self):
        mcp = AsyncMock()
        mcp.call_tool.side_effect = Exception("MCP error")
        curator = _TestCurator(mcp_client=mcp)
        result = await curator.check_dependencies("R-1")
        assert result.success is False
        assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_issues_added_to_curator_list(self):
        mcp = AsyncMock()
        mcp.call_tool.side_effect = [
            ["DEP-X"],
            {"status": "DEPRECATED"},
        ]
        curator = _TestCurator(mcp_client=mcp)
        await curator.check_dependencies("R-1")
        assert len(curator._issues) == 1


# ── validate_rule ─────────────────────────────────────────────


class TestValidateRule:
    @pytest.mark.asyncio
    async def test_rule_not_found(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            curator = _TestCurator()
            result = await curator.validate_rule("R-MISS")

        assert result.success is False
        assert "not found" in result.message

    @pytest.mark.asyncio
    async def test_complete_rule_no_issues(self):
        rule_data = {"name": "R1", "directive": "Do X", "category": "technical", "priority": "HIGH"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = rule_data
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            curator = _TestCurator()
            result = await curator.validate_rule("R-1")

        assert result.success is True
        assert len(result.issues_found) == 0

    @pytest.mark.asyncio
    async def test_missing_fields_found(self):
        rule_data = {"name": "R1"}  # missing directive, category, priority
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = rule_data
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            curator = _TestCurator()
            result = await curator.validate_rule("R-1")

        assert result.success is True
        assert len(result.issues_found) == 3  # directive, category, priority

    @pytest.mark.asyncio
    async def test_exception_returns_failure(self):
        with patch("httpx.AsyncClient", side_effect=Exception("connection error")):
            curator = _TestCurator()
            result = await curator.validate_rule("R-1")

        assert result.success is False
        assert "failed" in result.message.lower()


# ── propose_change ────────────────────────────────────────────


class TestProposeChange:
    @pytest.mark.asyncio
    async def test_no_mcp_client(self):
        curator = _TestCurator(mcp_client=None)
        result = await curator.propose_change("R-1", "update", "needs update")
        assert result.success is False
        assert "MCP client required" in result.message

    @pytest.mark.asyncio
    async def test_successful_proposal(self):
        mcp = AsyncMock()
        mcp.call_tool.return_value = {"proposal_id": "PROP-1"}
        curator = _TestCurator(mcp_client=mcp)
        result = await curator.propose_change("R-1", "deprecate", "outdated rule")
        assert result.success is True
        assert result.action == CurationAction.PROPOSE_CHANGE
        assert "deprecate" in result.message

    @pytest.mark.asyncio
    async def test_proposal_includes_evidence(self):
        mcp = AsyncMock()
        mcp.call_tool.return_value = {"id": "P-1"}
        curator = _TestCurator(mcp_client=mcp)
        result = await curator.propose_change("R-1", "merge", "duplicate")
        assert result.evidence is not None

    @pytest.mark.asyncio
    async def test_exception_returns_failure(self):
        mcp = AsyncMock()
        mcp.call_tool.side_effect = Exception("timeout")
        curator = _TestCurator(mcp_client=mcp)
        result = await curator.propose_change("R-1", "update", "fix it")
        assert result.success is False
        assert "failed" in result.message.lower()
