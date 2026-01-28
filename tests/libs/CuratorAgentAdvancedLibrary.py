"""
Robot Framework Library for Rules Curator Agent Advanced Tests.

Per ORCH-005: Rules curator agent.
Split from CuratorAgentLibrary.py per DOC-SIZE-01-v1.
Covers: Curation Action Tests, Integration Tests.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from robot.api.deco import keyword


class CuratorAgentAdvancedLibrary:
    """Library for testing rules curator agent - curation actions and integration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

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
