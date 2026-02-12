"""
Unit tests for Entity Document Viewing MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/evidence/documents_entity.py module.
Tests: doc_rule_get, doc_task_get registration and file-based lookup.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from governance.mcp_tools.evidence.documents_entity import register_entity_document_tools


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
    register_entity_document_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _force_json_output():
    """Patch format_mcp_result to return JSON for all tests."""
    with patch(
        "governance.mcp_tools.evidence.documents_entity.format_mcp_result",
        side_effect=_json_format,
    ):
        yield


@pytest.fixture(autouse=True)
def _mock_typedb():
    """Mock TypeDB client to prevent real connections."""
    mock_client = MagicMock()
    mock_client.connect.return_value = False
    with patch(
        "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
        return_value=mock_client,
    ):
        yield mock_client


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestRegistration:
    """Tests for tool registration."""

    def test_registers_doc_rule_get(self):
        mcp = _register()
        assert "doc_rule_get" in mcp.tools

    def test_registers_doc_task_get(self):
        mcp = _register()
        assert "doc_task_get" in mcp.tools

    def test_total_tools(self):
        mcp = _register()
        assert len(mcp.tools) == 2


# ---------------------------------------------------------------------------
# doc_rule_get
# ---------------------------------------------------------------------------
class TestDocRuleGet:
    """Tests for doc_rule_get tool."""

    def test_finds_rule_in_file(self, tmp_path):
        rules_file = tmp_path / "RULES-GOVERNANCE.md"
        rules_file.write_text(
            "# Rules\n\n"
            "## RULE-001: First Rule\n"
            "**Priority:** HIGH\n"
            "**Status:** ACTIVE\n"
            "**Category:** Governance\n"
            "Rule content here.\n\n"
            "## RULE-002: Second Rule\n"
            "Another rule.\n"
        )
        with patch("governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_rule_get"]("RULE-001"))
            assert result["rule_id"] == "RULE-001"
            assert "Rule content here" in result["content"]
            assert result["metadata"]["priority"] == "HIGH"
            assert result["metadata"]["status"] == "ACTIVE"

    def test_rule_not_found_returns_error(self, tmp_path):
        rules_file = tmp_path / "RULES-GOVERNANCE.md"
        rules_file.write_text("# Rules\n## RULE-999: Other\nContent\n")
        with patch("governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_rule_get"]("RULE-001"))
            assert "error" in result

    def test_extracts_category_metadata(self, tmp_path):
        rules_file = tmp_path / "RULES-TECHNICAL.md"
        rules_file.write_text(
            "## RULE-010: Tech Rule\n"
            "**Category:** Technical\n"
            "Content.\n"
        )
        with patch("governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_rule_get"]("RULE-010"))
            assert result["metadata"]["category"] == "Technical"

    def test_missing_rule_files_handled(self, tmp_path):
        """No rule files exist at all — should return error."""
        with patch("governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_rule_get"]("RULE-001"))
            assert "error" in result

    def test_rule_at_end_of_file(self, tmp_path):
        rules_file = tmp_path / "RULES-GOVERNANCE.md"
        rules_file.write_text(
            "## RULE-050: Last Rule\n"
            "This is the last rule in the file.\n"
        )
        with patch("governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_rule_get"]("RULE-050"))
            assert result["rule_id"] == "RULE-050"
            assert "last rule" in result["content"]


# ---------------------------------------------------------------------------
# doc_task_get
# ---------------------------------------------------------------------------
class TestDocTaskGet:
    """Tests for doc_task_get tool."""

    def test_finds_task_in_table(self, tmp_path):
        backlog = tmp_path / "R&D-BACKLOG.md"
        backlog.write_text("| RD-001 | Research task | IN_PROGRESS |\n")
        with patch("governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_task_get"]("RD-001"))
            assert result["task_id"] == "RD-001"
            assert len(result["sources"]) == 1
            assert "Research task" in result["sources"][0]["line"]

    def test_task_not_found_returns_error(self, tmp_path):
        backlog = tmp_path / "R&D-BACKLOG.md"
        backlog.write_text("| RD-999 | Other | DONE |\n")
        with patch("governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_task_get"]("RD-001"))
            assert "error" in result

    def test_multiple_matches(self, tmp_path):
        backlog = tmp_path / "R&D-BACKLOG.md"
        backlog.write_text(
            "| P10.1 | Task one | DONE |\n"
            "| P10.1 | Task two | IN_PROGRESS |\n"
        )
        with patch("governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_task_get"]("P10.1"))
            assert len(result["sources"]) == 2

    def test_missing_files_returns_error(self, tmp_path):
        """No backlog or TODO files exist."""
        with patch("governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_task_get"]("P10.1"))
            assert "error" in result

    def test_cells_parsed_from_table(self, tmp_path):
        backlog = tmp_path / "R&D-BACKLOG.md"
        backlog.write_text("| RD-005 | Description | HIGH | OPEN |\n")
        with patch("governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR", tmp_path):
            mcp = _register()
            result = json.loads(mcp.tools["doc_task_get"]("RD-005"))
            cells = result["sources"][0]["cells"]
            assert "RD-005" in cells
            assert "Description" in cells
