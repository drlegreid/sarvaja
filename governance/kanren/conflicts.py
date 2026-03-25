"""
Rule Conflict Detection (RULE-011).

Per RULE-011: Detect conflicting rules using inference.
Per EPIC-GOV-RULES-V3 P5: scope_conflict, lifecycle_conflict, expanded find_rule_conflicts.

Created: 2026-01-04
Updated: 2026-03-25 - P5: scope_conflict, lifecycle_conflict
"""

from typing import Dict, List, Tuple
from .models import RuleContext


def conflicting_priorities(rule1: RuleContext, rule2: RuleContext) -> bool:
    """
    Detect if two rules have conflicting priorities.

    Per RULE-011: Detect conflicting rules using inference.
    """
    if rule1.category == rule2.category and rule1.priority != rule2.priority:
        return True
    return False


def scope_conflict(rule1: RuleContext, rule2: RuleContext) -> bool:
    """Detect overlapping governance scope — two ACTIVE rules in same category with different priorities.

    This indicates competing directives where one rule demands a higher
    priority than another in the same governance domain.

    Args:
        rule1: First rule context
        rule2: Second rule context

    Returns:
        True if scope conflict detected
    """
    if rule1.rule_id == rule2.rule_id:
        return False
    return (
        rule1.category == rule2.category
        and rule1.status == "ACTIVE"
        and rule2.status == "ACTIVE"
        and rule1.priority != rule2.priority
    )


def lifecycle_conflict(
    rule1: RuleContext,
    rule2: RuleContext,
    dependencies: Dict[str, List[str]],
) -> bool:
    """Detect broken dependency chain — ACTIVE rule depends on DEPRECATED rule.

    Args:
        rule1: First rule context
        rule2: Second rule context
        dependencies: Map of rule_id -> list of dependency rule_ids

    Returns:
        True if lifecycle conflict detected
    """
    # Active depends on deprecated
    if rule1.status == "ACTIVE" and rule2.status == "DEPRECATED":
        if rule2.rule_id in dependencies.get(rule1.rule_id, []):
            return True
    # Reverse: deprecated is depended upon by active
    if rule2.status == "ACTIVE" and rule1.status == "DEPRECATED":
        if rule1.rule_id in dependencies.get(rule2.rule_id, []):
            return True
    return False


def find_rule_conflicts(
    rules: List[RuleContext],
    dependencies: Dict[str, List[str]] = None,
) -> List[Tuple[str, str, str]]:
    """Find all rule conflicts: scope overlaps and lifecycle breaks.

    Args:
        rules: List of rule contexts to analyze
        dependencies: Optional dependency graph (rule_id -> dep_ids)

    Returns:
        List of (rule1_id, rule2_id, description) conflict tuples
    """
    conflicts: List[Tuple[str, str, str]] = []
    deps = dependencies or {}

    for i, r1 in enumerate(rules):
        for r2 in rules[i + 1:]:
            if scope_conflict(r1, r2):
                conflicts.append((
                    r1.rule_id,
                    r2.rule_id,
                    f"Scope conflict in {r1.category}: {r1.priority} vs {r2.priority}",
                ))
            if lifecycle_conflict(r1, r2, deps):
                active = r1 if r1.status == "ACTIVE" else r2
                deprecated = r2 if r1.status == "ACTIVE" else r1
                conflicts.append((
                    active.rule_id,
                    deprecated.rule_id,
                    f"Lifecycle conflict: {active.rule_id} depends on DEPRECATED {deprecated.rule_id}",
                ))

    return conflicts
