"""
Rule Conflict Detection (RULE-011).

Per RULE-011: Detect conflicting rules using inference.
"""

from typing import List, Tuple
from .models import RuleContext


def conflicting_priorities(rule1: RuleContext, rule2: RuleContext) -> bool:
    """
    Detect if two rules have conflicting priorities.

    Per RULE-011: Detect conflicting rules using inference.
    """
    # Same category but different priorities
    if rule1.category == rule2.category and rule1.priority != rule2.priority:
        return True
    return False


def find_rule_conflicts(rules: List[RuleContext]) -> List[Tuple[str, str, str]]:
    """Find all rule conflicts in a rule set."""
    conflicts = []
    for i, r1 in enumerate(rules):
        for r2 in rules[i+1:]:
            if conflicting_priorities(r1, r2):
                conflicts.append((r1.rule_id, r2.rule_id, f"Priority conflict in {r1.category}"))
    return conflicts
