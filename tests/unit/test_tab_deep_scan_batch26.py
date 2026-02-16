"""
Unit tests for Tab Deep Scan Batch 26 — XSS prevention + view safety.

Covers: BUG-UI-XSS-001 (render_markdown HTML escaping),
view component safety patterns.
Per TEST-E2E-01-v1: Tier 1 unit tests for security changes.
"""

import inspect
from governance.services.cc_session_ingestion import render_markdown


# ── BUG-UI-XSS-001: render_markdown HTML escaping ─────────────────────


class TestRenderMarkdownXSSPrevention:
    """render_markdown must escape HTML entities before markdown conversion."""

    def test_escapes_script_tags(self):
        """<script> tags must be escaped to prevent XSS."""
        result = render_markdown("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escapes_img_onerror(self):
        """<img onerror=...> must be escaped."""
        result = render_markdown('<img src=x onerror="alert(1)">')
        assert "<img" not in result
        assert "&lt;img" in result

    def test_escapes_iframe(self):
        """<iframe> tags must be escaped."""
        result = render_markdown("<iframe src='evil.com'></iframe>")
        assert "<iframe" not in result
        assert "&lt;iframe" in result

    def test_escapes_event_handlers(self):
        """HTML event handler attributes must be escaped (no raw HTML tags)."""
        result = render_markdown('<div onmouseover="alert(1)">hover</div>')
        # The raw <div> tag must be escaped — onmouseover becomes inert text
        assert "<div" not in result
        assert "&lt;div" in result

    def test_preserves_markdown_headers(self):
        """Markdown headers still render as HTML."""
        result = render_markdown("# Hello World")
        assert "<h1>" in result
        assert "Hello World" in result

    def test_preserves_markdown_bold(self):
        """Markdown bold still works after escaping."""
        result = render_markdown("**bold text**")
        assert "<strong>" in result
        assert "bold text" in result

    def test_preserves_markdown_italic(self):
        result = render_markdown("*italic text*")
        assert "<em>" in result

    def test_preserves_code_blocks(self):
        """Code blocks still render."""
        result = render_markdown("```python\nprint('hello')\n```")
        assert "<pre>" in result
        assert "<code" in result

    def test_preserves_inline_code(self):
        result = render_markdown("Use `pip install` to install")
        assert "<code>" in result
        assert "pip install" in result

    def test_preserves_list_items(self):
        result = render_markdown("- Item one\n- Item two")
        assert "<li>" in result

    def test_empty_input(self):
        assert render_markdown("") == ""
        assert render_markdown(None) == ""

    def test_plain_text_unchanged(self):
        result = render_markdown("Plain text without markup")
        assert "Plain text without markup" in result

    def test_has_bugfix_marker(self):
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion.render_markdown)
        assert "BUG-UI-XSS-001" in source

    def test_escapes_before_markdown(self):
        """HTML escaping must happen BEFORE markdown regex transforms."""
        from governance.services import cc_session_ingestion
        source = inspect.getsource(cc_session_ingestion.render_markdown)
        # html.escape must come before any re.sub call
        escape_pos = source.index("html_mod.escape")
        first_re_sub = source.index("re.sub")
        assert escape_pos < first_re_sub, \
            "HTML escaping must happen before regex transforms"

    def test_mixed_html_and_markdown(self):
        """Evidence with both HTML and markdown renders safely."""
        text = "# Session Report\n\n<script>alert('xss')</script>\n\n**Important** finding"
        result = render_markdown(text)
        assert "<h1>" in result
        assert "<strong>" in result
        assert "<script>" not in result
        assert "&lt;script&gt;" in result


# ── View component safety patterns ────────────────────────────────────


class TestViewSafetyPatterns:
    """View components must use safe rendering patterns."""

    def test_evidence_preview_uses_v_html(self):
        """evidence_preview uses v_html — confirm render_markdown is the source."""
        from agent.governance_ui.views.sessions import evidence_preview
        source = inspect.getsource(evidence_preview)
        assert "v_html" in source
        assert "session_evidence_html" in source

    def test_evidence_preview_has_loading_guard(self):
        """Evidence preview must not render while loading."""
        from agent.governance_ui.views.sessions import evidence_preview
        source = inspect.getsource(evidence_preview)
        assert "session_evidence_loading" in source

    def test_render_markdown_called_in_evidence_route(self):
        """The evidence/rendered route must use render_markdown."""
        from governance.routes.sessions import detail
        source = inspect.getsource(detail)
        assert "render_markdown" in source
