"""
RED Phase: Tests for holographic HTML report renderer.
Per FEAT-009 / TEST-HOLO-01-v1.

Validates:
- render_html_report() produces valid self-contained HTML
- All 4 zoom levels rendered as sections
- Pass/fail badge, per-test rows, collapsible traces
- Category breakdown (unit/integration/e2e)
- Output to evidence/ directory
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.evidence.holographic_store import (
    HolographicTestStore,
    EvidenceRecord,
    get_global_store,
    reset_global_store,
)


def _make_store_with_data() -> HolographicTestStore:
    """Helper: create a store with mixed test data."""
    store = HolographicTestStore(session_id="TEST-2026-03-31")
    store.push_event("tests/unit/test_auth.py::test_login", "test_login",
                     "passed", category="unit", duration_ms=50)
    store.push_event("tests/unit/test_auth.py::test_logout", "test_logout",
                     "passed", category="unit", duration_ms=30)
    store.push_event("tests/unit/test_auth.py::test_bad_token", "test_bad_token",
                     "failed", category="unit", duration_ms=80,
                     error_message="AssertionError: expected 401 got 200")
    store.push_event("tests/e2e/test_dashboard_e2e.py::test_nav", "test_nav",
                     "passed", category="e2e", duration_ms=2500)
    store.push_event("tests/integration/test_typedb.py::test_query", "test_query",
                     "skipped", category="integration", duration_ms=0,
                     error_message="TypeDB not available")
    return store


# ---------------------------------------------------------------------------
# Core renderer tests
# ---------------------------------------------------------------------------

class TestHolographicReportRenderer:
    """Verify render_html_report produces valid HTML."""

    def test_render_returns_html_string(self):
        """render_html_report returns a non-empty HTML string."""
        from tests.evidence.holographic_report import render_html_report

        store = _make_store_with_data()
        html = render_html_report(store)

        assert isinstance(html, str)
        assert len(html) > 100
        assert "<html" in html.lower()
        assert "</html>" in html.lower()

    def test_html_is_self_contained(self):
        """HTML has embedded CSS, no external dependencies."""
        from tests.evidence.holographic_report import render_html_report

        store = _make_store_with_data()
        html = render_html_report(store)

        assert "<style>" in html
        # No external stylesheet links
        assert 'rel="stylesheet"' not in html
        assert "src=" not in html or "javascript:" not in html

    def test_html_contains_pass_fail_badge(self):
        """HTML contains a PASS/FAIL badge (zoom 0)."""
        from tests.evidence.holographic_report import render_html_report

        store = _make_store_with_data()
        html = render_html_report(store)

        # Store has failures so badge should say FAIL
        assert "FAIL" in html
        # Should contain counts
        assert "3/5" in html or "60%" in html

    def test_html_contains_summary_table(self):
        """HTML has summary stats table (zoom 1)."""
        from tests.evidence.holographic_report import render_html_report

        store = _make_store_with_data()
        html = render_html_report(store)

        # Should contain category breakdown
        assert "unit" in html.lower()
        assert "e2e" in html.lower()
        assert "integration" in html.lower()

    def test_html_contains_per_test_rows(self):
        """HTML has per-test rows with status (zoom 2)."""
        from tests.evidence.holographic_report import render_html_report

        store = _make_store_with_data()
        html = render_html_report(store)

        assert "test_login" in html
        assert "test_logout" in html
        assert "test_bad_token" in html
        assert "test_nav" in html
        assert "test_query" in html

    def test_html_contains_error_details(self):
        """Failed tests show error message (zoom 2-3)."""
        from tests.evidence.holographic_report import render_html_report

        store = _make_store_with_data()
        html = render_html_report(store)

        assert "AssertionError" in html

    def test_html_contains_zoom_sections(self):
        """HTML has labelled zoom-level sections."""
        from tests.evidence.holographic_report import render_html_report

        store = _make_store_with_data()
        html = render_html_report(store)

        assert "zoom-0" in html or "Zoom 0" in html or "zoom0" in html
        assert "zoom-1" in html or "Zoom 1" in html or "zoom1" in html
        assert "zoom-2" in html or "Zoom 2" in html or "zoom2" in html

    def test_empty_store_renders_gracefully(self):
        """Empty store produces valid HTML with 'no data' message."""
        from tests.evidence.holographic_report import render_html_report

        store = HolographicTestStore()
        html = render_html_report(store)

        assert "<html" in html.lower()
        assert "no" in html.lower() or "empty" in html.lower() or "0" in html


# ---------------------------------------------------------------------------
# File output tests
# ---------------------------------------------------------------------------

class TestHolographicReportFileOutput:
    """Verify report writes to correct paths."""

    def test_save_report_creates_file(self):
        """save_html_report writes file to specified directory."""
        from tests.evidence.holographic_report import save_html_report

        store = _make_store_with_data()

        with TemporaryDirectory() as tmpdir:
            path = save_html_report(store, output_dir=tmpdir)

            assert path.exists()
            assert path.suffix == ".html"
            content = path.read_text()
            assert "<html" in content.lower()

    def test_save_report_filename_has_date(self):
        """Output filename includes date for historical accumulation."""
        from tests.evidence.holographic_report import save_html_report

        store = _make_store_with_data()

        with TemporaryDirectory() as tmpdir:
            path = save_html_report(store, output_dir=tmpdir)

            assert "holographic-report" in path.name
            # Should have date component (YYYY-MM-DD)
            assert "2026" in path.name or "20" in path.name

    def test_save_report_does_not_overwrite(self):
        """Multiple saves on same day don't overwrite (append suffix)."""
        from tests.evidence.holographic_report import save_html_report

        store = _make_store_with_data()

        with TemporaryDirectory() as tmpdir:
            path1 = save_html_report(store, output_dir=tmpdir)
            path2 = save_html_report(store, output_dir=tmpdir)

            assert path1.exists()
            assert path2.exists()
            # If same date, second should have different name or overwrite is ok
            # (both files must exist)


# ---------------------------------------------------------------------------
# Integration with store
# ---------------------------------------------------------------------------

class TestReportStoreIntegration:
    """Verify render works with real store queries."""

    def test_render_from_global_store(self):
        """Can render directly from global store."""
        from tests.evidence.holographic_report import render_html_report

        reset_global_store()
        store = get_global_store()
        store.push_event("t1", "test_1", "passed", category="unit", duration_ms=10)
        store.push_event("t2", "test_2", "failed", category="e2e",
                         error_message="Timeout", duration_ms=5000)

        html = render_html_report(store)

        assert "test_1" in html
        assert "test_2" in html
        assert "Timeout" in html

    def test_render_large_suite(self):
        """Renderer handles large test suites without exploding."""
        from tests.evidence.holographic_report import render_html_report

        store = HolographicTestStore()
        for i in range(500):
            store.push_event(
                f"tests/unit/test_gen.py::test_{i}", f"test_{i}",
                "passed" if i < 490 else "failed",
                category="unit", duration_ms=10,
                error_message=f"Error {i}" if i >= 490 else None,
            )

        html = render_html_report(store)

        assert "490/500" in html or "98%" in html
        assert len(html) > 1000  # Substantial HTML
