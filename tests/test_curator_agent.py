"""
Tests for Rules Curator Agent (ORCH-005).

Per RULE-023: Test Coverage Protocol
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# Import Tests
# =============================================================================

class TestCuratorAgentImports:
    """Test curator agent module imports."""

    def test_import_curator_agent(self):
        """Import RulesCuratorAgent."""
        from agent.orchestrator import RulesCuratorAgent

        assert RulesCuratorAgent is not None

    def test_import_curation_action(self):
        """Import CurationAction enum."""
        from agent.orchestrator import CurationAction

        assert CurationAction.ANALYZE_QUALITY.value == "analyze_quality"
        assert CurationAction.RESOLVE_CONFLICT.value == "resolve_conflict"
        assert CurationAction.FIND_ORPHANS.value == "find_orphans"

    def test_import_issue_severity(self):
        """Import IssueSeverity enum."""
        from agent.orchestrator import IssueSeverity

        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.HIGH.value == "high"
        assert IssueSeverity.MEDIUM.value == "medium"
        assert IssueSeverity.LOW.value == "low"

    def test_import_curation_result(self):
        """Import CurationResult dataclass."""
        from agent.orchestrator import CurationResult, CurationAction

        result = CurationResult(
            action=CurationAction.ANALYZE_QUALITY,
            success=True,
            message="Test",
        )
        assert result.success is True
        assert result.action == CurationAction.ANALYZE_QUALITY

    def test_import_rule_issue(self):
        """Import RuleIssue dataclass."""
        from agent.orchestrator import RuleIssue, IssueSeverity

        issue = RuleIssue(
            issue_id="ISSUE-001",
            rule_id="RULE-001",
            issue_type="orphaned",
            severity=IssueSeverity.LOW,
            description="No dependents",
            recommendation="Document use cases",
        )
        assert issue.rule_id == "RULE-001"
        assert issue.resolved is False

    def test_import_factory_function(self):
        """Import create_curator_agent factory."""
        from agent.orchestrator import create_curator_agent

        curator = create_curator_agent()
        assert curator is not None


# =============================================================================
# Agent Info Tests
# =============================================================================

class TestCuratorAgentInfo:
    """Test curator agent registration info."""

    def test_agent_id(self):
        """Agent has correct ID."""
        from agent.orchestrator import RulesCuratorAgent

        assert RulesCuratorAgent.AGENT_ID == "rules-curator"

    def test_agent_name(self):
        """Agent has correct name."""
        from agent.orchestrator import RulesCuratorAgent

        assert RulesCuratorAgent.AGENT_NAME == "Rules Curator"

    def test_base_trust_score(self):
        """Agent has correct base trust score."""
        from agent.orchestrator import RulesCuratorAgent

        assert RulesCuratorAgent.BASE_TRUST_SCORE == 0.90

    def test_get_agent_info(self):
        """Get agent info returns correct AgentInfo."""
        from agent.orchestrator import RulesCuratorAgent, AgentRole

        curator = RulesCuratorAgent()
        info = curator.get_agent_info()

        assert info.agent_id == "rules-curator"
        assert info.name == "Rules Curator"
        assert info.role == AgentRole.CURATOR
        assert info.trust_score == 0.90


# =============================================================================
# Issue Management Tests
# =============================================================================

class TestIssueManagement:
    """Test issue tracking functionality."""

    def test_get_issues_empty(self):
        """Get issues returns empty list initially."""
        from agent.orchestrator import RulesCuratorAgent

        curator = RulesCuratorAgent()
        issues = curator.get_issues()

        assert issues == []

    def test_get_issues_filter_by_severity(self):
        """Filter issues by severity."""
        from agent.orchestrator import RulesCuratorAgent, RuleIssue, IssueSeverity

        curator = RulesCuratorAgent()

        # Add test issues
        curator._issues = [
            RuleIssue("I1", "R1", "orphan", IssueSeverity.LOW, "Desc", "Fix"),
            RuleIssue("I2", "R2", "conflict", IssueSeverity.HIGH, "Desc", "Fix"),
            RuleIssue("I3", "R3", "shallow", IssueSeverity.MEDIUM, "Desc", "Fix"),
        ]

        high_issues = curator.get_issues(severity=IssueSeverity.HIGH)
        assert len(high_issues) == 1
        assert high_issues[0].rule_id == "R2"

    def test_get_issues_filter_by_resolved(self):
        """Filter issues by resolution status."""
        from agent.orchestrator import RulesCuratorAgent, RuleIssue, IssueSeverity

        curator = RulesCuratorAgent()

        # Add test issues
        issue1 = RuleIssue("I1", "R1", "orphan", IssueSeverity.LOW, "Desc", "Fix")
        issue2 = RuleIssue("I2", "R2", "conflict", IssueSeverity.HIGH, "Desc", "Fix")
        issue2.resolved = True

        curator._issues = [issue1, issue2]

        open_issues = curator.get_issues(resolved=False)
        assert len(open_issues) == 1
        assert open_issues[0].rule_id == "R1"

    def test_get_summary(self):
        """Get curator summary."""
        from agent.orchestrator import RulesCuratorAgent, RuleIssue, IssueSeverity

        curator = RulesCuratorAgent()

        # Add test issues
        curator._issues = [
            RuleIssue("I1", "R1", "orphan", IssueSeverity.CRITICAL, "Desc", "Fix"),
            RuleIssue("I2", "R2", "conflict", IssueSeverity.HIGH, "Desc", "Fix"),
            RuleIssue("I3", "R3", "shallow", IssueSeverity.MEDIUM, "Desc", "Fix"),
        ]

        summary = curator.get_summary()

        assert summary["agent_id"] == "rules-curator"
        assert summary["total_issues"] == 3
        assert summary["open_issues"] == 3
        assert summary["by_severity"]["critical"] == 1
        assert summary["by_severity"]["high"] == 1
        assert summary["by_severity"]["medium"] == 1


# =============================================================================
# Curation Action Tests
# =============================================================================

class TestCurationActions:
    """Test curation actions."""

    @pytest.fixture
    def curator(self):
        """Create curator agent."""
        from agent.orchestrator import RulesCuratorAgent
        return RulesCuratorAgent(api_base="http://localhost:8082")

    @pytest.mark.asyncio
    async def test_validate_rule_not_found(self, curator):
        """Validate rule returns error for missing rule."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await curator.validate_rule("NONEXISTENT")

            assert result.success is False
            assert "not found" in result.message

    @pytest.mark.asyncio
    async def test_validate_rule_missing_fields(self, curator):
        """Validate rule detects missing fields."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "rule_id": "RULE-TEST",
                # Missing: name, directive, category, priority
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await curator.validate_rule("RULE-TEST")

            assert result.success is True
            assert len(result.issues_found) >= 4  # At least 4 missing fields

    @pytest.mark.asyncio
    async def test_validate_rule_complete(self, curator):
        """Validate rule passes for complete rule."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "rule_id": "RULE-TEST",
                "name": "Test Rule",
                "directive": "Do something",
                "category": "governance",
                "priority": "HIGH",
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await curator.validate_rule("RULE-TEST")

            assert result.success is True
            assert len(result.issues_found) == 0

    @pytest.mark.asyncio
    async def test_propose_change_no_client(self, curator):
        """Propose change fails without MCP client."""
        result = await curator.propose_change(
            rule_id="RULE-001",
            change_type="update",
            rationale="Test change",
        )

        assert result.success is False
        assert "MCP client required" in result.message


