"""
Unit tests for Document Link Extraction MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/evidence/documents_links.py module.
Tests: doc_links_extract, doc_link_resolve.
"""

import json
import pytest
from unittest.mock import patch
from pathlib import Path

from governance.mcp_tools.evidence.documents_links import register_link_document_tools


def _json_format(data, **kwargs):
    """Force JSON output for test assertions."""
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    """Captures tools registered via @mcp.tool()."""

    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        if callable(name):
            self.tools[name.__name__] = name
            return name

        def decorator(fn):
            key = name if name else fn.__name__
            self.tools[key] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_link_document_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _force_json_output():
    """Patch format_mcp_result to return JSON for all tests."""
    with patch(
        "governance.mcp_tools.evidence.documents_links.format_mcp_result",
        side_effect=_json_format,
    ):
        yield


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestRegistration:
    """Tests for tool registration."""

    def test_registers_extract(self):
        mcp = _register()
        assert "doc_links_extract" in mcp.tools

    def test_registers_resolve(self):
        mcp = _register()
        assert "doc_link_resolve" in mcp.tools

    def test_total_tools(self):
        mcp = _register()
        assert len(mcp.tools) == 2


# ---------------------------------------------------------------------------
# doc_links_extract
# ---------------------------------------------------------------------------
class TestDocLinksExtract:
    """Tests for doc_links_extract tool."""

    def test_extracts_markdown_links(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("[Click here](https://example.com)\n[Local](./file.md)")
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        links = result["links"]["markdown"]
        assert len(links) == 2

    def test_classifies_external_links(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("[Ext](https://example.com)")
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        assert result["links"]["markdown"][0]["type"] == "external"

    def test_classifies_internal_links(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("[Int](./other.md)")
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        assert result["links"]["markdown"][0]["type"] == "internal"

    def test_extracts_legacy_rule_refs(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("See RULE-001 and RULE-012 for details.")
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        assert len(result["links"]["rules_legacy"]) == 2
        assert result["links"]["rules_legacy"][0]["rule_id"] == "RULE-001"

    def test_extracts_semantic_rule_refs(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("Per DOC-SIZE-01-v1 and TEST-GUARD-01-v1.")
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        assert len(result["links"]["rules_semantic"]) == 2

    def test_extracts_gap_refs(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("Fix GAP-MCP-001 and GAP-UI-002.")
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        assert len(result["links"]["gaps"]) == 2
        assert result["links"]["gaps"][0]["gap_id"] == "GAP-MCP-001"

    def test_extracts_task_refs(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("Tasks P10.1, P11.5, and RD-001 are pending.")
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        assert len(result["links"]["tasks"]) == 3

    def test_summary_counts(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text(
            "[Ext](https://x.com)\n"
            "[Int](./f.md)\n"
            "RULE-001 DOC-SIZE-01-v1\n"
            "GAP-UI-001\n"
            "P10.1\n"
        )
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        s = result["summary"]
        assert s["markdown_links"] == 2
        assert s["external_links"] == 1
        assert s["internal_links"] == 1
        assert s["rule_refs"] == 2
        assert s["gap_refs"] == 1
        assert s["task_refs"] == 1

    def test_nonexistent_file_error(self):
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"]("/nonexistent/file.md"))
        assert "error" in result

    def test_empty_document(self, tmp_path):
        doc = tmp_path / "empty.md"
        doc.write_text("")
        mcp = _register()
        result = json.loads(mcp.tools["doc_links_extract"](str(doc)))
        assert result["summary"]["markdown_links"] == 0
        assert result["summary"]["rule_refs"] == 0


# ---------------------------------------------------------------------------
# doc_link_resolve
# ---------------------------------------------------------------------------
class TestDocLinkResolve:
    """Tests for doc_link_resolve tool."""

    def test_semantic_rule_with_leaf_file(self, tmp_path):
        leaf_dir = tmp_path / "leaf"
        leaf_dir.mkdir()
        leaf_file = leaf_dir / "DOC-SIZE-01-v1.md"
        leaf_file.write_text("# Rule content")

        with patch("governance.mcp_tools.evidence.documents_links.RULES_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_link_resolve"]("DOC-SIZE-01-v1"))
            assert result["type"] == "semantic_rule_id"
            assert result["exists"] is True

    def test_gap_id_resolve(self, tmp_path):
        gap_index = tmp_path / "GAP-INDEX.md"
        gap_index.write_text("# Gap Index\nGAP-MCP-001")

        with patch("governance.mcp_tools.evidence.documents_links.GAPS_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_link_resolve"]("GAP-MCP-001"))
            assert result["type"] == "gap_id"
            assert result["exists"] is True

    def test_absolute_path_resolve(self, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("content")
        mcp = _register()
        result = json.loads(mcp.tools["doc_link_resolve"](str(test_file)))
        assert result["type"] == "path"
        assert result["exists"] is True

    def test_absolute_path_nonexistent(self):
        mcp = _register()
        result = json.loads(mcp.tools["doc_link_resolve"]("/nonexistent/file.md"))
        assert result["type"] == "path"
        assert result["exists"] is False

    def test_context_path_resolution(self, tmp_path):
        context_file = tmp_path / "docs" / "rules" / "index.md"
        context_file.parent.mkdir(parents=True)
        context_file.write_text("index")
        target = tmp_path / "docs" / "rules" / "leaf" / "rule.md"
        target.parent.mkdir(parents=True)
        target.write_text("rule")

        mcp = _register()
        result = json.loads(mcp.tools["doc_link_resolve"](
            "leaf/rule.md", context_path=str(context_file)
        ))
        assert result["type"] == "path"
        assert result["exists"] is True

    def test_task_id_resolve(self, tmp_path):
        rd_file = tmp_path / "R&D-BACKLOG.md"
        rd_file.write_text("# Backlog\n| RD-001 | Task |")

        with patch("governance.mcp_tools.evidence.documents_links.BACKLOG_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_link_resolve"]("RD-001"))
            assert result["type"] == "task_id"
            assert result["exists"] is True
