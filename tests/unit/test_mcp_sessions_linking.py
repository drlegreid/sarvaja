"""
Unit tests for Session Linking MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/sessions_linking.py module.
Tests: session_get_tasks, session_link_rule, session_link_decision, session_link_evidence.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.sessions_linking import register_session_linking_tools

_P_CLIENT = "governance.mcp_tools.sessions_linking.TypeDBClient"
_P_FMT = "governance.mcp_tools.sessions_linking.format_mcp_result"
_P_MON = "governance.mcp_tools.sessions_linking.MONITORING_AVAILABLE"
_P_AVAIL = "governance.mcp_tools.sessions_linking.TYPEDB_AVAILABLE"


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def _make_client(connect=True, link_result=True):
    c = MagicMock()
    c.connect.return_value = connect
    c.execute_query.return_value = [
        {"tid": "T-1", "name": "Task 1", "status": "DONE"},
    ]
    c.link_rule_to_session.return_value = link_result
    c.link_decision_to_session.return_value = link_result
    c.link_evidence_to_session.return_value = link_result
    return c


@pytest.fixture(autouse=True)
def _json_format():
    with patch(_P_FMT, side_effect=lambda x: json.dumps(x)), \
         patch(_P_MON, False):
        yield


@pytest.fixture()
def mcp():
    m = _CaptureMCP()
    register_session_linking_tools(m)
    return m


class TestSessionGetTasks:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client()), \
             patch(_P_AVAIL, True):
            result = json.loads(mcp.tools["session_get_tasks"]("S-1"))
            assert result["count"] == 1
            assert result["tasks"][0]["task_id"] == "T-1"

    def test_no_typedb(self, mcp):
        with patch(_P_AVAIL, False):
            result = json.loads(mcp.tools["session_get_tasks"]("S-1"))
            assert "error" in result

    def test_no_connect(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client(connect=False)), \
             patch(_P_AVAIL, True):
            result = json.loads(mcp.tools["session_get_tasks"]("S-1"))
            assert "error" in result


class TestSessionLinkRule:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client()), \
             patch(_P_AVAIL, True):
            result = json.loads(mcp.tools["session_link_rule"]("S-1", "RULE-001"))
            assert result["relation"] == "session-applied-rule"

    def test_failure(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client(link_result=False)), \
             patch(_P_AVAIL, True):
            result = json.loads(mcp.tools["session_link_rule"]("S-1", "RULE-001"))
            assert "error" in result

    def test_no_typedb(self, mcp):
        with patch(_P_AVAIL, False):
            result = json.loads(mcp.tools["session_link_rule"]("S-1", "R-1"))
            assert "error" in result


class TestSessionLinkDecision:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client()), \
             patch(_P_AVAIL, True):
            result = json.loads(mcp.tools["session_link_decision"]("S-1", "DEC-001"))
            assert result["relation"] == "session-decision"

    def test_failure(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client(link_result=False)), \
             patch(_P_AVAIL, True):
            result = json.loads(mcp.tools["session_link_decision"]("S-1", "DEC-001"))
            assert "error" in result


class TestSessionLinkEvidence:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client()), \
             patch(_P_AVAIL, True):
            result = json.loads(mcp.tools["session_link_evidence"]("S-1", "ev.md"))
            assert result["relation"] == "has-evidence"

    def test_failure(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client(link_result=False)), \
             patch(_P_AVAIL, True):
            result = json.loads(mcp.tools["session_link_evidence"]("S-1", "ev.md"))
            assert "error" in result

    def test_no_typedb(self, mcp):
        with patch(_P_AVAIL, False):
            result = json.loads(mcp.tools["session_link_evidence"]("S-1", "ev.md"))
            assert "error" in result