# =============================================================================
# Integration Tests
# =============================================================================

class TestCuratorIntegration:
    """Integration tests for curator agent."""

    @pytest.fixture
    def curator_with_mock_client(self):
        """Create curator with mock MCP client."""
        from agent.orchestrator import RulesCuratorAgent

        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock()
        return RulesCuratorAgent(mcp_client=mock_client)

    @pytest.mark.asyncio
    async def test_analyze_quality_with_mcp(self, curator_with_mock_client):
        """Analyze quality using MCP client."""
        curator_with_mock_client._mcp_client.call_tool.return_value = {
            "issues": [
                {
                    "rule_id": "RULE-001",
                    "type": "orphaned",
                    "severity": "low",
                    "description": "No dependents",
                    "remediation": "Document use cases",
                }
            ]
        }

        result = await curator_with_mock_client.analyze_quality()

        assert result.success is True
        assert len(result.issues_found) == 1
        assert result.issues_found[0].rule_id == "RULE-001"

    @pytest.mark.asyncio
    async def test_find_conflicts_with_mcp(self, curator_with_mock_client):
        """Find conflicts using MCP client."""
        curator_with_mock_client._mcp_client.call_tool.return_value = [
            {
                "rule_a": "RULE-001",
                "rule_b": "RULE-005",
                "explanation": "Conflicting directives",
            }
        ]

        result = await curator_with_mock_client.find_conflicts()

        assert result.success is True
        assert len(result.issues_found) == 1
        assert result.issues_found[0].issue_type == "conflict"

    @pytest.mark.asyncio
    async def test_propose_change_with_mcp(self, curator_with_mock_client):
        """Propose change using MCP client."""
        curator_with_mock_client._mcp_client.call_tool.return_value = {
            "proposal_id": "PROP-001",
            "status": "pending",
        }

        result = await curator_with_mock_client.propose_change(
            rule_id="RULE-001",
            change_type="update",
            rationale="Improve clarity",
        )

        assert result.success is True
        assert "Proposed update" in result.message

    @pytest.mark.asyncio
    async def test_run_full_audit(self, curator_with_mock_client):
        """Run full audit returns all results."""
        curator_with_mock_client._mcp_client.call_tool.return_value = {"issues": []}

        results = await curator_with_mock_client.run_full_audit()

        assert "quality" in results
        assert "conflicts" in results
        assert "orphans" in results
        assert all(r.success for r in results.values())
