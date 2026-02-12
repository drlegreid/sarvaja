"""
Unit tests for Document Link Validation.

Per DOC-SIZE-01-v1: Tests for governance/mcp_tools/evidence/documents_validate.py.
Tests: _resolve_link, validate_document_links, register_validate_document_tools.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path

from governance.mcp_tools.evidence.documents_validate import (
    _resolve_link,
    validate_document_links,
)


# ── _resolve_link ──────────────────────────────────────


class TestResolveLink:
    def test_external_http(self):
        result = _resolve_link("https://example.com", Path("/tmp"))
        assert result["type"] == "external"
        assert result["exists"] is True
        assert result["resolved"] == "https://example.com"

    def test_external_https(self):
        result = _resolve_link("http://example.com", Path("/tmp"))
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_external_mailto(self):
        result = _resolve_link("mailto:x@y.com", Path("/tmp"))
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_external_anchor(self):
        result = _resolve_link("#section", Path("/tmp"))
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_internal_relative_exists(self, tmp_path):
        (tmp_path / "target.md").write_text("# Target")
        result = _resolve_link("target.md", tmp_path)
        assert result["type"] == "internal"
        assert result["exists"] is True
        assert "target.md" in result["resolved"]

    def test_internal_relative_not_found(self, tmp_path):
        result = _resolve_link("nonexistent.md", tmp_path)
        assert result["type"] == "internal"
        assert result["exists"] is False

    @patch("governance.mcp_tools.evidence.documents_validate._PROJECT_ROOT")
    def test_project_root_fallback(self, mock_root, tmp_path):
        (tmp_path / "README.md").write_text("# README")
        mock_root.__truediv__ = lambda self, p: tmp_path / p
        mock_root.resolve = MagicMock(return_value=tmp_path)
        # Context dir has no file, but project root does
        empty_dir = tmp_path / "sub"
        empty_dir.mkdir()
        result = _resolve_link("README.md", empty_dir)
        # Should find via relative or project root
        assert result["type"] == "internal"

    @patch("governance.mcp_tools.evidence.documents_validate._SEARCH_DIRS")
    def test_search_dirs_fallback(self, mock_dirs, tmp_path):
        search_dir = tmp_path / "docs"
        search_dir.mkdir()
        (search_dir / "found.md").write_text("# Found")
        mock_dirs.__iter__ = lambda self: iter([search_dir])

        empty = tmp_path / "empty"
        empty.mkdir()
        # Link won't resolve relative or project root
        with patch("governance.mcp_tools.evidence.documents_validate._PROJECT_ROOT",
                   empty):
            result = _resolve_link("found.md", empty)
        assert result["exists"] is True


# ── validate_document_links ────────────────────────────


class TestValidateDocumentLinks:
    def test_file_not_found(self, tmp_path):
        result = validate_document_links(str(tmp_path / "nonexistent.md"))
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_no_links(self, tmp_path):
        doc = tmp_path / "empty.md"
        doc.write_text("# No Links Here\n\nJust text.")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 0
        assert result["valid"] == 0
        assert result["broken"] == 0
        assert result["broken_links"] == []

    def test_all_external_links(self, tmp_path):
        doc = tmp_path / "external.md"
        doc.write_text("[Google](https://google.com)\n[Mail](mailto:a@b.com)")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 2
        assert result["valid"] == 2
        assert result["broken"] == 0

    def test_valid_internal_link(self, tmp_path):
        (tmp_path / "target.md").write_text("# Target")
        doc = tmp_path / "source.md"
        doc.write_text("[Target](target.md)")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 1
        assert result["valid"] == 1
        assert result["broken"] == 0

    def test_broken_internal_link(self, tmp_path):
        doc = tmp_path / "source.md"
        doc.write_text("[Missing](missing.md)")
        with patch("governance.mcp_tools.evidence.documents_validate._PROJECT_ROOT",
                   tmp_path), \
             patch("governance.mcp_tools.evidence.documents_validate._SEARCH_DIRS", []):
            result = validate_document_links(str(doc))
        assert result["broken"] == 1
        assert len(result["broken_links"]) == 1
        assert result["broken_links"][0]["text"] == "Missing"

    def test_mixed_links(self, tmp_path):
        (tmp_path / "exists.md").write_text("# Exists")
        doc = tmp_path / "mixed.md"
        doc.write_text(
            "[Ext](https://example.com)\n"
            "[Valid](exists.md)\n"
            "[Broken](nope.md)"
        )
        with patch("governance.mcp_tools.evidence.documents_validate._PROJECT_ROOT",
                   tmp_path), \
             patch("governance.mcp_tools.evidence.documents_validate._SEARCH_DIRS", []):
            result = validate_document_links(str(doc))
        assert result["total_links"] == 3
        assert result["valid"] == 2
        assert result["broken"] == 1

    def test_relative_path_resolution(self, tmp_path):
        with patch("governance.mcp_tools.evidence.documents_validate._PROJECT_ROOT",
                   tmp_path):
            doc = tmp_path / "doc.md"
            doc.write_text("# Empty")
            result = validate_document_links(str(doc))
        assert result["file"] == str(doc)


# ── register_validate_document_tools ───────────────────


class TestRegisterTools:
    def test_registers_doc_validate(self):
        from governance.mcp_tools.evidence.documents_validate import (
            register_validate_document_tools,
        )
        mcp = MagicMock()
        mcp.tool.return_value = lambda fn: fn
        register_validate_document_tools(mcp)
        mcp.tool.assert_called_once()
