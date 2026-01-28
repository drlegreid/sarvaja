"""
Rule Impact Analysis Module.

Per GAP-FILE-025: Extracted from quality/analyzer.py
Per DOC-SIZE-01-v1: Files under 400 lines

Provides impact analysis for rule modifications.

Created: 2026-01-14
"""

from typing import Dict, Any, Set


def calculate_rule_impact(
    rule_id: str,
    rule: Dict[str, Any],
    dependents_cache: Dict[str, Set[str]],
    all_rules: Dict[str, Dict]
) -> Dict[str, Any]:
    """
    Analyze impact if a rule is modified or deprecated.

    This is a pure function that calculates impact from provided data.

    Args:
        rule_id: The rule ID to analyze
        rule: Rule data dictionary
        dependents_cache: Mapping of rule_id -> set of rules that depend on it
        all_rules: All rules for context

    Returns:
        Dictionary with:
        - rule_id: The analyzed rule
        - rule_name: Rule name
        - direct_dependents: Rules that directly depend on this rule
        - all_affected_rules: All transitively affected rules
        - impact_score: 0-100 score
        - priority: Rule priority
        - category: Rule category
        - recommendation: Suggested approach
    """
    # Get direct and transitive dependents
    direct_dependents = dependents_cache.get(rule_id, set())

    # Get transitive dependents (rules that depend on dependents)
    all_dependents = set(direct_dependents)
    to_process = list(direct_dependents)

    while to_process:
        current = to_process.pop()
        for dep in dependents_cache.get(current, set()):
            if dep not in all_dependents:
                all_dependents.add(dep)
                to_process.append(dep)

    # Calculate impact score
    impact_score = 0

    # Base impact from priority
    priority_scores = {"CRITICAL": 40, "HIGH": 30, "MEDIUM": 20, "LOW": 10}
    impact_score += priority_scores.get(rule.get("priority", "MEDIUM"), 20)

    # Impact from dependents
    impact_score += min(len(all_dependents) * 10, 40)

    # Impact from category
    critical_categories = {"governance", "strategic", "architecture"}
    if rule.get("category") in critical_categories:
        impact_score += 20

    impact_score = min(impact_score, 100)

    # Recommendation based on score
    if impact_score >= 70:
        recommendation = "HIGH RISK: Requires thorough review and stakeholder approval before any changes"
    elif impact_score >= 40:
        recommendation = "MEDIUM RISK: Plan changes carefully, update all dependent rules"
    else:
        recommendation = "LOW RISK: Can proceed with standard change process"

    return {
        "rule_id": rule_id,
        "rule_name": rule.get("name", "Unknown"),
        "direct_dependents": list(direct_dependents),
        "all_affected_rules": list(all_dependents),
        "impact_score": impact_score,
        "priority": rule.get("priority"),
        "category": rule.get("category"),
        "recommendation": recommendation
    }


__all__ = ["calculate_rule_impact"]
