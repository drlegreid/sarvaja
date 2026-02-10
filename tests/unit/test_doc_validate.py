"""
Tests for document link validation (RD-DOCUMENT-MCP-SERVICE quick win).

Validates that doc_validate correctly identifies broken and valid links.

Created: 2026-02-11
"""

import pytest
import tempfile
from pathlib import Path


class TestDocumentValidation:
    """doc_validate MCP tool tests."""

    def test_validate_finds_valid_links(self, tmp_path):
        """Valid links should be counted correctly."""
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        # Create target file
        target = tmp_path / "target.md"
        target.write_text("# Target")
        # Create doc with link to target
        doc = tmp_path / "doc.md"
        doc.write_text(f"See [target](target.md) for details.")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 1
        assert result["valid"] == 1
        assert result["broken"] == 0

    def test_validate_finds_broken_links(self, tmp_path):
        """Broken links should be reported."""
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        doc = tmp_path / "doc.md"
        doc.write_text("See [missing](nonexistent.md) file.")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 1
        assert result["broken"] == 1
        assert len(result["broken_links"]) == 1
        assert result["broken_links"][0]["link"] == "nonexistent.md"

    def test_validate_skips_external_urls(self, tmp_path):
        """External URLs should be marked as valid (not checked)."""
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        doc = tmp_path / "doc.md"
        doc.write_text("Visit [docs](https://example.com/docs).")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 1
        assert result["valid"] == 1
        assert result["broken"] == 0

    def test_validate_handles_mixed_links(self, tmp_path):
        """Mix of valid, broken, and external links."""
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        target = tmp_path / "exists.md"
        target.write_text("# Exists")
        doc = tmp_path / "doc.md"
        doc.write_text(
            "- [valid](exists.md)\n"
            "- [broken](missing.md)\n"
            "- [external](https://example.com)\n"
        )
        result = validate_document_links(str(doc))
        assert result["total_links"] == 3
        assert result["valid"] == 2  # exists.md + external
        assert result["broken"] == 1  # missing.md

    def test_validate_nonexistent_file(self):
        """Non-existent document path should return error."""
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        result = validate_document_links("/nonexistent/path/doc.md")
        assert "error" in result

    def test_validate_empty_document(self, tmp_path):
        """Empty document should have zero links."""
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        doc = tmp_path / "empty.md"
        doc.write_text("")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 0
        assert result["broken"] == 0

    def test_validate_anchor_links_skipped(self, tmp_path):
        """Anchor-only links (#section) should be treated as external."""
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        doc = tmp_path / "doc.md"
        doc.write_text("See [section](#overview) below.")
        result = validate_document_links(str(doc))
        assert result["valid"] == 1
        assert result["broken"] == 0

    def test_validate_real_claude_md(self):
        """Validate CLAUDE.md as a real-world test."""
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        result = validate_document_links("CLAUDE.md")
        assert "error" not in result
        assert result["total_links"] > 0
