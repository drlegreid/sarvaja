"""
Unit tests for Curator Action Methods.

Per DOC-SIZE-01-v1: Tests for extracted curator_actions.py + curator_actions_validation.py.
Tests: CuratorActionsMixin, CuratorValidationMixin, _check_field.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from agent.orchestrator.curator_models import (
    CurationAction,
    CurationResult,
    IssueSeverity,
    RuleIssue,
)
from agent.orchestrator.curator_actions import CuratorActionsMixin, _check_field
from agent.orchestrator.curator_actions_validation import CuratorValidationMixin


class MockCurator(CuratorActionsMixin):
    """Mock host class for curator mixin testing."""

    def __init__(self, mcp_client=None, api_base="http://localhost:8082"):
        self._mcp_client = mcp_client
        self._api_base = api_base
        self._issues = []
        self._last_analysis = None


class TestCheckField:
    """Tests for _check_field() helper."""

    def test_missing_field_adds_issue(self):
        issues = []
        rule = {"rule_id": "R-1", "name": "Test"}
        _check_field(issues, rule, "R-1", "directive", IssueSeverity.HIGH)
        assert len(issues) == 1
        assert issues[0].issue_type == "missing_directive"
        assert issues[0].severity == IssueSeverity.HIGH

    def test_present_field_no_issue(self):
        issues = []
        rule = {"rule_id": "R-1", "name": "Test", "directive": "Do this"}
        _check_field(issues, rule, "R-1", "directive", IssueSeverity.HIGH)
        assert len(issues) == 0

    def test_empty_string_field_adds_issue(self):
        issues = []
        rule = {"rule_id": "R-1", "directive": ""}
        _check_field(issues, rule, "R-1", "directive", IssueSeverity.MEDIUM)
        assert len(issues) == 1

    def test_custom_recommendation(self):
        issues = []
        rule = {"rule_id": "R-1"}
        _check_field(issues, rule, "R-1", "category", IssueSeverity.MEDIUM,
                     recommendation="Set to governance or technical")
        assert issues[0].recommendation == "Set to governance or technical"

    def test_default_recommendation(self):
        issues = []
        rule = {"rule_id": "R-1"}
        _check_field(issues, rule, "R-1", "name", IssueSeverity.HIGH)
        assert "name" in issues[0].recommendation

    def test_issue_id_increments(self):
        issues = [MagicMock()]  # Pre-existing issue
        rule = {"rule_id": "R-1"}
        _check_field(issues, rule, "R-1", "directive", IssueSeverity.HIGH)
        assert issues[-1].issue_id == "VAL-002"


class TestCuratorActionsMixinAnalyzeQuality:
    """Tests for CuratorActionsMixin.analyze_quality()."""

    @pytest.mark.asyncio
    async def test_with_mcp_client(self):
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {
            "issues": [
                {"rule_id": "R-1", "type": "orphaned", "severity": "low",
                 "description": "No deps", "remediation": "Link it"},
            ]
        }
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.analyze_quality()
        assert result.success is True
        assert result.action == CurationAction.ANALYZE_QUALITY
        assert len(result.issues_found) == 1
        assert result.issues_found[0].rule_id == "R-1"

    @pytest.mark.asyncio
    async def test_updates_internal_state(self):
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {
            "issues": [
                {"rule_id": "R-1", "type": "stale", "severity": "medium",
                 "description": "Old", "remediation": "Update"},
            ]
        }
        curator = MockCurator(mcp_client=mock_client)
        await curator.analyze_quality()
        assert len(curator._issues) == 1
        assert curator._last_analysis is not None

    @pytest.mark.asyncio
    async def test_mcp_error_returns_failure(self):
        mock_client = AsyncMock()
        mock_client.call_tool.side_effect = Exception("MCP down")
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.analyze_quality()
        assert result.success is False
        assert "Analysis failed" in result.message

    @pytest.mark.asyncio
    async def test_no_mcp_no_http_returns_failure(self):
        curator = MockCurator(mcp_client=None, api_base="http://nonexistent:9999")
        result = await curator.analyze_quality()
        # Without reachable host, should fail gracefully
        assert result.success is False


class TestCuratorActionsMixinFindConflicts:
    """Tests for CuratorActionsMixin.find_conflicts()."""

    @pytest.mark.asyncio
    async def test_with_mcp_conflicts(self):
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = [
            {"rule_a": "CONTAINER-SHELL-01", "rule_b": "WORKFLOW-SHELL-01",
             "explanation": "Both cover shell commands"},
        ]
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.find_conflicts()
        assert result.success is True
        assert result.action == CurationAction.RESOLVE_CONFLICT
        assert len(result.issues_found) == 1
        assert result.issues_found[0].severity == IssueSeverity.HIGH

    @pytest.mark.asyncio
    async def test_no_conflicts(self):
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = []
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.find_conflicts()
        assert result.success is True
        assert len(result.issues_found) == 0


class TestCuratorActionsMixinFindOrphans:
    """Tests for CuratorActionsMixin.find_orphans()."""

    @pytest.mark.asyncio
    async def test_with_mcp_orphans(self):
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = [
            {"rule_id": "ORPHAN-01", "severity": "low", "description": "No deps",
             "remediation": "Link it"},
        ]
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.find_orphans()
        assert result.success is True
        assert result.action == CurationAction.FIND_ORPHANS
        assert len(result.issues_found) == 1

    @pytest.mark.asyncio
    async def test_no_mcp_no_orphans(self):
        curator = MockCurator(mcp_client=None)
        result = await curator.find_orphans()
        assert result.success is True
        assert len(result.issues_found) == 0


class TestCuratorValidationMixinCheckDependencies:
    """Tests for CuratorValidationMixin.check_dependencies()."""

    @pytest.mark.asyncio
    async def test_deprecated_dependency(self):
        mock_client = AsyncMock()
        mock_client.call_tool.side_effect = [
            ["DEP-RULE-01"],  # get dependencies
            {"status": "DEPRECATED"},  # get rule
        ]
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.check_dependencies("R-1")
        assert result.success is True
        assert result.action == CurationAction.CHECK_DEPENDENCIES
        assert len(result.issues_found) == 1
        assert result.issues_found[0].issue_type == "deprecated_dependency"

    @pytest.mark.asyncio
    async def test_no_deprecated(self):
        mock_client = AsyncMock()
        mock_client.call_tool.side_effect = [
            ["DEP-RULE-01"],
            {"status": "ACTIVE"},
        ]
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.check_dependencies("R-1")
        assert result.success is True
        assert len(result.issues_found) == 0

    @pytest.mark.asyncio
    async def test_error_returns_failure(self):
        mock_client = AsyncMock()
        mock_client.call_tool.side_effect = Exception("Connection refused")
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.check_dependencies("R-1")
        assert result.success is False
        assert "Dependency check failed" in result.message


class TestCuratorValidationMixinProposeChange:
    """Tests for CuratorValidationMixin.propose_change()."""

    @pytest.mark.asyncio
    async def test_with_mcp(self):
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {"proposal_id": "P-001"}
        curator = MockCurator(mcp_client=mock_client)
        result = await curator.propose_change("R-1", "update", "Outdated directive")
        assert result.success is True
        assert result.action == CurationAction.PROPOSE_CHANGE
        assert result.evidence is not None

    @pytest.mark.asyncio
    async def test_without_mcp_fails(self):
        curator = MockCurator(mcp_client=None)
        result = await curator.propose_change("R-1", "deprecate", "Replaced")
        assert result.success is False
        assert "MCP client required" in result.message
