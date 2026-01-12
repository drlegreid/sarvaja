"""
Rule Quality Analyzer (DEPRECATED - use governance.quality package)
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

This file is kept for backward compatibility.
Import from governance.quality instead:

    from governance.quality import RuleQualityAnalyzer, analyze_rule_quality

Per RULE-012 DSP: Rule quality analysis documented
Per RULE-032: Files >300 lines MUST be modularized.
"""
import warnings

# Re-export from modular package for backward compatibility
from governance.quality import (
    IssueSeverity,
    IssueType,
    RuleIssue,
    RuleHealthReport,
    RuleQualityAnalyzer,
    analyze_rule_quality,
    get_rule_impact,
    find_rule_issues,
)

__all__ = [
    "IssueSeverity",
    "IssueType",
    "RuleIssue",
    "RuleHealthReport",
    "RuleQualityAnalyzer",
    "analyze_rule_quality",
    "get_rule_impact",
    "find_rule_issues",
]

# Emit deprecation warning on import
warnings.warn(
    "governance.rule_quality is deprecated. "
    "Use 'from governance.quality import RuleQualityAnalyzer' instead.",
    DeprecationWarning,
    stacklevel=2
)
