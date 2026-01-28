"""
Rules Curator Agent (ORCH-005).

Monitors rule quality, resolves conflicts, and maintains governance integrity.

Per RULE-011: Multi-Agent Governance
Per RULE-012: Deep Sleep Protocol
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from .engine import AgentInfo, AgentRole


class CurationAction(Enum):
    """Types of curation actions."""
    ANALYZE_QUALITY = "analyze_quality"
    RESOLVE_CONFLICT = "resolve_conflict"
    FIND_ORPHANS = "find_orphans"
    CHECK_DEPENDENCIES = "check_dependencies"
    VALIDATE_RULE = "validate_rule"
    PROPOSE_CHANGE = "propose_change"


class IssueSeverity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RuleIssue:
    """A detected issue with a rule."""
    issue_id: str
    rule_id: str
    issue_type: str
    severity: IssueSeverity
    description: str
    recommendation: str
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved: bool = False
    resolved_at: Optional[str] = None


@dataclass
class CurationResult:
    """Result of a curation action."""
    action: CurationAction
    success: bool
    issues_found: List[RuleIssue] = field(default_factory=list)
    issues_resolved: int = 0
    message: str = ""
    evidence: Optional[str] = None


@dataclass
class ConflictResolution:
    """Resolution for a rule conflict."""
    conflict_id: str
    rule_a: str
    rule_b: str
    resolution_type: str  # "merge", "deprecate", "update", "escalate"
    rationale: str
    proposed_changes: Dict[str, Any] = field(default_factory=dict)


class RulesCuratorAgent:
    """
    Rules Curator Agent for governance quality management.

    Per ORCH-005 design from RD-AGENT-ORCHESTRATION.md.

    Responsibilities:
    - Monitor rule quality (orphans, shallow rules, circular deps)
    - Detect and resolve conflicts between rules
    - Validate rule dependencies
    - Propose rule improvements
    - Maintain governance integrity

    Usage:
        curator = RulesCuratorAgent(mcp_client)

        # Analyze rule quality
        result = await curator.analyze_quality()

        # Check for conflicts
        conflicts = await curator.find_conflicts()

        # Resolve a specific conflict
        resolution = await curator.resolve_conflict("RULE-001", "RULE-005")
    """

    AGENT_ID = "rules-curator"
    AGENT_NAME = "Rules Curator"
    BASE_TRUST_SCORE = 0.90

    def __init__(self, mcp_client: Any = None, api_base: str = "http://localhost:8082"):
        """
        Initialize Rules Curator Agent.

        Args:
            mcp_client: MCP client for governance tools (optional)
            api_base: Base URL for governance API
        """
        self._mcp_client = mcp_client
        self._api_base = api_base
        self._issues: List[RuleIssue] = []
        self._resolutions: List[ConflictResolution] = []
        self._last_analysis: Optional[datetime] = None

    def get_agent_info(self) -> AgentInfo:
        """Get agent registration info."""
        return AgentInfo(
            agent_id=self.AGENT_ID,
            name=self.AGENT_NAME,
            role=AgentRole.CURATOR,
            trust_score=self.BASE_TRUST_SCORE,
        )

    async def analyze_quality(self) -> CurationResult:
        """
        Analyze overall rule quality.

        Checks for:
        - Orphaned rules (no dependents)
        - Shallow rules (missing attributes)
        - Over-connected rules (too many dependencies)
        - Circular dependencies
        - Under-documented rules

        Returns:
            CurationResult with found issues
        """
        issues = []

        try:
            # Use governance MCP tool if available
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
                # Fallback: Use API directly
                import httpx
                async with httpx.AsyncClient() as client:
                    # Get rules
                    response = await client.get(f"{self._api_base}/api/rules")
                    if response.status_code == 200:
                        rules = response.json()

                        # Check for orphaned rules (no dependents)
                        for rule in rules:
                            rule_id = rule.get("rule_id") or rule.get("id")

                            # Check dependencies
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

                            # Check for shallow rules (missing directive)
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
        """
        Find conflicts between rules.

        Uses TypeDB inference to detect conflicting rules.

        Returns:
            CurationResult with conflict issues
        """
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
                # API fallback
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
        """
        Find orphaned rules with no dependents.

        Returns:
            CurationResult with orphan issues
        """
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

    async def check_dependencies(self, rule_id: str) -> CurationResult:
        """
        Check dependency health for a specific rule.

        Args:
            rule_id: Rule ID to check

        Returns:
            CurationResult with dependency issues
        """
        issues = []

        try:
            if self._mcp_client:
                result = await self._mcp_client.call_tool(
                    "governance_get_dependencies",
                    {"rule_id": rule_id}
                )
                if result and isinstance(result, list):
                    # Check if any dependencies are deprecated
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
        """
        Validate a rule for completeness and consistency.

        Args:
            rule_id: Rule ID to validate

        Returns:
            CurationResult with validation issues
        """
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

                # Check required fields
                if not rule.get("name"):
                    issues.append(RuleIssue(
                        issue_id=f"VAL-{len(issues)+1:03d}",
                        rule_id=rule_id,
                        issue_type="missing_name",
                        severity=IssueSeverity.HIGH,
                        description="Rule is missing a name",
                        recommendation="Add a descriptive name",
                    ))

                if not rule.get("directive"):
                    issues.append(RuleIssue(
                        issue_id=f"VAL-{len(issues)+1:03d}",
                        rule_id=rule_id,
                        issue_type="missing_directive",
                        severity=IssueSeverity.HIGH,
                        description="Rule is missing a directive",
                        recommendation="Add a clear directive statement",
                    ))

                if not rule.get("category"):
                    issues.append(RuleIssue(
                        issue_id=f"VAL-{len(issues)+1:03d}",
                        rule_id=rule_id,
                        issue_type="missing_category",
                        severity=IssueSeverity.MEDIUM,
                        description="Rule is missing a category",
                        recommendation="Assign to governance, technical, or operational",
                    ))

                if not rule.get("priority"):
                    issues.append(RuleIssue(
                        issue_id=f"VAL-{len(issues)+1:03d}",
                        rule_id=rule_id,
                        issue_type="missing_priority",
                        severity=IssueSeverity.MEDIUM,
                        description="Rule is missing a priority",
                        recommendation="Set priority (CRITICAL, HIGH, MEDIUM, LOW)",
                    ))

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
        """
        Propose a change to a rule.

        Args:
            rule_id: Rule ID to change
            change_type: Type of change (update, deprecate, etc.)
            rationale: Reason for the change

        Returns:
            CurationResult with proposal status
        """
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

    async def run_full_audit(self) -> Dict[str, CurationResult]:
        """
        Run a complete governance audit.

        Returns:
            Dict mapping action names to their results
        """
        results = {}

        # Quality analysis
        results["quality"] = await self.analyze_quality()

        # Conflict detection
        results["conflicts"] = await self.find_conflicts()

        # Orphan detection
        results["orphans"] = await self.find_orphans()

        return results

    def get_issues(
        self,
        severity: Optional[IssueSeverity] = None,
        resolved: Optional[bool] = None,
    ) -> List[RuleIssue]:
        """
        Get detected issues with optional filtering.

        Args:
            severity: Filter by severity level
            resolved: Filter by resolution status

        Returns:
            List of matching issues
        """
        issues = self._issues

        if severity is not None:
            issues = [i for i in issues if i.severity == severity]

        if resolved is not None:
            issues = [i for i in issues if i.resolved == resolved]

        return issues

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of curator state.

        Returns:
            Dict with issue counts and status
        """
        critical = len([i for i in self._issues if i.severity == IssueSeverity.CRITICAL and not i.resolved])
        high = len([i for i in self._issues if i.severity == IssueSeverity.HIGH and not i.resolved])
        medium = len([i for i in self._issues if i.severity == IssueSeverity.MEDIUM and not i.resolved])
        low = len([i for i in self._issues if i.severity == IssueSeverity.LOW and not i.resolved])

        return {
            "agent_id": self.AGENT_ID,
            "last_analysis": self._last_analysis.isoformat() if self._last_analysis else None,
            "total_issues": len(self._issues),
            "open_issues": len([i for i in self._issues if not i.resolved]),
            "by_severity": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
            },
            "resolutions_pending": len(self._resolutions),
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_curator_agent(
    mcp_client: Any = None,
    api_base: str = "http://localhost:8082",
) -> RulesCuratorAgent:
    """
    Create a Rules Curator Agent instance.

    Args:
        mcp_client: Optional MCP client
        api_base: Base URL for governance API

    Returns:
        Configured RulesCuratorAgent
    """
    return RulesCuratorAgent(mcp_client=mcp_client, api_base=api_base)
