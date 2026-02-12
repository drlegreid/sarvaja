"""
Unit tests for Decision Evidence MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/evidence/decisions.py module.
Tests: governance_list_decisions, governance_get_decision.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.evidence.decisions import register_decision_tools


_P_CLIENT = "governance.mcp_tools.evidence.decisions.get_typedb_client"
_P_FMT = "governance.mcp_tools.evidence.decisions.format_mcp_result"
_P_EVID = "governance.mcp_tools.evidence.decisions.EVIDENCE_DIR"


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
    register_decision_tools(m)
    return m


def _make_decision(did="DECISION-001", name="Test", status="ACTIVE",
                   date=None, context="ctx", rationale="rat"):
    d = MagicMock()
    d.id = did
    d.name = name
    d.status = status
    d.decision_date = date
    d.context = context
    d.rationale = rationale
    return d


def _make_client(connect=True, decisions=None, impacts=None):
    c = MagicMock()
    c.connect.return_value = connect
    c.get_all_decisions.return_value = decisions or []
    c.get_decision_impacts.return_value = impacts or []
    return c


class TestListDecisions:
    def test_from_typedb(self, mcp, tmp_path):
        dec = _make_decision()
        client = _make_client(decisions=[dec])

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_EVID, tmp_path):
            result = json.loads(mcp.tools["governance_list_decisions"]())

        assert result["count"] == 1
        assert result["decisions"][0]["decision_id"] == "DECISION-001"
        assert result["decisions"][0]["source"] == "typedb"

    def test_from_evidence_files(self, mcp, tmp_path):
        # Create a decision markdown file
        f = tmp_path / "DECISION-099.md"
        f.write_text("# My Decision\nSome content\n")

        client = _make_client(connect=False)
        with patch(_P_CLIENT, return_value=client), \
             patch(_P_EVID, tmp_path):
            result = json.loads(mcp.tools["governance_list_decisions"]())

        assert result["count"] == 1
        assert result["decisions"][0]["decision_id"] == "DECISION-099"
        assert result["decisions"][0]["name"] == "My Decision"
        assert result["decisions"][0]["source"] == "evidence_file"

    def test_no_duplicates(self, mcp, tmp_path):
        dec = _make_decision(did="DECISION-099")
        client = _make_client(decisions=[dec])

        # Also create evidence file with same ID
        f = tmp_path / "DECISION-099.md"
        f.write_text("# Duplicate\n")

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_EVID, tmp_path):
            result = json.loads(mcp.tools["governance_list_decisions"]())

        assert result["count"] == 1  # Not 2

    def test_empty(self, mcp, tmp_path):
        client = _make_client(connect=False)
        with patch(_P_CLIENT, return_value=client), \
             patch(_P_EVID, tmp_path):
            result = json.loads(mcp.tools["governance_list_decisions"]())

        assert result["count"] == 0
        assert result["decisions"] == []


class TestGetDecision:
    def test_from_typedb(self, mcp, tmp_path):
        dec = _make_decision(did="DECISION-003")
        client = _make_client(decisions=[dec], impacts=["RULE-001"])

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_EVID, tmp_path):
            result = json.loads(mcp.tools["governance_get_decision"]("DECISION-003"))

        assert result["decision_id"] == "DECISION-003"
        assert result["name"] == "Test"
        assert result["affected_rules"] == ["RULE-001"]

    def test_from_evidence_file(self, mcp, tmp_path):
        client = _make_client(connect=False)
        f = tmp_path / "DECISION-003.md"
        f.write_text("# Decision 3\nDetails here\n")

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_EVID, tmp_path):
            result = json.loads(mcp.tools["governance_get_decision"]("DECISION-003"))

        assert result["decision_id"] == "DECISION-003"
        assert "evidence_file" in result
        assert "Details here" in result["evidence_content"]

    def test_not_found(self, mcp, tmp_path):
        client = _make_client(connect=False)
        with patch(_P_CLIENT, return_value=client), \
             patch(_P_EVID, tmp_path):
            result = json.loads(mcp.tools["governance_get_decision"]("DECISION-999"))

        assert "error" in result

    def test_typedb_and_evidence(self, mcp, tmp_path):
        dec = _make_decision(did="DECISION-003")
        client = _make_client(decisions=[dec], impacts=[])

        f = tmp_path / "DECISION-003.md"
        f.write_text("# Decision File\nContent\n")

        with patch(_P_CLIENT, return_value=client), \
             patch(_P_EVID, tmp_path):
            result = json.loads(mcp.tools["governance_get_decision"]("DECISION-003"))

        assert result["source"] == "typedb"
        assert "evidence_content" in result
