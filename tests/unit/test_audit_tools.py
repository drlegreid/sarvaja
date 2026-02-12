"""
Unit tests for Audit Trail MCP Tools.

Per DOC-SIZE-01-v1: Tests for governance/mcp_tools/audit.py module.
Tests: register_audit_tools — audit_query, audit_summary,
       audit_entity_trail, audit_trace.
"""

import json
from unittest.mock import patch, MagicMock

import pytest


class _CaptureMCP:
    """Mock MCP server that captures @mcp.tool() decorated functions."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture()
def audit_tools():
    from governance.mcp_tools.audit import register_audit_tools
    mcp = _CaptureMCP()
    register_audit_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _mock_format():
    """Patch format_mcp_result to return plain JSON."""
    with patch("governance.mcp_tools.audit.format_mcp_result", side_effect=json.dumps):
        yield


# ── audit_query ────────────────────────────────────────────────


class TestAuditQuery:
    def test_returns_entries(self, audit_tools):
        entries = [{"entity_id": "T-1", "action_type": "CREATE"}]
        with patch("governance.stores.query_audit_trail", return_value=entries, create=True):
            result = json.loads(audit_tools["audit_query"]())
        assert result["count"] == 1

    def test_with_filters(self, audit_tools):
        with patch("governance.stores.query_audit_trail", return_value=[], create=True) as mock:
            result = json.loads(audit_tools["audit_query"](
                entity_id="T-1", entity_type="task", action_type="CREATE",
                correlation_id="CORR-1", limit=5
            ))
        assert result["count"] == 0
        mock.assert_called_once_with(
            entity_id="T-1", entity_type="task", action_type="CREATE",
            correlation_id="CORR-1", limit=5
        )

    def test_exception(self, audit_tools):
        with patch("governance.stores.query_audit_trail", side_effect=Exception("db err"), create=True):
            result = json.loads(audit_tools["audit_query"]())
        assert "error" in result


# ── audit_summary ──────────────────────────────────────────────


class TestAuditSummary:
    def test_returns_summary(self, audit_tools):
        summary = {"total": 42, "by_action": {"CREATE": 20}}
        with patch("governance.stores.get_audit_summary", return_value=summary, create=True):
            result = json.loads(audit_tools["audit_summary"]())
        assert result["total"] == 42

    def test_exception(self, audit_tools):
        with patch("governance.stores.get_audit_summary", side_effect=Exception("fail"), create=True):
            result = json.loads(audit_tools["audit_summary"]())
        assert "error" in result


# ── audit_entity_trail ─────────────────────────────────────────


class TestAuditEntityTrail:
    def test_with_entries(self, audit_tools):
        entries = [
            {"entity_id": "T-1", "action_type": "CREATE", "actor_id": "agent-1", "applied_rules": ["R-1"]},
            {"entity_id": "T-1", "action_type": "UPDATE", "actor_id": "agent-2", "applied_rules": ["R-2"]},
        ]
        with patch("governance.stores.query_audit_trail", return_value=entries, create=True):
            result = json.loads(audit_tools["audit_entity_trail"](entity_id="T-1"))
        assert result["count"] == 2
        assert result["entity_id"] == "T-1"
        assert "CREATE" in result["timeline_summary"]["actions"]
        assert "R-1" in result["timeline_summary"]["rules_applied"]

    def test_empty_entries(self, audit_tools):
        with patch("governance.stores.query_audit_trail", return_value=[], create=True):
            result = json.loads(audit_tools["audit_entity_trail"](entity_id="T-MISS"))
        assert result["count"] == 0
        assert "No audit entries" in result["message"]

    def test_entries_no_applied_rules(self, audit_tools):
        entries = [{"entity_id": "T-1", "action_type": "DELETE", "actor_id": "a1"}]
        with patch("governance.stores.query_audit_trail", return_value=entries, create=True):
            result = json.loads(audit_tools["audit_entity_trail"](entity_id="T-1"))
        assert result["timeline_summary"]["rules_applied"] == []

    def test_exception(self, audit_tools):
        with patch("governance.stores.query_audit_trail", side_effect=Exception("fail"), create=True):
            result = json.loads(audit_tools["audit_entity_trail"](entity_id="T-1"))
        assert "error" in result


# ── audit_trace ────────────────────────────────────────────────


class TestAuditTrace:
    def test_with_entries(self, audit_tools):
        entries = [
            {"entity_id": "T-1", "action_type": "CREATE"},
            {"entity_id": "S-1", "action_type": "UPDATE"},
            {"entity_id": "T-1", "action_type": "COMPLETE"},
        ]
        with patch("governance.stores.query_audit_trail", return_value=entries, create=True):
            result = json.loads(audit_tools["audit_trace"](correlation_id="CORR-1"))
        assert result["count"] == 3
        assert result["correlation_id"] == "CORR-1"
        assert "T-1" in result["affected_entities"]
        assert len(result["affected_entities"]["T-1"]) == 2

    def test_empty_entries(self, audit_tools):
        with patch("governance.stores.query_audit_trail", return_value=[], create=True):
            result = json.loads(audit_tools["audit_trace"](correlation_id="CORR-MISS"))
        assert result["count"] == 0
        assert "No operations" in result["message"]

    def test_exception(self, audit_tools):
        with patch("governance.stores.query_audit_trail", side_effect=Exception("fail"), create=True):
            result = json.loads(audit_tools["audit_trace"](correlation_id="CORR-1"))
        assert "error" in result
