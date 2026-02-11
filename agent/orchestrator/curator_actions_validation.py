"""
Rules Curator Validation & Proposal Actions (Mixin).

Per DOC-SIZE-01-v1: Extracted from curator_actions.py.
Validation, dependency checks, and change proposals.
"""

from .curator_models import (
    CurationAction,
    CurationResult,
    IssueSeverity,
    RuleIssue,
)


class CuratorValidationMixin:
    """Mixin providing validation and proposal action methods.

    Expects host class to provide:
        self._mcp_client: Optional MCP client
        self._api_base: str API base URL
        self._issues: List[RuleIssue]
    """

    async def check_dependencies(self, rule_id: str) -> CurationResult:
        """Check dependency health for a specific rule."""
        issues = []

        try:
            if self._mcp_client:
                result = await self._mcp_client.call_tool(
                    "governance_get_dependencies",
                    {"rule_id": rule_id}
                )
                if result and isinstance(result, list):
                    for dep_id in result:
                        dep_result = await self._mcp_client.call_tool(
                            "governance_get_rule",
                            {"rule_id": dep_id}
                        )
                        if dep_result and dep_result.get("status") == "DEPRECATED":
                            issues.append(RuleIssue(
                                issue_id=f"DEP-{len(issues)+1:03d}",
                                rule_id=rule_id,
                                issue_type="deprecated_dependency",
                                severity=IssueSeverity.MEDIUM,
                                description=f"Depends on deprecated rule {dep_id}",
                                recommendation=f"Update to remove dependency on {dep_id}",
                            ))

            self._issues.extend(issues)

            return CurationResult(
                action=CurationAction.CHECK_DEPENDENCIES,
                success=True,
                issues_found=issues,
                message=f"Checked {rule_id}: {len(issues)} issues found",
            )

        except Exception as e:
            return CurationResult(
                action=CurationAction.CHECK_DEPENDENCIES,
                success=False,
                message=f"Dependency check failed: {str(e)}",
            )

    async def validate_rule(self, rule_id: str) -> CurationResult:
        """Validate a rule for completeness and consistency."""
        issues = []

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self._api_base}/api/rules/{rule_id}")
                if response.status_code != 200:
                    return CurationResult(
                        action=CurationAction.VALIDATE_RULE,
                        success=False,
                        message=f"Rule {rule_id} not found",
                    )

                rule = response.json()

                _check_field(issues, rule, rule_id, "name", IssueSeverity.HIGH)
                _check_field(issues, rule, rule_id, "directive", IssueSeverity.HIGH)
                _check_field(
                    issues, rule, rule_id, "category", IssueSeverity.MEDIUM,
                    recommendation="Assign to governance, technical, or operational",
                )
                _check_field(
                    issues, rule, rule_id, "priority", IssueSeverity.MEDIUM,
                    recommendation="Set priority (CRITICAL, HIGH, MEDIUM, LOW)",
                )

            self._issues.extend(issues)

            return CurationResult(
                action=CurationAction.VALIDATE_RULE,
                success=True,
                issues_found=issues,
                message=f"Validated {rule_id}: {len(issues)} issues",
            )

        except Exception as e:
            return CurationResult(
                action=CurationAction.VALIDATE_RULE,
                success=False,
                message=f"Validation failed: {str(e)}",
            )

    async def propose_change(
        self,
        rule_id: str,
        change_type: str,
        rationale: str,
    ) -> CurationResult:
        """Propose a change to a rule."""
        try:
            if self._mcp_client:
                result = await self._mcp_client.call_tool(
                    "governance_propose_rule",
                    {
                        "action": change_type,
                        "rule_id": rule_id,
                        "hypothesis": rationale,
                        "evidence": [f"Curator analysis: {rationale}"],
                    }
                )

                return CurationResult(
                    action=CurationAction.PROPOSE_CHANGE,
                    success=True,
                    message=f"Proposed {change_type} for {rule_id}",
                    evidence=str(result),
                )

            return CurationResult(
                action=CurationAction.PROPOSE_CHANGE,
                success=False,
                message="MCP client required for proposals",
            )

        except Exception as e:
            return CurationResult(
                action=CurationAction.PROPOSE_CHANGE,
                success=False,
                message=f"Proposal failed: {str(e)}",
            )


def _check_field(
    issues: list,
    rule: dict,
    rule_id: str,
    field_name: str,
    severity: IssueSeverity,
    recommendation: str | None = None,
) -> None:
    """Append a missing-field issue if the rule lacks the given field."""
    if not rule.get(field_name):
        issues.append(RuleIssue(
            issue_id=f"VAL-{len(issues)+1:03d}",
            rule_id=rule_id,
            issue_type=f"missing_{field_name}",
            severity=severity,
            description=f"Rule is missing a {field_name}",
            recommendation=recommendation or f"Add a descriptive {field_name}",
        ))
