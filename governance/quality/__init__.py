"""
Rule Quality Package
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Detects issues with rules:
- Orphaned rules (no dependents)
- Shallow rules (missing attributes)
- Over-connected rules (too many dependencies)
- Under-documented rules (not referenced by docs)
- Circular dependencies
- Impact analysis for rule changes
- Remediation strategies

Per: RULE-010 (Evidence-Based Wisdom), RULE-013 (Rules Applicability)

Usage:
    from governance.quality import RuleQualityAnalyzer, analyze_rule_quality

    # Full analysis
    analyzer = RuleQualityAnalyzer()
    report = analyzer.analyze()

    # Or use convenience function
    json_report = analyze_rule_quality()
"""

from governance.quality.models import (
    IssueSeverity,
    IssueType,
    RuleIssue,
    RuleHealthReport,
)
from governance.quality.analyzer import RuleQualityAnalyzer
from governance.quality.functions import (
    analyze_rule_quality,
    get_rule_impact,
    find_rule_issues,
)

__all__ = [
    # Models
    "IssueSeverity",
    "IssueType",
    "RuleIssue",
    "RuleHealthReport",
    # Analyzer
    "RuleQualityAnalyzer",
    # Functions
    "analyze_rule_quality",
    "get_rule_impact",
    "find_rule_issues",
]
