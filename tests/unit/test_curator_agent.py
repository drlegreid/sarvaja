"""
Unit tests for Rules Curator Agent.

Per ORCH-005: Tests for curator_agent.py main class.
Tests: RulesCuratorAgent, create_curator_agent, get_issues, get_summary, run_full_audit.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from agent.orchestrator.curator_agent import (
    RulesCuratorAgent,
    create_curator_agent,
)
from agent.orchestrator.curator_models import (
    CurationAction,
    CurationResult,
    IssueSeverity,
    RuleIssue,
)
from agent.orchestrator.engine_models import AgentRole


class TestRulesCuratorAgentInit:
    """Tests for RulesCuratorAgent initialization."""

    def test_default_init(self):
        curator = RulesCuratorAgent()
        assert curator._mcp_client is None
        assert curator._api_base == "http://localhost:8082"
        assert curator._issues == []
        assert curator._resolutions == []
        assert curator._last_analysis is None

    def test_custom_init(self):
        mock_client = MagicMock()
        curator = RulesCuratorAgent(mcp_client=mock_client, api_base="http://custom:9000")
        assert curator._mcp_client is mock_client
        assert curator._api_base == "http://custom:9000"

    def test_class_constants(self):
        assert RulesCuratorAgent.AGENT_ID == "rules-curator"
        assert RulesCuratorAgent.AGENT_NAME == "Rules Curator"
        assert RulesCuratorAgent.BASE_TRUST_SCORE == 0.90


class TestGetAgentInfo:
    """Tests for RulesCuratorAgent.get_agent_info()."""

    def test_returns_agent_info(self):
        curator = RulesCuratorAgent()
        info = curator.get_agent_info()
        assert info.agent_id == "rules-curator"
        assert info.name == "Rules Curator"
        assert info.role == AgentRole.CURATOR
        assert info.trust_score == 0.90

    def test_trust_level_expert(self):
        curator = RulesCuratorAgent()
        info = curator.get_agent_info()
        assert info.trust_level == "expert"


class TestGetIssues:
    """Tests for RulesCuratorAgent.get_issues()."""

    @pytest.fixture
    def curator_with_issues(self):
        curator = RulesCuratorAgent()
        curator._issues = [
            RuleIssue("I-1", "R-1", "orphaned", IssueSeverity.LOW, "d", "r", resolved=False),
            RuleIssue("I-2", "R-2", "conflict", IssueSeverity.HIGH, "d", "r", resolved=False),
            RuleIssue("I-3", "R-3", "stale", IssueSeverity.MEDIUM, "d", "r", resolved=True),
            RuleIssue("I-4", "R-4", "shallow", IssueSeverity.HIGH, "d", "r", resolved=False),
        ]
        return curator

    def test_all_issues(self, curator_with_issues):
        issues = curator_with_issues.get_issues()
        assert len(issues) == 4

    def test_filter_by_severity(self, curator_with_issues):
        issues = curator_with_issues.get_issues(severity=IssueSeverity.HIGH)
        assert len(issues) == 2
        assert all(i.severity == IssueSeverity.HIGH for i in issues)

    def test_filter_by_resolved(self, curator_with_issues):
        issues = curator_with_issues.get_issues(resolved=False)
        assert len(issues) == 3

    def test_filter_resolved_true(self, curator_with_issues):
        issues = curator_with_issues.get_issues(resolved=True)
        assert len(issues) == 1
        assert issues[0].issue_id == "I-3"

    def test_filter_combined(self, curator_with_issues):
        issues = curator_with_issues.get_issues(severity=IssueSeverity.HIGH, resolved=False)
        assert len(issues) == 2

    def test_no_issues(self):
        curator = RulesCuratorAgent()
        assert curator.get_issues() == []


class TestGetSummary:
    """Tests for RulesCuratorAgent.get_summary()."""

    def test_empty_summary(self):
        curator = RulesCuratorAgent()
        summary = curator.get_summary()
        assert summary["agent_id"] == "rules-curator"
        assert summary["last_analysis"] is None
        assert summary["total_issues"] == 0
        assert summary["open_issues"] == 0
        assert summary["resolutions_pending"] == 0

    def test_summary_with_issues(self):
        curator = RulesCuratorAgent()
        curator._issues = [
            RuleIssue("I-1", "R-1", "orphan", IssueSeverity.LOW, "d", "r"),
            RuleIssue("I-2", "R-2", "conflict", IssueSeverity.HIGH, "d", "r"),
            RuleIssue("I-3", "R-3", "stale", IssueSeverity.HIGH, "d", "r", resolved=True),
        ]
        summary = curator.get_summary()
        assert summary["total_issues"] == 3
        assert summary["open_issues"] == 2
        assert summary["by_severity"]["low"] == 1
        assert summary["by_severity"]["high"] == 1  # Only open HIGH
        assert summary["by_severity"]["critical"] == 0

    def test_summary_with_last_analysis(self):
        curator = RulesCuratorAgent()
        now = datetime.now()
        curator._last_analysis = now
        summary = curator.get_summary()
        assert summary["last_analysis"] == now.isoformat()

    def test_summary_resolutions(self):
        curator = RulesCuratorAgent()
        curator._resolutions = [MagicMock(), MagicMock()]
        summary = curator.get_summary()
        assert summary["resolutions_pending"] == 2


class TestRunFullAudit:
    """Tests for RulesCuratorAgent.run_full_audit()."""

    @pytest.mark.asyncio
    async def test_runs_all_checks(self):
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {"issues": []}
        curator = RulesCuratorAgent(mcp_client=mock_client)
        results = await curator.run_full_audit()
        assert "quality" in results
        assert "conflicts" in results
        assert "orphans" in results
        assert isinstance(results["quality"], CurationResult)
        assert isinstance(results["conflicts"], CurationResult)
        assert isinstance(results["orphans"], CurationResult)


class TestCreateCuratorAgent:
    """Tests for create_curator_agent() factory."""

    def test_creates_instance(self):
        agent = create_curator_agent()
        assert isinstance(agent, RulesCuratorAgent)
        assert agent._mcp_client is None

    def test_with_args(self):
        mock = MagicMock()
        agent = create_curator_agent(mcp_client=mock, api_base="http://test:8080")
        assert agent._mcp_client is mock
        assert agent._api_base == "http://test:8080"
