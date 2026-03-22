"""
Tests for EDS Heuristic Categories.

Per EPIC-GOV-TASKS-V2 Phase 9e: Expanded heuristic checklist
covering 5 gap categories missed by prior EDS gates.

TDD-first: these tests written BEFORE implementation.
Created: 2026-03-21
"""

import pytest


# ---------------------------------------------------------------------------
# TestEDSHeuristicCategories — category definitions
# ---------------------------------------------------------------------------

class TestEDSHeuristicCategories:
    """Each heuristic category has defined checklist items."""

    def test_data_model_category_exists(self):
        from governance.eds.heuristic_categories import HEURISTIC_CATEGORIES
        assert "DATA_MODEL" in HEURISTIC_CATEGORIES
        items = HEURISTIC_CATEGORIES["DATA_MODEL"]
        assert len(items) >= 3

    def test_ux_defaults_category_exists(self):
        from governance.eds.heuristic_categories import HEURISTIC_CATEGORIES
        assert "UX_DEFAULTS" in HEURISTIC_CATEGORIES
        items = HEURISTIC_CATEGORIES["UX_DEFAULTS"]
        assert len(items) >= 3

    def test_cross_nav_category_exists(self):
        from governance.eds.heuristic_categories import HEURISTIC_CATEGORIES
        assert "CROSS_NAV" in HEURISTIC_CATEGORIES
        items = HEURISTIC_CATEGORIES["CROSS_NAV"]
        assert len(items) >= 3

    def test_search_category_exists(self):
        from governance.eds.heuristic_categories import HEURISTIC_CATEGORIES
        assert "SEARCH" in HEURISTIC_CATEGORIES
        items = HEURISTIC_CATEGORIES["SEARCH"]
        assert len(items) >= 3

    def test_field_integrity_category_exists(self):
        from governance.eds.heuristic_categories import HEURISTIC_CATEGORIES
        assert "FIELD_INTEGRITY" in HEURISTIC_CATEGORIES
        items = HEURISTIC_CATEGORIES["FIELD_INTEGRITY"]
        assert len(items) >= 3


# ---------------------------------------------------------------------------
# TestEDSGapAnalysis — coverage analysis
# ---------------------------------------------------------------------------

class TestEDSGapAnalysis:
    """analyze_eds_coverage() identifies missing categories per scenario."""

    def test_crud_only_scenario_misses_all_categories(self):
        from governance.eds.heuristic_categories import analyze_eds_coverage
        scenario = {
            "name": "Create task via MCP",
            "categories_tested": ["CRUD"],
        }
        gaps = analyze_eds_coverage(scenario)
        assert "DATA_MODEL" in gaps
        assert "UX_DEFAULTS" in gaps
        assert "CROSS_NAV" in gaps
        assert "SEARCH" in gaps
        assert "FIELD_INTEGRITY" in gaps

    def test_full_coverage_returns_no_gaps(self):
        from governance.eds.heuristic_categories import analyze_eds_coverage
        scenario = {
            "name": "Full validation",
            "categories_tested": [
                "CRUD", "DATA_MODEL", "UX_DEFAULTS",
                "CROSS_NAV", "SEARCH", "FIELD_INTEGRITY",
            ],
        }
        gaps = analyze_eds_coverage(scenario)
        assert len(gaps) == 0

    def test_partial_coverage_returns_missing(self):
        from governance.eds.heuristic_categories import analyze_eds_coverage
        scenario = {
            "name": "Partial test",
            "categories_tested": ["CRUD", "DATA_MODEL", "SEARCH"],
        }
        gaps = analyze_eds_coverage(scenario)
        assert "UX_DEFAULTS" in gaps
        assert "CROSS_NAV" in gaps
        assert "FIELD_INTEGRITY" in gaps
        assert "DATA_MODEL" not in gaps
        assert "SEARCH" not in gaps

    def test_empty_categories_returns_all_gaps(self):
        from governance.eds.heuristic_categories import analyze_eds_coverage
        scenario = {"name": "No coverage", "categories_tested": []}
        gaps = analyze_eds_coverage(scenario)
        assert len(gaps) == 5

    def test_unknown_category_ignored(self):
        from governance.eds.heuristic_categories import analyze_eds_coverage
        scenario = {
            "name": "With unknown",
            "categories_tested": ["CRUD", "UNKNOWN_CAT", "DATA_MODEL"],
        }
        gaps = analyze_eds_coverage(scenario)
        assert "UNKNOWN_CAT" not in gaps
        assert "DATA_MODEL" not in gaps
        assert len(gaps) == 4  # Missing 4 of the 5 required categories
