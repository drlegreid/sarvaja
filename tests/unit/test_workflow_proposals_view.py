"""
Tests for workflow proposal UI components.

Per DOC-SIZE-01-v1: Extracted from workflow_view.py.
Batch 160: New coverage for views/workflow_proposals.py (0→12 tests).
"""
import inspect

import pytest


class TestWorkflowProposalComponents:
    def test_build_proposal_graph_callable(self):
        from agent.governance_ui.views.workflow_proposals import build_proposal_graph_panel
        assert callable(build_proposal_graph_panel)

    def test_build_proposal_form_callable(self):
        from agent.governance_ui.views.workflow_proposals import build_proposal_form
        assert callable(build_proposal_form)

    def test_build_proposal_history_callable(self):
        from agent.governance_ui.views.workflow_proposals import build_proposal_history
        assert callable(build_proposal_history)


class TestProposalGraphPanel:
    def test_has_graph_panel_testid(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "workflow-graph-panel" in source

    def test_has_stepper(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "workflow-phase-stepper" in source

    def test_has_langgraph_indicator(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "LangGraph Active" in source
        assert "Fallback Mode" in source


class TestProposalForm:
    def test_has_form_panel_testid(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "proposal-form-panel" in source

    def test_has_submit_button(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "proposal-submit-btn" in source

    def test_has_action_select(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "proposal-action" in source

    def test_has_hypothesis_field(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "proposal-hypothesis" in source

    def test_has_evidence_field(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "proposal-evidence" in source


class TestProposalHistory:
    def test_has_history_panel_testid(self):
        from agent.governance_ui.views import workflow_proposals
        source = inspect.getsource(workflow_proposals)
        assert "proposal-history-panel" in source
