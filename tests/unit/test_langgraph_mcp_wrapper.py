"""
Unit tests for LangGraph MCP Wrapper.

Per DOC-SIZE-01-v1: Tests for governance/langgraph/mcp_wrapper.py.
Tests: proposal_submit_mcp — evidence parsing, result formatting, dry run.
"""

import json
from unittest.mock import patch

from governance.langgraph.mcp_wrapper import proposal_submit_mcp

_MOCK_RESULT = {
    "proposal_id": "PROP-001",
    "action": "create",
    "decision": "approved",
    "status": "COMPLETE",
    "phases_completed": ["SUBMIT", "VALIDATE", "VOTE", "DECIDE"],
    "impact_score": 0.5,
    "risk_level": "LOW",
    "votes_for": 3,
    "votes_against": 0,
    "error_message": None,
}

_PATCH = "governance.langgraph.mcp_wrapper.run_proposal_workflow"


class TestProposalSubmitMcp:
    @patch(_PATCH, return_value=_MOCK_RESULT)
    def test_returns_json(self, mock_workflow):
        result = proposal_submit_mcp("create", "hypothesis text", "evidence1, evidence2")
        parsed = json.loads(result)
        assert parsed["proposal_id"] == "PROP-001"
        assert parsed["decision"] == "approved"

    @patch(_PATCH, return_value=_MOCK_RESULT)
    def test_evidence_split(self, mock_workflow):
        proposal_submit_mcp("create", "test hypothesis", "a, b, c")
        call_args = mock_workflow.call_args
        assert call_args[1]["evidence"] == ["a", "b", "c"]

    @patch(_PATCH, return_value=_MOCK_RESULT)
    def test_single_evidence(self, mock_workflow):
        proposal_submit_mcp("create", "test hypothesis", "single evidence")
        call_args = mock_workflow.call_args
        assert call_args[1]["evidence"] == ["single evidence"]

    @patch(_PATCH, return_value=_MOCK_RESULT)
    def test_passes_all_params(self, mock_workflow):
        proposal_submit_mcp(
            action="modify",
            hypothesis="modify rule",
            evidence="ev1",
            submitter_id="AGENT-002",
            rule_id="R-1",
            directive="New directive",
            dry_run=False
        )
        call_args = mock_workflow.call_args[1]
        assert call_args["action"] == "modify"
        assert call_args["submitter_id"] == "AGENT-002"
        assert call_args["rule_id"] == "R-1"
        assert call_args["directive"] == "New directive"
        assert call_args["dry_run"] is False

    @patch(_PATCH, return_value=_MOCK_RESULT)
    def test_dry_run_default(self, mock_workflow):
        proposal_submit_mcp("create", "hypothesis", "evidence")
        assert mock_workflow.call_args[1]["dry_run"] is True

    @patch(_PATCH, return_value={**_MOCK_RESULT, "error_message": "validation failed"})
    def test_error_in_result(self, mock_workflow):
        result = proposal_submit_mcp("create", "bad", "no evidence")
        parsed = json.loads(result)
        assert parsed["error_message"] == "validation failed"

    @patch(_PATCH, return_value=_MOCK_RESULT)
    def test_result_keys(self, mock_workflow):
        result = proposal_submit_mcp("create", "hypothesis", "ev")
        parsed = json.loads(result)
        expected_keys = {"proposal_id", "action", "decision", "status",
                         "phases_completed", "impact_score", "risk_level",
                         "votes_for", "votes_against", "error_message"}
        assert set(parsed.keys()) == expected_keys

    @patch(_PATCH, return_value=_MOCK_RESULT)
    def test_evidence_whitespace_trimmed(self, mock_workflow):
        proposal_submit_mcp("create", "test", "  a  ,  b  ,  c  ")
        evidence = mock_workflow.call_args[1]["evidence"]
        assert evidence == ["a", "b", "c"]
