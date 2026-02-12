"""
Unit tests for Workflow Data Loader Controllers.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/controllers/workflow_loaders.py.
Tests: register_workflow_loader_controllers — load_workflow_status, submit_proposal.
"""

from unittest.mock import MagicMock, patch

from agent.governance_ui.controllers.workflow_loaders import (
    register_workflow_loader_controllers,
)


def _setup():
    """Create mock ctrl + state, register handlers, return internals."""
    ctrl = MagicMock()
    state = MagicMock()

    triggers = {}

    def trigger_decorator(name):
        def wrapper(fn):
            triggers[name] = fn
            return fn
        return wrapper

    ctrl.trigger = MagicMock(side_effect=trigger_decorator)

    result = register_workflow_loader_controllers(state, ctrl, "http://localhost:8082")

    return ctrl, state, triggers, result


# ── Registration ─────────────────────────────────────────


class TestRegistration:
    def test_registers_triggers(self):
        _, _, triggers, _ = _setup()
        assert "load_workflow_status" in triggers
        assert "submit_proposal" in triggers

    def test_returns_loader(self):
        _, _, _, result = _setup()
        assert "load_workflow_status" in result


# ── load_workflow_status ─────────────────────────────────


class TestLoadWorkflowStatus:
    @patch("agent.governance_ui.controllers.workflow_loaders.httpx")
    def test_success(self, mock_httpx):
        _, state, triggers, _ = _setup()

        with patch("governance.workflow_compliance.run_compliance_checks") as mock_checks, \
             patch("governance.workflow_compliance.format_compliance_for_ui") as mock_fmt:
            mock_checks.return_value = {"passed": 10}
            mock_fmt.return_value = {
                "status": {"overall": "COMPLIANT", "passed": 10, "failed": 0},
                "checks": [{"rule_id": "R-1", "check_name": "C1", "status": "PASS", "message": "OK"}],
                "violations": [],
                "recommendations": [],
            }
            # Mock workflow-info and history API calls
            info_resp = MagicMock(status_code=200, json=MagicMock(return_value={"graph": "data"}))
            hist_resp = MagicMock(status_code=200, json=MagicMock(return_value={"items": []}))
            mock_httpx.get.side_effect = [info_resp, hist_resp]

            triggers["load_workflow_status"]()

        assert state.workflow_loading is False
        assert state.workflow_violations == []

    def test_compliance_exception(self):
        _, state, triggers, _ = _setup()

        with patch("governance.workflow_compliance.run_compliance_checks",
                    side_effect=Exception("TypeDB down")), \
             patch("agent.governance_ui.controllers.workflow_loaders.httpx"):
            triggers["load_workflow_status"]()

        assert state.workflow_status["overall"] == "ERROR"
        assert state.workflow_checks == []
        assert "failed" in state.workflow_recommendations[0]
        assert state.workflow_loading is False


# ── submit_proposal ──────────────────────────────────────


class TestSubmitProposal:
    @patch("agent.governance_ui.controllers.workflow_loaders.httpx")
    def test_success(self, mock_httpx):
        _, state, triggers, _ = _setup()
        state.proposal_action = "create"
        state.proposal_hypothesis = "Test hypothesis"
        state.proposal_evidence = "Evidence 1, Evidence 2"
        state.proposal_rule_id = None
        state.proposal_directive = None
        state.proposal_dry_run = True

        submit_resp = MagicMock(status_code=200)
        submit_resp.json.return_value = {"decision": "approved"}
        hist_resp = MagicMock(status_code=200)
        hist_resp.json.return_value = {"items": [{"id": "P-1"}]}
        mock_httpx.post.return_value = submit_resp
        mock_httpx.get.return_value = hist_resp

        triggers["submit_proposal"]()
        assert state.proposal_result == {"decision": "approved"}
        assert state.proposal_history == [{"id": "P-1"}]
        assert state.proposal_submitting is False

    @patch("agent.governance_ui.controllers.workflow_loaders.httpx")
    def test_api_error(self, mock_httpx):
        _, state, triggers, _ = _setup()
        state.proposal_action = "modify"
        state.proposal_hypothesis = "H"
        state.proposal_evidence = ""
        state.proposal_rule_id = "R-1"
        state.proposal_directive = None
        state.proposal_dry_run = False

        submit_resp = MagicMock(status_code=500, text="Internal error")
        mock_httpx.post.return_value = submit_resp

        triggers["submit_proposal"]()
        assert state.proposal_result["decision"] == "error"
        assert "Internal error" in state.proposal_result["decision_reasoning"]

    @patch("agent.governance_ui.controllers.workflow_loaders.httpx")
    def test_exception(self, mock_httpx):
        _, state, triggers, _ = _setup()
        state.proposal_action = "create"
        state.proposal_hypothesis = "H"
        state.proposal_evidence = "E"
        state.proposal_rule_id = None
        state.proposal_directive = None
        state.proposal_dry_run = True

        mock_httpx.post.side_effect = Exception("network error")

        triggers["submit_proposal"]()
        assert state.proposal_result["decision"] == "error"
        assert "network error" in state.proposal_result["decision_reasoning"]
        assert state.proposal_submitting is False

    @patch("agent.governance_ui.controllers.workflow_loaders.httpx")
    def test_empty_evidence(self, mock_httpx):
        _, state, triggers, _ = _setup()
        state.proposal_action = "create"
        state.proposal_hypothesis = "H"
        state.proposal_evidence = ""  # Empty
        state.proposal_rule_id = None
        state.proposal_directive = None
        state.proposal_dry_run = True

        submit_resp = MagicMock(status_code=200)
        submit_resp.json.return_value = {"decision": "approved"}
        hist_resp = MagicMock(status_code=200, json=MagicMock(return_value={"items": []}))
        mock_httpx.post.return_value = submit_resp
        mock_httpx.get.return_value = hist_resp

        triggers["submit_proposal"]()
        # Evidence defaults to ["no evidence provided"]
        call_body = mock_httpx.post.call_args[1]["json"]
        assert call_body["evidence"] == ["no evidence provided"]
