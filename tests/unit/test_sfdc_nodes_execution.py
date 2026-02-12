"""
Unit tests for SFDC LangGraph Execution Nodes.

Per DOC-SIZE-01-v1: Tests for sfdc/langgraph/nodes_execution.py module.
Tests: develop_node, run_tests_node, deploy_node, validate_node, monitor_node, report_node.
"""

from governance.sfdc.langgraph.nodes_execution import (
    develop_node,
    run_tests_node,
    deploy_node,
    validate_node,
    monitor_node,
    report_node,
)


def _base_state(**kw):
    defaults = {
        "cycle_id": "SFDC-TEST-001",
        "org_alias": "sandbox1",
        "target_org": "sandbox1",
        "phases_completed": [],
        "phase_results": [],
        "metadata_components": [],
        "apex_classes": ["AccountTrigger"],
        "lwc_components": [],
        "flows": [],
        "dry_run": True,
        "retry_count": 0,
        "review_findings": [],
        "monitoring_alerts": [],
        "code_coverage": 0.0,
    }
    defaults.update(kw)
    return defaults


class TestDevelopNode:
    def test_dry_run(self):
        result = develop_node(_base_state())
        assert result["current_phase"] == "developed"
        assert "develop" in result["phases_completed"]

    def test_with_components(self):
        result = develop_node(_base_state(
            metadata_components=[
                {"name": "Acc", "status": "modified"},
                {"name": "New", "status": "created"},
            ],
        ))
        assert result["current_phase"] == "developed"


class TestRunTestsNode:
    def test_dry_run(self):
        result = run_tests_node(_base_state())
        assert result["current_phase"] == "tested"
        assert result["test_results"]["total"] >= 5
        assert result["code_coverage"] == 78.0
        assert result["coverage_met"] is True  # 78 >= 75

    def test_retry_higher_coverage(self):
        result = run_tests_node(_base_state(retry_count=1))
        assert result["code_coverage"] == 82.5

    def test_production(self):
        result = run_tests_node(_base_state(dry_run=False))
        assert result["coverage_met"] is False


class TestDeployNode:
    def test_dry_run(self):
        result = deploy_node(_base_state())
        assert result["current_phase"] == "deployed"
        assert result["deployment_id"] is not None
        assert result["deployment_status"] == "Succeeded"

    def test_production(self):
        result = deploy_node(_base_state(dry_run=False))
        assert result["deployment_status"] == "Pending"


class TestValidateNode:
    def test_dry_run(self):
        result = validate_node(_base_state())
        assert result["current_phase"] == "validated"
        assert result["validation_passed"] is True

    def test_production(self):
        result = validate_node(_base_state(dry_run=False))
        assert result["validation_passed"] is False


class TestMonitorNode:
    def test_dry_run(self):
        result = monitor_node(_base_state())
        assert result["current_phase"] == "monitored"
        assert result["monitoring_alerts"] == []


class TestReportNode:
    def test_basic(self):
        result = report_node(_base_state())
        assert result["current_phase"] == "reported"
        assert "report" in result["phases_completed"]
