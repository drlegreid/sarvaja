"""
Rule Quality MCP Tools
======================
Rule quality analysis operations.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-008: Extracted from evidence.py

Tools:
- governance_analyze_rules: Comprehensive rule quality analysis
- governance_rule_impact: Analyze rule modification impact
- governance_find_issues: Find specific rule quality issues

Created: 2024-12-28
"""

from typing import Optional

from governance.mcp_tools.common import format_mcp_result

# Import rule quality analyzer (with fallback)
try:
    from governance.rule_quality import (
        RuleQualityAnalyzer,
        analyze_rule_quality,
        get_rule_impact,
        find_rule_issues
    )
    RULE_QUALITY_AVAILABLE = True
except ImportError:
    RULE_QUALITY_AVAILABLE = False


def register_quality_tools(mcp) -> None:
    """Register rule quality MCP tools."""

    @mcp.tool()
    def governance_analyze_rules() -> str:
        """
        Run comprehensive rule quality analysis.

        Detects:
        - Orphaned rules (no dependents)
        - Shallow rules (missing attributes)
        - Over-connected rules (too many dependencies)
        - Under-documented rules (not referenced by docs)
        - Circular dependencies

        Returns:
            JSON health report with issues, severity, impact, and remediation
        """
        if not RULE_QUALITY_AVAILABLE:
            return format_mcp_result({"error": "RuleQualityAnalyzer not available"})

        return analyze_rule_quality()

    @mcp.tool()
    def governance_rule_impact(rule_id: str) -> str:
        """
        Analyze impact if a rule is modified or deprecated.

        Args:
            rule_id: Rule ID (e.g., "RULE-001")

        Returns:
            JSON with affected rules, impact score, and recommendation
        """
        if not RULE_QUALITY_AVAILABLE:
            return format_mcp_result({"error": "RuleQualityAnalyzer not available"})

        return get_rule_impact(rule_id)

    @mcp.tool()
    def governance_find_issues(issue_type: Optional[str] = None) -> str:
        """
        Find specific types of rule quality issues.

        Args:
            issue_type: Type of issues to find:
                - "orphaned": Rules with no dependents
                - "shallow": Rules missing attributes
                - "over_connected": Rules with too many dependencies
                - "circular": Circular dependency chains
                - "under_documented": Rules not in any docs
                - None: All issues (default)

        Returns:
            JSON array of issues with severity, impact, and remediation
        """
        if not RULE_QUALITY_AVAILABLE:
            return format_mcp_result({"error": "RuleQualityAnalyzer not available"})

        return find_rule_issues(issue_type)
