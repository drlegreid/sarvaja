"""
Unit tests for Decision Evidence MCP Tools.

Batch 148: Tests for governance/mcp_tools/evidence/decisions.py
- governance_list_decisions: TypeDB + evidence file listing
- governance_get_decision: TypeDB + evidence file retrieval
"""

import json
import os
from dataclasses import dataclass, field
from unittest.mock import patch, MagicMock

import pytest

_MOD = "governance.mcp_tools.evidence.decisions"


@pytest.fixture(autouse=True)
def force_json_output():
    """Force JSON output format for predictable test results."""
    old = os.environ.get("MCP_OUTPUT_FORMAT")
    os.environ["MCP_OUTPUT_FORMAT"] = "json"
    yield
    if old is None:
        os.environ.pop("MCP_OUTPUT_FORMAT", None)
    else:
        os.environ["MCP_OUTPUT_FORMAT"] = old


def _register_tools():
    """Register and return tools by name."""
    from governance.mcp_tools.evidence.decisions import register_decision_tools

    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    register_decision_tools(MockMCP())
    return tools


@dataclass
class FakeDecision:
    id: str = "DECISION-001"
    name: str = "TypeDB-First Strategy"
    status: str = "APPROVED"
    decision_date: str = "2026-01-15"
    context: str = "Need persistent storage"
    rationale: str = "TypeDB provides graph + relational"


class TestRegistration:
    def test_registers_both_tools(self):
        tools = _register_tools()
        assert "governance_list_decisions" in tools
        assert "governance_get_decision" in tools


# ── governance_list_decisions ────────────────────────────


class TestGovernanceListDecisions:

    @patch(f"{_MOD}.glob.glob", return_value=[])
    @patch(f"{_MOD}.get_typedb_client")
    def test_typedb_decisions(self, mock_get_client, mock_glob):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_decisions.return_value = [FakeDecision()]
        mock_get_client.return_value = client

        result = json.loads(tools["governance_list_decisions"]())
        assert result["count"] == 1
        assert result["decisions"][0]["decision_id"] == "DECISION-001"
        assert result["decisions"][0]["source"] == "typedb"

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    @patch(f"{_MOD}.get_typedb_client")
    def test_evidence_file_fallback(self, mock_get_client, mock_path_cls, mock_glob):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = False
        mock_get_client.return_value = client

        mock_glob.return_value = ["/evidence/DECISION-003.md"]
        mock_path = MagicMock()
        mock_path.name = "DECISION-003.md"
        mock_path.read_text.return_value = "# TypeDB-First Strategy\nContent here\n"
        mock_path_cls.return_value = mock_path

        result = json.loads(tools["governance_list_decisions"]())
        assert result["count"] == 1
        assert result["decisions"][0]["decision_id"] == "DECISION-003"
        assert result["decisions"][0]["source"] == "evidence_file"
        assert result["decisions"][0]["name"] == "TypeDB-First Strategy"

    @patch(f"{_MOD}.glob.glob", return_value=[])
    @patch(f"{_MOD}.get_typedb_client")
    def test_typedb_exception_continues(self, mock_get_client, mock_glob):
        tools = _register_tools()
        client = MagicMock()
        client.connect.side_effect = Exception("connection error")
        mock_get_client.return_value = client

        # Should not raise
        result = json.loads(tools["governance_list_decisions"]())
        assert result["count"] == 0

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    @patch(f"{_MOD}.get_typedb_client")
    def test_dedup_typedb_and_evidence(self, mock_get_client, mock_path_cls, mock_glob):
        """Evidence files with same ID as TypeDB should not duplicate."""
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_decisions.return_value = [FakeDecision(id="DECISION-003")]
        mock_get_client.return_value = client

        mock_glob.return_value = ["/evidence/DECISION-003.md"]
        mock_path = MagicMock()
        mock_path.name = "DECISION-003.md"
        mock_path.read_text.return_value = "# Dup\n"
        mock_path_cls.return_value = mock_path

        result = json.loads(tools["governance_list_decisions"]())
        assert result["count"] == 1  # Not 2

    @patch(f"{_MOD}.glob.glob", return_value=[])
    @patch(f"{_MOD}.get_typedb_client")
    def test_empty_results(self, mock_get_client, mock_glob):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_decisions.return_value = []
        mock_get_client.return_value = client

        result = json.loads(tools["governance_list_decisions"]())
        assert result["count"] == 0
        assert result["decisions"] == []


# ── governance_get_decision ──────────────────────────────


class TestGovernanceGetDecision:

    @patch(f"{_MOD}.glob.glob", return_value=[])
    @patch(f"{_MOD}.get_typedb_client")
    def test_from_typedb(self, mock_get_client, mock_glob):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_decisions.return_value = [FakeDecision()]
        client.get_decision_impacts.return_value = ["RULE-001"]
        mock_get_client.return_value = client

        # Mock EVIDENCE_DIR / "DECISION-001.md" not existing
        with patch(f"{_MOD}.EVIDENCE_DIR") as mock_dir:
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_dir.__truediv__ = MagicMock(return_value=mock_file)

            result = json.loads(tools["governance_get_decision"]("DECISION-001"))

        assert result["decision_id"] == "DECISION-001"
        assert result["name"] == "TypeDB-First Strategy"
        assert result["source"] == "typedb"
        assert result["affected_rules"] == ["RULE-001"]

    @patch(f"{_MOD}.get_typedb_client")
    def test_from_evidence_file(self, mock_get_client):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = False
        mock_get_client.return_value = client

        with patch(f"{_MOD}.EVIDENCE_DIR") as mock_dir:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = "# Decision Content\nFull text here.\n"
            mock_dir.__truediv__ = MagicMock(return_value=mock_file)

            result = json.loads(tools["governance_get_decision"]("DECISION-003"))

        assert result["decision_id"] == "DECISION-003"
        assert "evidence_content" in result

    @patch(f"{_MOD}.glob.glob", return_value=[])
    @patch(f"{_MOD}.get_typedb_client")
    def test_not_found(self, mock_get_client, mock_glob):
        tools = _register_tools()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_decisions.return_value = []
        mock_get_client.return_value = client

        with patch(f"{_MOD}.EVIDENCE_DIR") as mock_dir:
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_dir.__truediv__ = MagicMock(return_value=mock_file)

            result = json.loads(tools["governance_get_decision"]("DECISION-MISSING"))

        assert "error" in result
        assert "not found" in result["error"]

    @patch(f"{_MOD}.glob.glob", return_value=[])
    @patch(f"{_MOD}.get_typedb_client")
    def test_typedb_exception_continues(self, mock_get_client, mock_glob):
        tools = _register_tools()
        client = MagicMock()
        client.connect.side_effect = Exception("timeout")
        mock_get_client.return_value = client

        with patch(f"{_MOD}.EVIDENCE_DIR") as mock_dir:
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_dir.__truediv__ = MagicMock(return_value=mock_file)

            result = json.loads(tools["governance_get_decision"]("D-1"))

        assert "error" in result
