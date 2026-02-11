"""
Rules Curator Action Methods (Mixin).

Per DOC-SIZE-01-v1: Extracted from curator_agent.py (588 lines).
Async curation actions: quality analysis, conflict detection, orphan finding.
Per DOC-SIZE-01-v1: Validation + proposals in curator_actions_validation.py.
"""

from datetime import datetime

from .curator_models import (
    CurationAction,
    CurationResult,
    IssueSeverity,
    RuleIssue,
)

# Re-export validation mixin for backward compatibility
from .curator_actions_validation import (  # noqa: F401
    CuratorValidationMixin,
    _check_field,
)


class CuratorActionsMixin(CuratorValidationMixin):
    """Mixin providing async curation action methods.

    Expects host class to provide:
        self._mcp_client: Optional MCP client
        self._api_base: str API base URL
        self._issues: List[RuleIssue]
        self._last_analysis: Optional[datetime]

    Inherits check_dependencies, validate_rule, propose_change from
    CuratorValidationMixin.
    """

    async def analyze_quality(self) -> CurationResult:
        """Analyze overall rule quality.

        Checks for orphaned rules, shallow rules, and missing attributes.
        """
        issues = []

        try:
            if self._mcp_client:
                result = await self._mcp_client.call_tool(
                    "governance_analyze_rules", {}
                )
                if result and "issues" in result:
                    for issue_data in result["issues"]:
                        issues.append(RuleIssue(
                            issue_id=f"ISSUE-{len(issues)+1:03d}",
                            rule_id=issue_data.get("rule_id", "UNKNOWN"),
                            issue_type=issue_data.get("type", "unknown"),
                            severity=IssueSeverity(issue_data.get("severity", "medium").lower()),
                            description=issue_data.get("description", ""),
                            recommendation=issue_data.get("remediation", ""),
                        ))
            else:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self._api_base}/api/rules")
                    if response.status_code == 200:
                        rules = response.json()
                        for rule in rules:
                            rule_id = rule.get("rule_id") or rule.get("id")
                            deps_response = await client.get(
                                f"{self._api_base}/api/rules/{rule_id}/impact"
                            )
                            if deps_response.status_code == 200:
                                impact = deps_response.json()
                                if not impact.get("direct_dependents"):
                                    issues.append(RuleIssue(
                                        issue_id=f"ISSUE-{len(issues)+1:03d}",
                                        rule_id=rule_id,
                                        issue_type="orphaned",
                                        severity=IssueSeverity.LOW,
                                        description=f"Rule {rule_id} has no dependents",
                                        recommendation="Consider consolidating or documenting use cases",
                                    ))
                            if not rule.get("directive"):
                                issues.append(RuleIssue(
                                    issue_id=f"ISSUE-{len(issues)+1:03d}",
                                    rule_id=rule_id,
                                    issue_type="shallow",
                                    severity=IssueSeverity.MEDIUM,
                                    description=f"Rule {rule_id} is missing directive",
                                    recommendation="Add a clear directive statement",
                                ))

            self._issues.extend(issues)
            self._last_analysis = datetime.now()

            return CurationResult(
                action=CurationAction.ANALYZE_QUALITY,
                success=True,
                issues_found=issues,
                message=f"Found {len(issues)} quality issues",
            )

        except Exception as e:
            return CurationResult(
                action=CurationAction.ANALYZE_QUALITY,
                success=False,
                message=f"Analysis failed: {str(e)}",
            )

    async def find_conflicts(self) -> CurationResult:
        """Find conflicts between rules using TypeDB inference."""
        issues = []

        try:
            if self._mcp_client:
                result = await self._mcp_client.call_tool(
                    "governance_find_conflicts", {}
                )
                if result and isinstance(result, list):
                    for conflict in result:
                        issues.append(RuleIssue(
                            issue_id=f"CONFLICT-{len(issues)+1:03d}",
                            rule_id=conflict.get("rule_a", ""),
                            issue_type="conflict",
                            severity=IssueSeverity.HIGH,
                            description=f"Conflict with {conflict.get('rule_b', '')}",
                            recommendation=conflict.get("explanation", "Review and resolve"),
                        ))
            else:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self._api_base}/api/rules/conflicts")
                    if response.status_code == 200:
                        conflicts = response.json()
                        for conflict in conflicts:
                            issues.append(RuleIssue(
                                issue_id=f"CONFLICT-{len(issues)+1:03d}",
                                rule_id=conflict.get("rule_a", ""),
                                issue_type="conflict",
                                severity=IssueSeverity.HIGH,
                                description=f"Conflict with {conflict.get('rule_b', '')}",
                                recommendation="Review and resolve conflict",
                            ))

            self._issues.extend(issues)

            return CurationResult(
                action=CurationAction.RESOLVE_CONFLICT,
                success=True,
                issues_found=issues,
                message=f"Found {len(issues)} conflicts",
            )

        except Exception as e:
            return CurationResult(
                action=CurationAction.RESOLVE_CONFLICT,
                success=False,
                message=f"Conflict detection failed: {str(e)}",
            )

    async def find_orphans(self) -> CurationResult:
        """Find orphaned rules with no dependents."""
        issues = []

        try:
            if self._mcp_client:
                result = await self._mcp_client.call_tool(
                    "governance_find_issues",
                    {"issue_type": "orphaned"}
                )
                if result and isinstance(result, list):
                    for issue_data in result:
                        issues.append(RuleIssue(
                            issue_id=f"ORPHAN-{len(issues)+1:03d}",
                            rule_id=issue_data.get("rule_id", ""),
                            issue_type="orphaned",
                            severity=IssueSeverity(issue_data.get("severity", "low").lower()),
                            description=issue_data.get("description", "No dependents"),
                            recommendation=issue_data.get("remediation", ""),
                        ))

            self._issues.extend(issues)

            return CurationResult(
                action=CurationAction.FIND_ORPHANS,
                success=True,
                issues_found=issues,
                message=f"Found {len(issues)} orphaned rules",
            )

        except Exception as e:
            return CurationResult(
                action=CurationAction.FIND_ORPHANS,
                success=False,
                message=f"Orphan detection failed: {str(e)}",
            )
