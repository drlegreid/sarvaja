"""
Rule Scope Mechanism — GAP-RULE-SCOPE-001.

Allows rules to be scoped to specific components/directories
instead of applying globally.

Uses fnmatch glob patterns for path matching.
"""

from fnmatch import fnmatch
from typing import Dict, List, Optional, Any


def rule_applies_to_path(scope: Optional[List[str]], path: str) -> bool:
    """
    Check if a rule with the given scope applies to a file path.

    Args:
        scope: List of glob patterns (e.g. ["governance/**", "agent/**"]).
               None or [] means global (applies everywhere).
               ["*"] is explicit global.
        path: File path to check against.

    Returns:
        True if the rule applies to the path.
    """
    if not scope:
        return True

    for pattern in scope:
        if pattern == "*":
            return True
        if fnmatch(path, pattern):
            return True

    return False


def get_applicable_rules(
    rules: List[Dict[str, Any]], path: str
) -> List[Dict[str, Any]]:
    """
    Filter a list of rules to only those applicable to a given path.

    Args:
        rules: List of rule dicts, each optionally containing a "scope" key.
        path: File path to check against.

    Returns:
        List of rules whose scope matches the path.
    """
    return [
        rule for rule in rules
        if rule_applies_to_path(rule.get("scope"), path)
    ]
