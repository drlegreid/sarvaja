"""
Unit tests for Workspace Rule-Document Linking MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/workspace_rules.py module.
Tests: workspace_scan_rule_documents, workspace_link_rules_to_documents,
       workspace_get_document_for_rule, workspace_get_rules_for_document.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.workspace_rules import register_workspace_rule_tools


_P_FMT = "governance.mcp_tools.workspace_rules.format_mcp_result"
_P_LINKER = "governance.rule_linker"


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _json_format():
    with patch(_P_FMT, side_effect=lambda x: json.dumps(x)):
        yield


@pytest.fixture()
def mcp():
    m = _CaptureMCP()
    register_workspace_rule_tools(m)
    return m


class _FakeDoc:
    def __init__(self, doc_id, path, rule_ids):
        self.document_id = doc_id
        self.path = path
        self.rule_ids = rule_ids


class TestScanRuleDocuments:
    def test_success(self, mcp):
        docs = [
            _FakeDoc("RULES-GOV", "docs/rules/RULES-GOVERNANCE.md", ["RULE-001", "RULE-002"]),
            _FakeDoc("RULES-TECH", "docs/rules/RULES-TECHNICAL.md", ["RULE-010"]),
        ]
        with patch(f"{_P_LINKER}.scan_rule_documents", return_value=docs):
            result = json.loads(mcp.tools["workspace_scan_rule_documents"]())

        assert result["total_documents"] == 2
        assert len(result["documents"]) == 2
        assert result["documents"][0]["rule_count"] == 2
        assert result["documents"][1]["path"] == "docs/rules/RULES-TECHNICAL.md"

    def test_empty(self, mcp):
        with patch(f"{_P_LINKER}.scan_rule_documents", return_value=[]):
            result = json.loads(mcp.tools["workspace_scan_rule_documents"]())

        assert result["total_documents"] == 0
        assert result["documents"] == []

    def test_none_rule_ids(self, mcp):
        docs = [_FakeDoc("D-1", "path.md", None)]
        with patch(f"{_P_LINKER}.scan_rule_documents", return_value=docs):
            result = json.loads(mcp.tools["workspace_scan_rule_documents"]())

        assert result["documents"][0]["rule_count"] == 0
        assert result["documents"][0]["rule_ids"] == []

    def test_error(self, mcp):
        with patch(f"{_P_LINKER}.scan_rule_documents",
                   side_effect=RuntimeError("scan failed")):
            result = json.loads(mcp.tools["workspace_scan_rule_documents"]())

        assert "error" in result
        assert "workspace_scan_rule_documents failed: RuntimeError" in result["error"]


class TestLinkRulesToDocuments:
    def test_success(self, mcp):
        link_result = {
            "documents_inserted": 3,
            "relations_created": 10,
        }
        with patch(f"{_P_LINKER}.link_rules_to_documents",
                   return_value=link_result):
            result = json.loads(mcp.tools["workspace_link_rules_to_documents"]())

        assert result["documents_inserted"] == 3
        assert result["relations_created"] == 10

    def test_error(self, mcp):
        with patch(f"{_P_LINKER}.link_rules_to_documents",
                   side_effect=RuntimeError("link failed")):
            result = json.loads(mcp.tools["workspace_link_rules_to_documents"]())

        assert "error" in result


class TestGetDocumentForRule:
    def test_found(self, mcp):
        with patch(f"{_P_LINKER}.get_document_for_rule",
                   return_value="docs/rules/leaf/SESSION-EVID-01-v1.md"):
            result = json.loads(
                mcp.tools["workspace_get_document_for_rule"]("SESSION-EVID-01-v1")
            )

        assert result["rule_id"] == "SESSION-EVID-01-v1"
        assert result["document_path"] == "docs/rules/leaf/SESSION-EVID-01-v1.md"

    def test_not_found(self, mcp):
        with patch(f"{_P_LINKER}.get_document_for_rule", return_value=None):
            result = json.loads(
                mcp.tools["workspace_get_document_for_rule"]("RULE-999")
            )

        assert result["document_path"] is None

    def test_error(self, mcp):
        with patch(f"{_P_LINKER}.get_document_for_rule",
                   side_effect=RuntimeError("db error")):
            result = json.loads(
                mcp.tools["workspace_get_document_for_rule"]("RULE-001")
            )

        assert "error" in result


class TestGetRulesForDocument:
    def test_found(self, mcp):
        with patch(f"{_P_LINKER}.get_rules_for_document",
                   return_value=["RULE-001", "RULE-002", "SESSION-EVID-01-v1"]):
            result = json.loads(
                mcp.tools["workspace_get_rules_for_document"]("RULES-GOV")
            )

        assert result["document_id"] == "RULES-GOV"
        assert result["rule_count"] == 3
        assert "SESSION-EVID-01-v1" in result["rule_ids"]

    def test_empty(self, mcp):
        with patch(f"{_P_LINKER}.get_rules_for_document", return_value=[]):
            result = json.loads(
                mcp.tools["workspace_get_rules_for_document"]("UNKNOWN")
            )

        assert result["rule_count"] == 0
        assert result["rule_ids"] == []

    def test_error(self, mcp):
        with patch(f"{_P_LINKER}.get_rules_for_document",
                   side_effect=RuntimeError("query error")):
            result = json.loads(
                mcp.tools["workspace_get_rules_for_document"]("DOC-1")
            )

        assert "error" in result
