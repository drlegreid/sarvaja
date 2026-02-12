"""
Unit tests for Agent Task Backlog Data Access.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/data_access/backlog.py.
Tests: get_available_tasks, claim_task, complete_task, get_agent_tasks,
       link_evidence_to_session, get_session_evidence.
"""

from unittest.mock import patch, MagicMock

from agent.governance_ui.data_access.backlog import (
    get_available_tasks, claim_task, complete_task,
    get_agent_tasks, link_evidence_to_session, get_session_evidence,
)


def _mock_client(response):
    """Create a mock httpx.Client context manager."""
    mock_client = MagicMock()
    mock_client.get.return_value = response
    mock_client.put.return_value = response
    mock_client.post.return_value = response
    return mock_client


def _mock_context(MockClient, response):
    """Set up MockClient context manager to return mock_client."""
    mc = _mock_client(response)
    MockClient.return_value.__enter__ = MagicMock(return_value=mc)
    MockClient.return_value.__exit__ = MagicMock(return_value=False)
    return mc


# ── get_available_tasks ──────────────────────────────────


class TestGetAvailableTasks:
    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_success(self, MockClient):
        resp = MagicMock(status_code=200)
        resp.json.return_value = [{"task_id": "T-1"}]
        _mock_context(MockClient, resp)
        assert get_available_tasks() == [{"task_id": "T-1"}]

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_api_error(self, MockClient):
        _mock_context(MockClient, MagicMock(status_code=500))
        assert get_available_tasks() == []

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_exception(self, MockClient):
        MockClient.side_effect = Exception("err")
        assert get_available_tasks() == []


# ── claim_task ───────────────────────────────────────────


class TestClaimTask:
    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_success(self, MockClient):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"task_id": "T-1", "status": "IN_PROGRESS"}
        _mock_context(MockClient, resp)
        result = claim_task("T-1", "agent-001")
        assert result["task_id"] == "T-1"

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_conflict(self, MockClient):
        resp = MagicMock(status_code=409, text="already claimed")
        _mock_context(MockClient, resp)
        result = claim_task("T-1", "agent-001")
        assert "error" in result
        assert result["status_code"] == 409

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_exception(self, MockClient):
        MockClient.side_effect = Exception("timeout")
        result = claim_task("T-1", "agent-001")
        assert "timeout" in result["error"]


# ── complete_task ────────────────────────────────────────


class TestCompleteTask:
    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_success(self, MockClient):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"task_id": "T-1", "status": "DONE"}
        _mock_context(MockClient, resp)
        result = complete_task("T-1", evidence="done")
        assert result["status"] == "DONE"

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_without_evidence(self, MockClient):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"task_id": "T-1"}
        mc = _mock_context(MockClient, resp)
        complete_task("T-1")
        params = mc.put.call_args[1]["params"]
        assert params == {}

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_error(self, MockClient):
        resp = MagicMock(status_code=400, text="bad request")
        _mock_context(MockClient, resp)
        result = complete_task("T-1")
        assert "error" in result


# ── get_agent_tasks ──────────────────────────────────────


class TestGetAgentTasks:
    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_success(self, MockClient):
        resp = MagicMock(status_code=200)
        resp.json.return_value = [{"task_id": "T-1"}]
        _mock_context(MockClient, resp)
        assert get_agent_tasks("agent-001") == [{"task_id": "T-1"}]

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_error(self, MockClient):
        _mock_context(MockClient, MagicMock(status_code=500))
        assert get_agent_tasks("agent-001") == []


# ── link_evidence_to_session ─────────────────────────────


class TestLinkEvidenceToSession:
    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_success(self, MockClient):
        resp = MagicMock(status_code=201)
        resp.json.return_value = {"linked": True}
        _mock_context(MockClient, resp)
        result = link_evidence_to_session("S-1", "evidence/S-1.md")
        assert result["linked"] is True

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_error(self, MockClient):
        resp = MagicMock(status_code=400, text="bad")
        _mock_context(MockClient, resp)
        result = link_evidence_to_session("S-1", "bad.md")
        assert "error" in result

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_exception(self, MockClient):
        MockClient.side_effect = Exception("conn err")
        result = link_evidence_to_session("S-1", "x.md")
        assert "conn err" in result["error"]


# ── get_session_evidence ─────────────────────────────────


class TestGetSessionEvidence:
    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_success(self, MockClient):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"evidence_files": ["e1.md", "e2.md"]}
        _mock_context(MockClient, resp)
        result = get_session_evidence("S-1")
        assert result == ["e1.md", "e2.md"]

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_error(self, MockClient):
        _mock_context(MockClient, MagicMock(status_code=404))
        assert get_session_evidence("S-X") == []

    @patch("agent.governance_ui.data_access.backlog.httpx.Client")
    def test_exception(self, MockClient):
        MockClient.side_effect = Exception("err")
        assert get_session_evidence("S-X") == []
