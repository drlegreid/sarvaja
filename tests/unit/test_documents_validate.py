"""
Unit tests for Document Link Validation.

Batch 123: Tests for governance/mcp_tools/evidence/documents_validate.py
- _resolve_link(): external, relative, project root, search dirs
- validate_document_links(): file not found, valid links, broken links
- register_validate_document_tools(): MCP registration
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


_MOD = "governance.mcp_tools.evidence.documents_validate"


# ── _resolve_link ───────────────────────────────────────────


class TestResolveLink:
    """Tests for _resolve_link path resolution."""

    def test_external_http_link(self):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        result = _resolve_link("https://example.com", Path("/tmp"))
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_external_https_link(self):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        result = _resolve_link("http://example.com", Path("/tmp"))
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_external_mailto(self):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        result = _resolve_link("mailto:test@test.com", Path("/tmp"))
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_anchor_link(self):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        result = _resolve_link("#section", Path("/tmp"))
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_relative_link_exists(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        (tmp_path / "target.md").write_text("content")
        result = _resolve_link("target.md", tmp_path)
        assert result["type"] == "internal"
        assert result["exists"] is True

    def test_relative_link_not_found(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        result = _resolve_link("nonexistent.md", tmp_path)
        assert result["type"] == "internal"
        assert result["exists"] is False

    def test_project_root_link(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        # Patch _PROJECT_ROOT to tmp_path
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "README.md").write_text("readme")
        with patch(f"{_MOD}._PROJECT_ROOT", tmp_path):
            result = _resolve_link("docs/README.md", Path("/other"))
            assert result["exists"] is True

    def test_search_dirs_fallback(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        # Create file in one of the search dirs
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "MY-RULE.md").write_text("rule")
        with patch(f"{_MOD}._SEARCH_DIRS", [rules_dir]), \
             patch(f"{_MOD}._PROJECT_ROOT", Path("/nonexistent")):
            result = _resolve_link("some/path/MY-RULE.md", Path("/other"))
            assert result["exists"] is True

    def test_returns_link_in_result(self):
        from governance.mcp_tools.evidence.documents_validate import _resolve_link
        result = _resolve_link("test.md", Path("/tmp"))
        assert result["link"] == "test.md"


# ── validate_document_links ─────────────────────────────────


class TestValidateDocumentLinks:
    """Tests for validate_document_links function."""

    def test_file_not_found(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        with patch(f"{_MOD}._PROJECT_ROOT", tmp_path):
            result = validate_document_links("nonexistent.md")
            assert "error" in result

    def test_absolute_path_file_not_found(self):
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        result = validate_document_links("/nonexistent/path/file.md")
        assert "error" in result

    def test_no_links(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        doc = tmp_path / "doc.md"
        doc.write_text("No links here, just text.")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 0
        assert result["valid"] == 0
        assert result["broken"] == 0

    def test_all_external_links(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        doc = tmp_path / "doc.md"
        doc.write_text("[Google](https://google.com)\n[Docs](http://docs.io)")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 2
        assert result["valid"] == 2
        assert result["broken"] == 0

    def test_valid_internal_link(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        (tmp_path / "other.md").write_text("target")
        doc = tmp_path / "doc.md"
        doc.write_text("[Other](other.md)")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 1
        assert result["valid"] == 1
        assert result["broken"] == 0

    def test_broken_internal_link(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        doc = tmp_path / "doc.md"
        doc.write_text("[Missing](missing.md)")
        with patch(f"{_MOD}._PROJECT_ROOT", tmp_path), \
             patch(f"{_MOD}._SEARCH_DIRS", []):
            result = validate_document_links(str(doc))
            assert result["broken"] == 1
            assert len(result["broken_links"]) == 1
            assert result["broken_links"][0]["link"] == "missing.md"

    def test_mixed_links(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        (tmp_path / "exists.md").write_text("yes")
        doc = tmp_path / "doc.md"
        doc.write_text(
            "[External](https://example.com)\n"
            "[Exists](exists.md)\n"
            "[Missing](gone.md)\n"
        )
        with patch(f"{_MOD}._PROJECT_ROOT", tmp_path), \
             patch(f"{_MOD}._SEARCH_DIRS", []):
            result = validate_document_links(str(doc))
            assert result["total_links"] == 3
            assert result["valid"] == 2
            assert result["broken"] == 1

    def test_relative_path_resolved_to_project_root(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import validate_document_links
        doc = tmp_path / "doc.md"
        doc.write_text("No links")
        with patch(f"{_MOD}._PROJECT_ROOT", tmp_path):
            result = validate_document_links("doc.md")
            assert result["file"] == str(tmp_path / "doc.md")


# ── register_validate_document_tools ────────────────────────


class TestRegisterValidateTools:
    """Tests for MCP tool registration."""

    def test_registration(self):
        from governance.mcp_tools.evidence.documents_validate import register_validate_document_tools
        mcp = MagicMock()
        tools = {}

        def tool_decorator():
            def wrapper(fn):
                tools[fn.__name__] = fn
                return fn
            return wrapper

        mcp.tool = tool_decorator
        register_validate_document_tools(mcp)
        assert "doc_validate" in tools

    def test_doc_validate_calls_validate(self, tmp_path):
        from governance.mcp_tools.evidence.documents_validate import register_validate_document_tools
        mcp = MagicMock()
        tools = {}

        def tool_decorator():
            def wrapper(fn):
                tools[fn.__name__] = fn
                return fn
            return wrapper

        mcp.tool = tool_decorator
        register_validate_document_tools(mcp)

        doc = tmp_path / "test.md"
        doc.write_text("[Link](https://example.com)")
        with patch(f"{_MOD}.format_mcp_result", side_effect=lambda d: json.dumps(d)):
            result = tools["doc_validate"](str(doc))
            data = json.loads(result)
            assert data["total_links"] == 1
