"""
Unit tests for Task Linking MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/tasks_linking.py module.
Per SRVJ-BUG-LINK-IDEM-01: Write handlers route through service layer;
tests mock service functions for writes, TypeDB client for reads.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.tasks_linking import register_task_linking_tools
from governance.services.link_result import LinkResult

_P_CLIENT = "governance.mcp_tools.tasks_linking.get_typedb_client"
_P_FMT = "governance.mcp_tools.tasks_linking.format_mcp_result"
_P_MON = "governance.mcp_tools.tasks_linking.MONITORING_AVAILABLE"
_P_SVC = "governance.services.tasks_mutations_linking"


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
    c.link_task_to_session.return_value = link_result
    c.link_task_to_rule.return_value = link_result
    c.link_evidence_to_task.return_value = link_result
    c.get_task_evidence.return_value = ["evidence/file.md"]
    c.link_task_to_commit.return_value = link_result
    c.get_task_commits.return_value = [{"sha": "abc123"}]
    c.update_task_details.return_value = link_result
    c.get_task_details.return_value = {"business": "desc"}
    return c


@pytest.fixture(autouse=True)
def _json_format():
    with patch(_P_FMT, side_effect=lambda x: json.dumps(x)), \
         patch(_P_MON, False):
        yield


@pytest.fixture()
def mcp():
    m = _CaptureMCP()
    register_task_linking_tools(m)
    return m


class TestTaskLinkSession:
    def test_success(self, mcp):
        with patch(f"{_P_SVC}.link_task_to_session",
                   return_value=LinkResult(success=True, already_existed=False, reason="linked")):
            result = json.loads(mcp.tools["task_link_session"]("T-1", "S-1"))
            assert result["relation"] == "completed-in"

    def test_failure(self, mcp):
        with patch(f"{_P_SVC}.link_task_to_session",
                   return_value=LinkResult(success=False, already_existed=False,
                                           reason="task T-1 not found", error_code="ENTITY_NOT_FOUND")):
            result = json.loads(mcp.tools["task_link_session"]("T-1", "S-1"))
            assert "error" in result


class TestTaskLinkRule:
    def test_success(self, mcp):
        with patch(f"{_P_SVC}.link_task_to_rule",
                   return_value=LinkResult(success=True, already_existed=False, reason="linked")):
            result = json.loads(mcp.tools["task_link_rule"]("T-1", "RULE-001"))
            assert result["relation"] == "implements-rule"

    def test_failure(self, mcp):
        with patch(f"{_P_SVC}.link_task_to_rule",
                   return_value=LinkResult(success=False, already_existed=False,
                                           reason="task T-1 not found", error_code="ENTITY_NOT_FOUND")):
            result = json.loads(mcp.tools["task_link_rule"]("T-1", "RULE-001"))
            assert "error" in result


class TestTaskLinkEvidence:
    def test_success(self, mcp):
        with patch(f"{_P_SVC}.link_task_to_evidence",
                   return_value=LinkResult(success=True, already_existed=False, reason="linked")):
            result = json.loads(mcp.tools["task_link_evidence"]("T-1", "ev.md"))
            assert result["relation"] == "evidence-supports"

    def test_failure(self, mcp):
        with patch(f"{_P_SVC}.link_task_to_evidence",
                   return_value=LinkResult(success=False, already_existed=False,
                                           reason="task T-1 not found", error_code="ENTITY_NOT_FOUND")):
            result = json.loads(mcp.tools["task_link_evidence"]("T-1", "ev.md"))
            assert "error" in result


class TestTaskGetEvidence:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client()):
            result = json.loads(mcp.tools["task_get_evidence"]("T-1"))
            assert result["count"] == 1
            assert "evidence/file.md" in result["evidence_files"]


class TestTaskLinkCommit:
    def test_success(self, mcp):
        # BUG-381-LNK-001: commit_sha must be 7-40 char hex string
        with patch(f"{_P_SVC}.link_task_to_commit",
                   return_value=LinkResult(success=True, already_existed=False, reason="linked")):
            result = json.loads(mcp.tools["task_link_commit"]("T-1", "abc1234"))
            assert result["relation"] == "task-commit"

    def test_failure(self, mcp):
        with patch(f"{_P_SVC}.link_task_to_commit",
                   return_value=LinkResult(success=False, already_existed=False,
                                           reason="task T-1 not found", error_code="ENTITY_NOT_FOUND")):
            result = json.loads(mcp.tools["task_link_commit"]("T-1", "abc1234"))
            assert "error" in result


class TestTaskGetCommits:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client()):
            result = json.loads(mcp.tools["task_get_commits"]("T-1"))
            assert result["count"] == 1


class TestTaskUpdateDetails:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client()):
            result = json.loads(mcp.tools["task_update_details"]("T-1", business="desc"))
            assert "task_id" in result

    def test_failure(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client(link_result=False)):
            result = json.loads(mcp.tools["task_update_details"]("T-1", business="x"))
            assert "error" in result


class TestTaskGetDetails:
    def test_success(self, mcp):
        with patch(_P_CLIENT, return_value=_make_client()):
            result = json.loads(mcp.tools["task_get_details"]("T-1"))
            assert result["task_id"] == "T-1"
            assert result["business"] == "desc"

    def test_not_found(self, mcp):
        c = _make_client()
        c.get_task_details.return_value = None
        with patch(_P_CLIENT, return_value=c):
            result = json.loads(mcp.tools["task_get_details"]("T-MISS"))
            assert "error" in result
