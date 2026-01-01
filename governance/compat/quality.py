"""
Rule Quality Analyzer Exports (GAP-FILE-007)
=============================================
Rule quality backward compatibility exports for test imports.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-007: Extracted from mcp_server.py

Created: 2024-12-28
"""

import json

# Try to import rule quality analyzer
try:
    from governance.rule_quality import (
        RuleQualityAnalyzer,
        analyze_rule_quality as _analyze_rule_quality,
        get_rule_impact as _get_rule_impact,
        find_rule_issues as _find_rule_issues
    )
    _RULE_QUALITY_AVAILABLE = True
except ImportError:
    _RULE_QUALITY_AVAILABLE = False


def governance_analyze_rules():
    """Analyze rule quality (backward compat export)."""
    if not _RULE_QUALITY_AVAILABLE:
        return json.dumps({"error": "RuleQualityAnalyzer not available"})
    return _analyze_rule_quality()


def governance_rule_impact(rule_id):
    """Get rule impact (backward compat export)."""
    if not _RULE_QUALITY_AVAILABLE:
        return json.dumps({"error": "RuleQualityAnalyzer not available"})
    return _get_rule_impact(rule_id)


def governance_find_issues(issue_type=None):
    """Find rule issues (backward compat export)."""
    if not _RULE_QUALITY_AVAILABLE:
        return json.dumps({"error": "RuleQualityAnalyzer not available"})
    return _find_rule_issues(issue_type)
