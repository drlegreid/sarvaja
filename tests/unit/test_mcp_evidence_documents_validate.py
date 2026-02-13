"""
Unit tests for Document Link Validation MCP Tool.

Batch 153: Tests for governance/mcp_tools/evidence/documents_validate.py
- _resolve_link: external, internal (relative, project root, search dirs)
- validate_document_links: full document validation
- doc_validate: MCP tool registration + delegation
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.mcp_tools.evidence.documents_validate import (
    _resolve_link,
    validate_document_links,
    register_validate_document_tools,
    _MARKDOWN_LINK,
)

_MOD = "governance.mcp_tools.evidence.documents_validate"


def _json_fmt(data):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_validate_document_tools(mcp)
    return mcp.tools


# ── _MARKDOWN_LINK regex ────────────────────────────────

class TestMarkdownLinkRegex:
    def test_finds_link(self):
        matches = _MARKDOWN_LINK.findall("[text](path.md)")
        assert len(matches) == 1
        assert matches[0] == ("text", "path.md")

    def test_multiple_links(self):
        text = "[a](b.md) and [c](d.md)"
        matches = _MARKDOWN_LINK.findall(text)
        assert len(matches) == 2

    def test_url_link(self):
        matches = _MARKDOWN_LINK.findall("[site](https://example.com)")
        assert matches[0] == ("site", "https://example.com")


# ── _resolve_link ───────────────────────────────────────

class TestResolveLink:
    def test_external_http(self, tmp_path):
        result = _resolve_link("https://example.com", tmp_path)
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_external_mailto(self, tmp_path):
        result = _resolve_link("mailto:test@test.com", tmp_path)
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_anchor_link(self, tmp_path):
        result = _resolve_link("#section", tmp_path)
        assert result["type"] == "external"
        assert result["exists"] is True

    def test_relative_found(self, tmp_path):
        target = tmp_path / "target.md"
        target.write_text("content")
        result = _resolve_link("target.md", tmp_path)
        assert result["type"] == "internal"
        assert result["exists"] is True

    def test_relative_not_found(self, tmp_path):
        result = _resolve_link("missing.md", tmp_path)
        assert result["type"] == "internal"
        assert result["exists"] is False

    def test_project_root_found(self, tmp_path):
        target = tmp_path / "docs" / "file.md"
        target.parent.mkdir(parents=True)
        target.write_text("content")
        with patch(f"{_MOD}._PROJECT_ROOT", tmp_path):
            result = _resolve_link("docs/file.md", tmp_path / "other")
        assert result["exists"] is True


# ── validate_document_links ─────────────────────────────

class TestValidateDocumentLinks:
    def test_file_not_found(self):
        result = validate_document_links("/nonexistent/file.md")
        assert "error" in result

    def test_no_links(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("No links here")
        result = validate_document_links(str(f))
        assert result["total_links"] == 0
        assert result["broken"] == 0

    def test_valid_links(self, tmp_path):
        target = tmp_path / "target.md"
        target.write_text("target content")
        doc = tmp_path / "doc.md"
        doc.write_text("[link](target.md)")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 1
        assert result["valid"] == 1
        assert result["broken"] == 0

    def test_broken_link(self, tmp_path):
        doc = tmp_path / "doc.md"
        doc.write_text("[broken](missing.md)")
        result = validate_document_links(str(doc))
        assert result["broken"] == 1
        assert len(result["broken_links"]) == 1

    def test_mixed_links(self, tmp_path):
        target = tmp_path / "exists.md"
        target.write_text("ok")
        doc = tmp_path / "doc.md"
        doc.write_text("[ok](exists.md) and [bad](missing.md) and [ext](https://example.com)")
        result = validate_document_links(str(doc))
        assert result["total_links"] == 3
        assert result["valid"] == 2  # exists.md + external
        assert result["broken"] == 1  # missing.md


# ── doc_validate MCP tool ──────────────────────────────

class TestDocValidateTool:
    def test_registration(self):
        tools = _register()
        assert "doc_validate" in tools

    def test_delegates_to_validate(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("[a](b.md)")
        tools = _register()
        with patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt):
            result = json.loads(tools["doc_validate"](path=str(doc)))
        assert result["total_links"] == 1
