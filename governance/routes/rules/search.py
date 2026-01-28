"""
Rules Search Module.

Per GAP-UI-SEARCH-001: Server-side rule search.
Per DOC-SIZE-01-v1: Single responsibility module.

Provides search filtering for rules to bypass pagination limitation.
Client-side search is blocked when rules exceed default page size.
"""

from typing import List, Any, Optional


def filter_rules_by_search(rules: List[Any], search: Optional[str]) -> List[Any]:
    """
    Filter rules by search query across id, name, and directive.

    Args:
        rules: List of rule objects with id, name, directive attributes
        search: Search query string (case-insensitive)

    Returns:
        Filtered list of rules matching the search query.
        Returns all rules if search is empty or None.
    """
    if not search:
        return rules

    search_lower = search.lower()
    return [
        rule for rule in rules
        if (
            (rule.id and search_lower in rule.id.lower()) or
            (rule.name and search_lower in rule.name.lower()) or
            (rule.directive and search_lower in rule.directive.lower())
        )
    ]
