"""
Unit tests for Governance Proposal Routes.

Per DOC-SIZE-01-v1: Tests for routes/proposals.py module.
Tests: submit_proposal, list_proposals, get_workflow_info.
"""

import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from governance.routes.proposals import (
    router, submit_proposal, list_proposals, get_workflow_info,
    ProposalRequest, ProposalResponse, _proposal_history,
)

_P = "governance.routes.proposals"


@pytest.fixture(autouse=True)
def _clear_history():
    _proposal_history.clear()
    yield
    _proposal_history.clear()


def _make_workflow_result(**overrides):
    base = {
        "proposal_id": "PROP-001",
        "action": "create",
        "decision": "approved",
        "status": "completed",
        "phases_completed": ["submit", "validate", "assess", "vote", "decide"],
        "impact_score": 0.7,
        "risk_level": "LOW",
        "votes_for": 0.8,
        "votes_against": 0.2,
        "quorum_reached": True,
        "threshold_met": True,
        "decision_reasoning": "Evidence supports the proposal",
    }
    base.update(overrides)
    return base


class TestProposalRequest:
    def test_valid_create(self):
        req = ProposalRequest(
            action="create",
            hypothesis="This is a valid hypothesis text",
            evidence=["e1"],
        )
        assert req.action == "create"
        assert req.dry_run is True

    def test_defaults(self):
        req = ProposalRequest(
            action="modify",
            hypothesis="This hypothesis is long enough",
            evidence=["e1"],
        )
        assert req.submitter_id == "AGENT-001"
        assert req.rule_id is None
        assert req.directive is None
        assert req.dry_run is True


class TestProposalResponse:
    def test_from_dict(self):
        resp = ProposalResponse(
            proposal_id="PROP-001",
            action="create",
            decision="approved",
            status="completed",
            phases_completed=["submit"],
            impact_score=0.5,
            risk_level="LOW",
            votes_for=0.8,
            votes_against=0.2,
            quorum_reached=True,
            threshold_met=True,
            decision_reasoning="Valid",
            dry_run=True,
            submitted_at="2026-01-01T00:00:00",
        )
        assert resp.proposal_id == "PROP-001"
        assert resp.error_message is None


class TestSubmitProposal:
    @pytest.mark.asyncio
    async def test_success(self):
        req = ProposalRequest(
            action="create",
            hypothesis="This is a valid hypothesis text",
            evidence=["e1"],
            directive="Do X",
        )
        with patch(f"{_P}.run_proposal_workflow", return_value=_make_workflow_result()):
            result = await submit_proposal(req)
        assert result.proposal_id == "PROP-001"
        assert result.decision == "approved"
        assert result.dry_run is True
        assert len(_proposal_history) == 1

    @pytest.mark.asyncio
    async def test_workflow_failure(self):
        from fastapi import HTTPException
        req = ProposalRequest(
            action="create",
            hypothesis="This is a valid hypothesis text",
            evidence=["e1"],
        )
        with patch(f"{_P}.run_proposal_workflow", side_effect=Exception("workflow error")):
            with pytest.raises(HTTPException) as exc:
                await submit_proposal(req)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_defaults_for_missing_fields(self):
        req = ProposalRequest(
            action="create",
            hypothesis="This is a valid hypothesis text",
            evidence=["e1"],
        )
        with patch(f"{_P}.run_proposal_workflow", return_value={}):
            result = await submit_proposal(req)
        assert result.proposal_id == ""
        assert result.decision == "pending"
        assert result.status == "unknown"

    @pytest.mark.asyncio
    async def test_passes_all_params(self):
        req = ProposalRequest(
            action="modify",
            hypothesis="This is a valid hypothesis text",
            evidence=["e1", "e2"],
            submitter_id="AGENT-002",
            rule_id="RULE-001",
            directive="Do Y",
            dry_run=False,
        )
        with patch(f"{_P}.run_proposal_workflow", return_value=_make_workflow_result()) as mock_run:
            await submit_proposal(req)
        mock_run.assert_called_once_with(
            action="modify",
            hypothesis="This is a valid hypothesis text",
            evidence=["e1", "e2"],
            submitter_id="AGENT-002",
            rule_id="RULE-001",
            directive="Do Y",
            dry_run=False,
        )


class TestListProposals:
    @pytest.mark.asyncio
    async def test_empty(self):
        result = await list_proposals()
        assert result["items"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_with_history(self):
        _proposal_history.append({"proposal_id": "P-1"})
        _proposal_history.append({"proposal_id": "P-2"})
        result = await list_proposals()
        assert result["total"] == 2
        # Most recent first
        assert result["items"][0]["proposal_id"] == "P-2"

    @pytest.mark.asyncio
    async def test_limit(self):
        for i in range(5):
            _proposal_history.append({"proposal_id": f"P-{i}"})
        result = await list_proposals(limit=3)
        assert len(result["items"]) == 3


class TestGetWorkflowInfo:
    @pytest.mark.asyncio
    async def test_returns_phases(self):
        result = await get_workflow_info()
        assert "phases" in result
        assert len(result["phases"]) == 7

    @pytest.mark.asyncio
    async def test_returns_thresholds(self):
        result = await get_workflow_info()
        assert "thresholds" in result
        assert "quorum" in result["thresholds"]
        assert "approval" in result["thresholds"]

    @pytest.mark.asyncio
    async def test_returns_edges(self):
        result = await get_workflow_info()
        assert "edges" in result
        assert len(result["edges"]) > 0

    @pytest.mark.asyncio
    async def test_langgraph_flag(self):
        result = await get_workflow_info()
        assert "langgraph_available" in result
