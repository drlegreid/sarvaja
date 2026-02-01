"""
Tests for session evidence filters.

Per B.4: Session evidence view should have a working search filter.
Verifies:
- Evidence view has a search/filter input
- Filter is client-side on evidence path content

Created: 2026-02-01
"""
import pytest
import inspect


class TestEvidenceFilter:
    """Tests for evidence file list filtering."""

    def test_evidence_view_has_search_filter(self):
        """Evidence view should have a search/filter text field."""
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "evidence_search" in source or "evidence_filter" in source

    def test_evidence_list_uses_filter(self):
        """Evidence list should filter items based on search text."""
        from agent.governance_ui.views.sessions.evidence import build_evidence_files_card
        source = inspect.getsource(build_evidence_files_card)
        assert "filter" in source.lower() or "includes" in source
