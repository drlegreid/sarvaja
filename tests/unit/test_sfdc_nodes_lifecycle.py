"""
Unit tests for SFDC LangGraph Lifecycle Nodes.

Per DOC-SIZE-01-v1: Tests for sfdc/langgraph/nodes_lifecycle.py module.
Tests: _create_phase_result, start_node, complete_node, abort_node,
       rollback_node, skip_to_report_node.
"""

from governance.sfdc.langgraph.nodes_lifecycle import (
    _create_phase_result,
    start_node,
    complete_node,
    abort_node,
    rollback_node,
    skip_to_report_node,
)


def _base_state(**kw):
    defaults = {
        "cycle_id": "SFDC-TEST-001",
        "org_alias": "sandbox1",
        "target_org": "sandbox1",
        "phases_completed": [],
        "phase_results": [],
        "review_findings": [],
        "deployment_errors": [],
        "post_deploy_checks": {},
        "validation_passed": True,
        "dry_run": True,
        "sandbox_only": True,
        "metadata_components": [],
        "apex_classes": [],
        "lwc_components": [],
    }
    defaults.update(kw)
    return defaults


class TestCreatePhaseResult:
    def test_basic(self):
        result = _create_phase_result("deploy", "success", _base_state())
        assert result["phase"] == "deploy"
        assert result["status"] == "success"

    def test_with_findings(self):
        state = _base_state(review_findings=[
            {"phase": "deploy"}, {"phase": "other"},
        ])
        result = _create_phase_result("deploy", "success", state)
        assert result["findings"] == 1


class TestStartNode:
    def test_dry_run(self):
        result = start_node(_base_state())
        assert result["current_phase"] == "started"
        assert result["status"] == "running"

    def test_sandbox_only_blocks_prod(self):
        result = start_node(_base_state(
            dry_run=False, sandbox_only=True, target_org="production",
        ))
        assert result["current_phase"] == "start_failed"
        assert "production" in result["error_message"]

    def test_sandbox_allows_sandbox(self):
        result = start_node(_base_state(
            dry_run=False, sandbox_only=True, target_org="dev-sandbox",
        ))
        assert result["current_phase"] == "started"


class TestCompleteNode:
    def test_success(self):
        result = complete_node(_base_state())
        assert result["status"] == "success"

    def test_rolled_back(self):
        result = complete_node(_base_state(rollback_reason="bad deploy"))
        assert result["status"] == "rolled_back"

    def test_failed(self):
        result = complete_node(_base_state(error_message="timeout"))
        assert result["status"] == "failed"

    def test_aborted(self):
        result = complete_node(_base_state(abort_reason="cancel"))
        assert result["status"] == "aborted"


class TestAbortNode:
    def test_basic(self):
        result = abort_node(_base_state(error_message="critical"))
        assert result["status"] == "aborted"
        assert result["abort_reason"] == "critical"

    def test_default(self):
        result = abort_node(_base_state())
        assert result["abort_reason"] == "Unknown reason"


class TestRollbackNode:
    def test_with_errors(self):
        result = rollback_node(_base_state(
            deployment_errors=["error1"],
        ))
        assert "Deploy errors" in result["rollback_reason"]

    def test_with_failed_checks(self):
        result = rollback_node(_base_state(
            validation_passed=False,
            post_deploy_checks={"apex_compilation": True, "lwc_rendering": False},
        ))
        assert "lwc_rendering" in result["rollback_reason"]

    def test_default_reason(self):
        result = rollback_node(_base_state())
        assert "failed" in result["rollback_reason"].lower()


class TestSkipToReportNode:
    def test_basic(self):
        result = skip_to_report_node(_base_state())
        assert result["current_phase"] == "skipped_to_report"
        assert result["should_skip_monitor"] is True
