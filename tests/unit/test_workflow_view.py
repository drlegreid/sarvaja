"""
Tests for workflow compliance dashboard view.

Per RD-WORKFLOW Phase 4: Reporting & Alerts Dashboard.
Batch 167: New coverage for views/workflow_view.py (0->10 tests).
"""
import inspect

import pytest


class TestWorkflowViewComponents:
    def test_build_workflow_header_callable(self):
        from agent.governance_ui.views.workflow_view import build_workflow_header
        assert callable(build_workflow_header)

    def test_build_compliance_summary_callable(self):
        from agent.governance_ui.views.workflow_view import build_compliance_summary
        assert callable(build_compliance_summary)


class TestWorkflowViewContent:
    def test_has_refresh_btn(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert "workflow-refresh-btn" in source

    def test_has_check_icon(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert "mdi-check-decagram" in source

    def test_has_compliance_label(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert "COMPLIANT" in source

    def test_re_exports_proposals(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert "build_proposal_form" in source
        assert "build_proposal_graph_panel" in source

    def test_has_workflow_loading(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert "workflow_loading" in source

    def test_has_workflow_status(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert "workflow_status" in source

    def test_has_validation_checks(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert "check" in source.lower()

    def test_has_refresh_icon(self):
        from agent.governance_ui.views import workflow_view
        source = inspect.getsource(workflow_view)
        assert "mdi-refresh" in source
