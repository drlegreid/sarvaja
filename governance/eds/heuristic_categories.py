"""
EDS Heuristic Categories.

Per EPIC-GOV-TASKS-V2 Phase 9e: Expanded heuristic checklist
covering 5 gap categories that CRUD-only EDS specs miss.

Root cause: Phases 6/6c/9b EDS gates validated CRUD mechanics
but did NOT catch data model completeness, UX defaults,
cross-entity navigation, search behavior, or field integrity.

Created: 2026-03-21
"""

# The 5 required heuristic categories for EDS completeness.
# Each category maps to a list of checklist items.
HEURISTIC_CATEGORIES: dict[str, list[str]] = {
    "DATA_MODEL": [
        "All schema attributes present in API response",
        "New fields propagate through all layers (TypeDB -> service -> route -> UI)",
        "Optional fields have sensible defaults",
        "Enum/Literal values consistent across layers",
        "Auto-generated fields populate correctly",
    ],
    "UX_DEFAULTS": [
        "Default sort order is user-friendly (newest first)",
        "Filter dropdowns match API-accepted values",
        "Empty states have meaningful messages",
        "Column widths appropriate for data content",
    ],
    "CROSS_NAV": [
        "Linked entities are clickable (not just displayed)",
        "Navigation preserves back-button context",
        "Bidirectional navigation works (A->B and B->A)",
        "Navigation to missing entities shows clear error",
    ],
    "SEARCH": [
        "Search is server-side (not client-side page filter)",
        "Search respects pagination (correct total count)",
        "Structured search syntax works for power users",
    ],
    "FIELD_INTEGRITY": [
        "No null fields that should have defaults",
        "No embedded metadata in wrong fields ([Priority: X] in description)",
        "Timestamp ordering valid (completed >= created)",
        "Status values normalized (uppercase)",
    ],
}

# All required category names
REQUIRED_CATEGORIES = frozenset(HEURISTIC_CATEGORIES.keys())


def analyze_eds_coverage(scenario: dict) -> list[str]:
    """Identify which heuristic categories a scenario does NOT cover.

    Args:
        scenario: Dict with 'name' and 'categories_tested' (list of strings).

    Returns:
        List of missing category names from REQUIRED_CATEGORIES.
    """
    tested = set(scenario.get("categories_tested", []))
    return sorted(REQUIRED_CATEGORIES - tested)
