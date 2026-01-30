"""
Tests for evidence grid view.

Per PLAN-UI-OVERHAUL-001 Task 1.4: Evidence Grid.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestEvidenceGrid:
    """Verify evidence search uses data table for results."""

    def test_evidence_uses_data_table(self):
        """Evidence search should use VDataTable for results."""
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert 'VDataTable' in source, (
            "Evidence search should use VDataTable for grid display"
        )

    def test_evidence_grid_has_columns(self):
        """Evidence grid should have relevant columns."""
        from agent.governance_ui.views import search_view
        source = inspect.getsource(search_view)
        assert 'headers' in source, (
            "Evidence grid should define column headers"
        )
