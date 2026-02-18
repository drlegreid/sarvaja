"""Deep scan batch 178: Controllers layer.

Batch 178 findings: 25 total, 2 confirmed fixes, 23 rejected/deferred.
- BUG-S-03: is_loading stuck True on early return in submit_session_form.
- BUG-INGEST-SES-002: XSS via javascript: protocol in render_markdown links.
"""
import pytest
from pathlib import Path


# ── Session form is_loading defense ──────────────


class TestSessionFormIsLoadingDefense:
    """Verify is_loading is reset on all exit paths in submit_session_form."""

    def test_early_return_resets_is_loading(self):
        """Guard return for missing selected_session resets is_loading."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/sessions.py").read_text()
        start = src.index("def submit_session_form")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        # Find the selected_session guard
        guard_start = func.index("No session selected for editing")
        # Within 5 lines after guard, is_loading must be set False
        guard_block = func[guard_start:guard_start + 300]
        assert "is_loading = False" in guard_block

    def test_exception_handler_resets_is_loading(self):
        """Exception handler in submit_session_form resets is_loading."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/sessions.py").read_text()
        start = src.index("def submit_session_form")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        # Find the "Save session failed" except block (specific to submit_session_form)
        except_idx = func.index("Save session failed")
        except_block = func[except_idx - 100:except_idx + 200]
        assert "is_loading = False" in except_block

    def test_success_path_resets_is_loading(self):
        """Normal success path in submit_session_form resets is_loading."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/controllers/sessions.py").read_text()
        start = src.index("def submit_session_form")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        # Count all is_loading = False occurrences — should be at least 3
        # (guard return, success path, exception handler)
        count = func.count("is_loading = False")
        assert count >= 3, f"Expected at least 3 is_loading resets, found {count}"


# ── Render markdown XSS defense ──────────────


class TestRenderMarkdownXSSDefense:
    """Verify render_markdown blocks javascript: URIs."""

    def test_javascript_uri_blocked(self):
        """render_markdown strips javascript: protocol links."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("[click](javascript:alert(1))")
        assert "javascript:" not in result
        assert "click" in result  # Text preserved

    def test_javascript_uri_case_insensitive(self):
        """render_markdown blocks JavaScript: (mixed case)."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("[evil](JavaScript:void(0))")
        assert "javascript:" not in result.lower()

    def test_normal_links_preserved(self):
        """render_markdown preserves normal http/https links."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("[docs](https://example.com)")
        assert 'href="https://example.com"' in result
        assert "docs" in result

    def test_html_entities_escaped(self):
        """render_markdown escapes HTML entities (existing XSS defense)."""
        from governance.services.cc_session_ingestion import render_markdown
        result = render_markdown("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_empty_input(self):
        """render_markdown handles empty string."""
        from governance.services.cc_session_ingestion import render_markdown
        assert render_markdown("") == ""
        assert render_markdown(None) == ""


# ── Dashboard data loader type safety defense ──────────────


class TestDashboardDataLoaderDefense:
    """Verify dashboard data loader handles paginated API responses."""

    def test_sessions_loader_checks_dict_with_items(self):
        """Sessions loader checks for dict with 'items' key."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/dashboard_data_loader.py").read_text()
        # Should check isinstance(data, dict) and "items" in data
        assert 'isinstance(data, dict) and "items" in data' in src

    def test_compute_session_metrics_importable(self):
        """compute_session_metrics function is importable."""
        from agent.governance_ui.utils import compute_session_metrics
        assert callable(compute_session_metrics)

    def test_compute_session_duration_importable(self):
        """compute_session_duration function is importable."""
        from agent.governance_ui.utils import compute_session_duration
        assert callable(compute_session_duration)
