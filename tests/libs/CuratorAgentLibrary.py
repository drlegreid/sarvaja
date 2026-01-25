"""
Robot Framework Library for Rules Curator Agent Tests.

Per ORCH-005: Rules curator agent.
Migrated from tests/test_curator_agent.py
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from robot.api.deco import keyword


class CuratorAgentLibrary:
    """Library for testing rules curator agent."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Import Tests
    # =============================================================================

    @keyword("Import Rules Curator Agent")
    def import_rules_curator_agent(self):
        """Import RulesCuratorAgent."""
        try:
            from agent.orchestrator import RulesCuratorAgent
            return {"imported": RulesCuratorAgent is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Curation Action Enum")
    def import_curation_action_enum(self):
        """Import CurationAction enum."""
        try:
            from agent.orchestrator import CurationAction
            return {
                "analyze_correct": CurationAction.ANALYZE_QUALITY.value == "analyze_quality",
                "resolve_correct": CurationAction.RESOLVE_CONFLICT.value == "resolve_conflict",
                "find_correct": CurationAction.FIND_ORPHANS.value == "find_orphans"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Issue Severity Enum")
    def import_issue_severity_enum(self):
        """Import IssueSeverity enum."""
        try:
            from agent.orchestrator import IssueSeverity
            return {
                "critical_correct": IssueSeverity.CRITICAL.value == "critical",
                "high_correct": IssueSeverity.HIGH.value == "high",
                "medium_correct": IssueSeverity.MEDIUM.value == "medium",
                "low_correct": IssueSeverity.LOW.value == "low"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Curation Result Dataclass")
    def import_curation_result_dataclass(self):
        """Import CurationResult dataclass."""
        try:
            from agent.orchestrator import CurationResult, CurationAction

            result = CurationResult(
                action=CurationAction.ANALYZE_QUALITY,
                success=True,
                message="Test",
            )
            return {
                "success_true": result.success is True,
                "action_correct": result.action == CurationAction.ANALYZE_QUALITY
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Rule Issue Dataclass")
    def import_rule_issue_dataclass(self):
        """Import RuleIssue dataclass."""
        try:
            from agent.orchestrator import RuleIssue, IssueSeverity

            issue = RuleIssue(
                issue_id="ISSUE-001",
                rule_id="RULE-001",
                issue_type="orphaned",
                severity=IssueSeverity.LOW,
                description="No dependents",
                recommendation="Document use cases",
            )
            return {
                "rule_id_correct": issue.rule_id == "RULE-001",
                "resolved_false": issue.resolved is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Import Create Curator Agent Factory")
    def import_create_curator_agent_factory(self):
        """Import create_curator_agent factory."""
        try:
            from agent.orchestrator import create_curator_agent

            curator = create_curator_agent()
            return {"created": curator is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Agent Info Tests
    # =============================================================================

    @keyword("Curator Agent Has Correct ID")
    def curator_agent_has_correct_id(self):
        """Agent has correct ID."""
        try:
            from agent.orchestrator import RulesCuratorAgent
            return {"id_correct": RulesCuratorAgent.AGENT_ID == "rules-curator"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Curator Agent Has Correct Name")
    def curator_agent_has_correct_name(self):
        """Agent has correct name."""
        try:
            from agent.orchestrator import RulesCuratorAgent
            return {"name_correct": RulesCuratorAgent.AGENT_NAME == "Rules Curator"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Curator Agent Has Correct Trust Score")
    def curator_agent_has_correct_trust_score(self):
        """Agent has correct base trust score."""
        try:
            from agent.orchestrator import RulesCuratorAgent
            return {"trust_correct": RulesCuratorAgent.BASE_TRUST_SCORE == 0.90}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Curator Agent Get Info Returns Agent Info")
    def curator_agent_get_info_returns_agent_info(self):
        """Get agent info returns correct AgentInfo."""
        try:
            from agent.orchestrator import RulesCuratorAgent, AgentRole

            curator = RulesCuratorAgent()
            info = curator.get_agent_info()

            return {
                "id_correct": info.agent_id == "rules-curator",
                "name_correct": info.name == "Rules Curator",
                "role_correct": info.role == AgentRole.CURATOR,
                "trust_correct": info.trust_score == 0.90
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Issue Management Tests
    # =============================================================================

    @keyword("Get Issues Returns Empty Initially")
    def get_issues_returns_empty_initially(self):
        """Get issues returns empty list initially."""
        try:
            from agent.orchestrator import RulesCuratorAgent

            curator = RulesCuratorAgent()
            issues = curator.get_issues()

            return {"is_empty": issues == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Issues Filters By Severity")
    def get_issues_filters_by_severity(self):
        """Filter issues by severity."""
        try:
            from agent.orchestrator import RulesCuratorAgent, RuleIssue, IssueSeverity

            curator = RulesCuratorAgent()

            curator._issues = [
                RuleIssue("I1", "R1", "orphan", IssueSeverity.LOW, "Desc", "Fix"),
                RuleIssue("I2", "R2", "conflict", IssueSeverity.HIGH, "Desc", "Fix"),
                RuleIssue("I3", "R3", "shallow", IssueSeverity.MEDIUM, "Desc", "Fix"),
            ]

            high_issues = curator.get_issues(severity=IssueSeverity.HIGH)
            return {
                "count_correct": len(high_issues) == 1,
                "rule_correct": high_issues[0].rule_id == "R2"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Issues Filters By Resolved")
    def get_issues_filters_by_resolved(self):
        """Filter issues by resolution status."""
        try:
            from agent.orchestrator import RulesCuratorAgent, RuleIssue, IssueSeverity

            curator = RulesCuratorAgent()

            issue1 = RuleIssue("I1", "R1", "orphan", IssueSeverity.LOW, "Desc", "Fix")
            issue2 = RuleIssue("I2", "R2", "conflict", IssueSeverity.HIGH, "Desc", "Fix")
            issue2.resolved = True

            curator._issues = [issue1, issue2]

            open_issues = curator.get_issues(resolved=False)
            return {
                "count_correct": len(open_issues) == 1,
                "rule_correct": open_issues[0].rule_id == "R1"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Summary Returns Correct Data")
    def get_summary_returns_correct_data(self):
        """Get curator summary."""
        try:
            from agent.orchestrator import RulesCuratorAgent, RuleIssue, IssueSeverity

            curator = RulesCuratorAgent()

            curator._issues = [
                RuleIssue("I1", "R1", "orphan", IssueSeverity.CRITICAL, "Desc", "Fix"),
                RuleIssue("I2", "R2", "conflict", IssueSeverity.HIGH, "Desc", "Fix"),
                RuleIssue("I3", "R3", "shallow", IssueSeverity.MEDIUM, "Desc", "Fix"),
            ]

            summary = curator.get_summary()

            return {
                "agent_id_correct": summary["agent_id"] == "rules-curator",
                "total_issues_correct": summary["total_issues"] == 3,
                "open_issues_correct": summary["open_issues"] == 3,
                "critical_correct": summary["by_severity"]["critical"] == 1,
                "high_correct": summary["by_severity"]["high"] == 1,
                "medium_correct": summary["by_severity"]["medium"] == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Curation Action Tests
    # =============================================================================

    @keyword("Validate Rule Not Found Returns Error")
    def validate_rule_not_found_returns_error(self):
        """Validate rule returns error for missing rule."""
        try:
            from agent.orchestrator import RulesCuratorAgent
            from unittest.mock import patch, AsyncMock, MagicMock

            curator = RulesCuratorAgent(api_base="http://localhost:8082")

            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                result = asyncio.run(curator.validate_rule("NONEXISTENT"))

                return {
                    "success_false": result.success is False,
                    "has_not_found": "not found" in result.message
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Rule Detects Missing Fields")
    def validate_rule_detects_missing_fields(self):
        """Validate rule detects missing fields."""
        try:
            from agent.orchestrator import RulesCuratorAgent
            from unittest.mock import patch, AsyncMock, MagicMock

            curator = RulesCuratorAgent(api_base="http://localhost:8082")

            with patch('httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "rule_id": "RULE-TEST",
                }
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                result = asyncio.run(curator.validate_rule("RULE-TEST"))

                return {
                    "success_true": result.success is True,
                    "has_issues": len(result.issues_found) >= 4
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Rule Passes For Complete Rule")
    def validate_rule_passes_for_complete_rule(self):
        """Validate rule passes for complete rule."""
        try:
            from agent.orchestrator import RulesCuratorAgent
            from unittest.mock import patch, AsyncMock, MagicMock

            curator = RulesCuratorAgent(api_base="http://localhost:8082")

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

                result = asyncio.run(curator.validate_rule("RULE-TEST"))

                return {
                    "success_true": result.success is True,
                    "no_issues": len(result.issues_found) == 0
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Propose Change Fails Without MCP Client")
    def propose_change_fails_without_mcp_client(self):
        """Propose change fails without MCP client."""
        try:
            from agent.orchestrator import RulesCuratorAgent

            curator = RulesCuratorAgent(api_base="http://localhost:8082")
            result = asyncio.run(curator.propose_change(
                rule_id="RULE-001",
                change_type="update",
                rationale="Test change",
            ))

            return {
                "success_false": result.success is False,
                "has_mcp_required": "MCP client required" in result.message
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("Analyze Quality With MCP Returns Results")
    def analyze_quality_with_mcp_returns_results(self):
        """Analyze quality using MCP client."""
        try:
            from agent.orchestrator import RulesCuratorAgent

            mock_client = MagicMock()
            mock_client.call_tool = AsyncMock(return_value={
                "issues": [
                    {
                        "rule_id": "RULE-001",
                        "type": "orphaned",
                        "severity": "low",
                        "description": "No dependents",
                        "remediation": "Document use cases",
                    }
                ]
            })

            curator = RulesCuratorAgent(mcp_client=mock_client)
            result = asyncio.run(curator.analyze_quality())

            return {
                "success_true": result.success is True,
                "has_issue": len(result.issues_found) == 1,
                "rule_correct": result.issues_found[0].rule_id == "RULE-001"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Find Conflicts With MCP Returns Results")
    def find_conflicts_with_mcp_returns_results(self):
        """Find conflicts using MCP client."""
        try:
            from agent.orchestrator import RulesCuratorAgent

            mock_client = MagicMock()
            mock_client.call_tool = AsyncMock(return_value=[
                {
                    "rule_a": "RULE-001",
                    "rule_b": "RULE-005",
                    "explanation": "Conflicting directives",
                }
            ])

            curator = RulesCuratorAgent(mcp_client=mock_client)
            result = asyncio.run(curator.find_conflicts())

            return {
                "success_true": result.success is True,
                "has_issue": len(result.issues_found) == 1,
                "type_correct": result.issues_found[0].issue_type == "conflict"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Propose Change With MCP Returns Success")
    def propose_change_with_mcp_returns_success(self):
        """Propose change using MCP client."""
        try:
            from agent.orchestrator import RulesCuratorAgent

            mock_client = MagicMock()
            mock_client.call_tool = AsyncMock(return_value={
                "proposal_id": "PROP-001",
                "status": "pending",
            })

            curator = RulesCuratorAgent(mcp_client=mock_client)
            result = asyncio.run(curator.propose_change(
                rule_id="RULE-001",
                change_type="update",
                rationale="Improve clarity",
            ))

            return {
                "success_true": result.success is True,
                "has_proposed": "Proposed update" in result.message
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Run Full Audit Returns All Results")
    def run_full_audit_returns_all_results(self):
        """Run full audit returns all results."""
        try:
            from agent.orchestrator import RulesCuratorAgent

            mock_client = MagicMock()
            mock_client.call_tool = AsyncMock(return_value={"issues": []})

            curator = RulesCuratorAgent(mcp_client=mock_client)
            results = asyncio.run(curator.run_full_audit())

            return {
                "has_quality": "quality" in results,
                "has_conflicts": "conflicts" in results,
                "has_orphans": "orphans" in results,
                "all_success": all(r.success for r in results.values())
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
