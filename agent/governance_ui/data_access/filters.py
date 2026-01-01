"""
Filter & Transform Functions (GAP-FILE-006)
============================================
Pure functions for filtering and transforming data.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-006: Extracted from data_access.py

Created: 2024-12-28
"""

from typing import Dict, List, Optional


def filter_rules_by_status(rules: List[Dict], status: Optional[str]) -> List[Dict]:
    """Filter rules by status (pure function)."""
    if not status:
        return rules
    return [r for r in rules if r.get('status') == status]


def filter_rules_by_category(rules: List[Dict], category: Optional[str]) -> List[Dict]:
    """Filter rules by category (pure function)."""
    if not category:
        return rules
    return [r for r in rules if r.get('category') == category]


def filter_rules_by_search(rules: List[Dict], query: str) -> List[Dict]:
    """Filter rules by text search (pure function)."""
    if not query:
        return rules
    query_lower = query.lower()
    return [
        r for r in rules
        if query_lower in (r.get('title', '') or '').lower()
        or query_lower in (r.get('rule_id', '') or r.get('id', '')).lower()
        or query_lower in (r.get('directive', '') or '').lower()
    ]


def sort_rules(rules: List[Dict], column: str, ascending: bool = True) -> List[Dict]:
    """Sort rules by column (pure function, returns new list)."""
    return sorted(
        rules,
        key=lambda r: r.get(column, ''),
        reverse=not ascending
    )
