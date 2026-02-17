"""
Rule Scope Mechanism — GAP-RULE-SCOPE-001.

Allows rules to be scoped to specific components/directories
instead of applying globally.

Uses fnmatch glob patterns for path matching.
"""

import os.path
from fnmatch import fnmatch
from pathlib import PurePath
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

    # BUG-287-RSC-001: Guard against None/empty path
    if not isinstance(path, str) or not path:
        return False

    # BUG-348-SCO-001: Normalize path to collapse '..' and prevent traversal bypass
    # (e.g. 'governance/../../admin/secrets.py' matching 'governance/**')
    # os.path.normpath resolves '..' unlike PurePath.as_posix()
    path = os.path.normpath(path).replace(os.sep, "/")
    # Strip leading '../' sequences after normalization
    while path.startswith("../"):
        path = path[3:]

    for pattern in scope:
        if pattern == "*":
            return True
        if fnmatch(path, pattern):
            return True
        # BUG-RULE-SCOPE-DOUBLESTAR-001: fnmatch doesn't support **
        if "**" in pattern:
            try:
                if PurePath(path).match(pattern):
                    return True
            except (ValueError, TypeError):
                pass

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
