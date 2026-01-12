"""
Rule Quality Convenience Functions
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Convenience functions for MCP tools and direct usage.
"""

import json
from governance.quality.analyzer import RuleQualityAnalyzer


def analyze_rule_quality() -> str:
    """Run full analysis and return JSON report."""
    analyzer = RuleQualityAnalyzer()
    try:
        report = analyzer.analyze()
        return report.to_json()
    finally:
        analyzer.close()


def get_rule_impact(rule_id: str) -> str:
    """Get impact analysis for a specific rule."""
    analyzer = RuleQualityAnalyzer()
    try:
        impact = analyzer.get_rule_impact(rule_id)
        return json.dumps(impact, indent=2)
    finally:
        analyzer.close()


def find_rule_issues(issue_type: str = None) -> str:
    """Find specific type of rule issues."""
    analyzer = RuleQualityAnalyzer()
    try:
        if issue_type == "orphaned":
            issues = analyzer.find_orphaned_rules()
        elif issue_type == "shallow":
            issues = analyzer.find_shallow_rules()
        elif issue_type == "over_connected":
            issues = analyzer.find_over_connected_rules()
        elif issue_type == "circular":
            issues = analyzer.find_circular_dependencies()
        elif issue_type == "under_documented":
            issues = analyzer.find_under_documented_rules()
        else:
            report = analyzer.analyze()
            return report.to_json()

        return json.dumps([i.to_dict() for i in issues], indent=2)
    finally:
        analyzer.close()
