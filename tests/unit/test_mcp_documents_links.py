"""
Unit tests for Document Link Extraction MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/evidence/documents_links.py module.
Tests: doc_links_extract, doc_link_resolve.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_P = "governance.mcp_tools.evidence.documents_links"


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
    from governance.mcp_tools.evidence.documents_links import register_link_document_tools
    register_link_document_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _mock_format():
    with patch(f"{_P}.format_mcp_result", side_effect=lambda x: json.dumps(x)):
        yield


# ── doc_links_extract ───────────────────────────────────────────


class TestDocLinksExtract:
    def test_extracts_markdown_links(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.md"
        doc.write_text("[Example](https://example.com)\n[Local](./file.md)\n")
        result = json.loads(tools["doc_links_extract"](path=str(doc)))
        assert result["summary"]["markdown_links"] == 2
        assert result["summary"]["external_links"] == 1
        assert result["summary"]["internal_links"] == 1

    def test_extracts_semantic_rule_refs(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.md"
        doc.write_text("See DOC-SIZE-01-v1 and TEST-GUARD-01-v1 for details.\n")
        result = json.loads(tools["doc_links_extract"](path=str(doc)))
        assert result["summary"]["rule_refs"] == 2
        rules = result["links"]["rules_semantic"]
        assert rules[0]["semantic_id"] == "DOC-SIZE-01-v1"

    def test_extracts_legacy_rule_refs(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.md"
        doc.write_text("Per RULE-001 and RULE-012.\n")
        result = json.loads(tools["doc_links_extract"](path=str(doc)))
        assert result["summary"]["rule_refs"] == 2

    def test_extracts_gap_refs(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.md"
        doc.write_text("See GAP-MCP-001 and GAP-DATA-003.\n")
        result = json.loads(tools["doc_links_extract"](path=str(doc)))
        assert result["summary"]["gap_refs"] == 2

    def test_extracts_task_refs(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.md"
        doc.write_text("Tasks P11.5 and RD-001 are done.\n")
        result = json.loads(tools["doc_links_extract"](path=str(doc)))
        assert result["summary"]["task_refs"] == 2

    def test_file_not_found(self):
        tools = _register()
        result = json.loads(tools["doc_links_extract"](path="/nonexistent/file.md"))
        assert "error" in result

    def test_relative_path_not_found(self):
        tools = _register()
        result = json.loads(tools["doc_links_extract"](path="nonexistent_doc_xyz.md"))
        assert "error" in result
        assert "tried_paths" in result

    def test_empty_document(self, tmp_path):
        tools = _register()
        doc = tmp_path / "empty.md"
        doc.write_text("")
        result = json.loads(tools["doc_links_extract"](path=str(doc)))
        assert result["summary"]["markdown_links"] == 0
        assert result["summary"]["rule_refs"] == 0

    def test_source_path_included(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.md"
        doc.write_text("Hello\n")
        result = json.loads(tools["doc_links_extract"](path=str(doc)))
        assert str(doc) in result["source"]


# ── doc_link_resolve ────────────────────────────────────────────


class TestDocLinkResolve:
    def test_semantic_rule_with_leaf_file(self, tmp_path):
        tools = _register()
        leaf_dir = tmp_path / "leaf"
        leaf_dir.mkdir()
        leaf_file = leaf_dir / "DOC-SIZE-01-v1.md"
        leaf_file.write_text("# DOC-SIZE-01-v1\n")
        with patch(f"{_P}.RULES_DIR", tmp_path):
            result = json.loads(tools["doc_link_resolve"](link="DOC-SIZE-01-v1"))
        assert result["type"] == "semantic_rule_id"
        assert result["exists"] is True

    def test_semantic_rule_fallback_to_legacy(self, tmp_path):
        tools = _register()
        rules_file = tmp_path / "RULES-GOVERNANCE.md"
        rules_file.write_text("## RULE-001\nSESSION-EVID-01-v1\n")
        with patch(f"{_P}.RULES_DIR", tmp_path), \
             patch("governance.rule_linker.SEMANTIC_TO_LEGACY", {"SESSION-EVID-01-v1": "RULE-001"}):
            result = json.loads(tools["doc_link_resolve"](link="SESSION-EVID-01-v1"))
        assert result["type"] == "semantic_rule_id"
        assert result["exists"] is True

    def test_semantic_rule_not_found(self, tmp_path):
        tools = _register()
        with patch(f"{_P}.RULES_DIR", tmp_path), \
             patch("governance.rule_linker.SEMANTIC_TO_LEGACY", {}):
            result = json.loads(tools["doc_link_resolve"](link="FAKE-RULE-01-v1"))
        assert result["type"] == "semantic_rule_id"
        assert result["exists"] is False

    def test_legacy_rule_with_semantic(self, tmp_path):
        tools = _register()
        leaf_dir = tmp_path / "leaf"
        leaf_dir.mkdir()
        leaf_file = leaf_dir / "SESSION-EVID-01-v1.md"
        leaf_file.write_text("# Rule\n")
        with patch(f"{_P}.RULES_DIR", tmp_path), \
             patch("governance.rule_linker.LEGACY_TO_SEMANTIC", {"RULE-001": "SESSION-EVID-01-v1"}):
            result = json.loads(tools["doc_link_resolve"](link="RULE-001"))
        assert result["type"] == "legacy_rule_id"
        assert result["exists"] is True

    def test_legacy_rule_not_found(self, tmp_path):
        tools = _register()
        with patch(f"{_P}.RULES_DIR", tmp_path), \
             patch("governance.rule_linker.LEGACY_TO_SEMANTIC", {}):
            result = json.loads(tools["doc_link_resolve"](link="RULE-999"))
        assert result["type"] == "legacy_rule_id"
        assert result["exists"] is False

    def test_gap_id_with_index(self, tmp_path):
        tools = _register()
        gap_index = tmp_path / "GAP-INDEX.md"
        gap_index.write_text("# Gaps\n")
        with patch(f"{_P}.GAPS_DIR", tmp_path):
            result = json.loads(tools["doc_link_resolve"](link="GAP-MCP-001"))
        assert result["type"] == "gap_id"
        assert result["exists"] is True

    def test_gap_id_with_dedicated_file(self, tmp_path):
        tools = _register()
        gap_file = tmp_path / "GAP-DATA-001.md"
        gap_file.write_text("# Gap\n")
        with patch(f"{_P}.GAPS_DIR", tmp_path):
            result = json.loads(tools["doc_link_resolve"](link="GAP-DATA-001"))
        assert result["type"] == "gap_id"
        assert result["exists"] is True

    def test_task_id_rd(self, tmp_path):
        tools = _register()
        rd_file = tmp_path / "R&D-BACKLOG.md"
        rd_file.write_text("# Backlog\n")
        with patch(f"{_P}.BACKLOG_DIR", tmp_path):
            result = json.loads(tools["doc_link_resolve"](link="RD-001"))
        assert result["type"] == "task_id"
        assert result["exists"] is True

    def test_absolute_path(self, tmp_path):
        tools = _register()
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n")
        result = json.loads(tools["doc_link_resolve"](link=str(test_file)))
        assert result["type"] == "path"
        assert result["exists"] is True

    def test_relative_path_with_context(self, tmp_path):
        tools = _register()
        sub = tmp_path / "docs"
        sub.mkdir()
        target = sub / "readme.md"
        target.write_text("# Readme\n")
        # Context file must exist for is_file() check
        context_file = sub / "other.md"
        context_file.write_text("# Other\n")
        result = json.loads(tools["doc_link_resolve"](
            link="readme.md", context_path=str(context_file),
        ))
        assert result["type"] == "path"
        assert result["exists"] is True
