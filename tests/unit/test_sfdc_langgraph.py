"""
Tests for SFDC LangGraph Workflow.

Per TEST-GUARD-01: Test coverage for critical workflows

Created: 2026-02-09
"""

import pytest
from datetime import datetime

from governance.sfdc.langgraph import (
    SFDCState,
    create_initial_state,
    run_sfdc_workflow,
    build_sfdc_graph,
    LANGGRAPH_AVAILABLE,
    MIN_CODE_COVERAGE,
    MAX_DEPLOY_RETRIES,
    MAX_COMPONENTS_PER_DEPLOY,
    BREAKING_CHANGE_THRESHOLD,
    # Nodes
    start_node,
    discover_node,
    develop_node,
    run_tests_node,
    review_node,
    deploy_node,
    validate_node,
    monitor_node,
    report_node,
    complete_node,
    abort_node,
    rollback_node,
    skip_to_report_node,
    # Edges
    check_discover_status,
    check_phase_status,
    check_test_result,
    check_review_result,
    check_deploy_result,
    check_validation_result,
)


class TestSFDCState:
    """Tests for SFDC state creation."""

    def test_create_initial_state_defaults(self):
        """Test initial state has correct defaults."""
        state = create_initial_state()

        assert state["current_phase"] == "idle"
        assert state["status"] == "pending"
        assert state["phases_completed"] == []
        assert state["dry_run"] is False
        assert state["sandbox_only"] is True
        assert state["cycle_id"].startswith("SFDC-")
        assert state["org_alias"] == "default"

    def test_create_initial_state_with_options(self):
        """Test initial state respects options."""
        state = create_initial_state(
            org_alias="mydev",
            target_org="mysandbox",
            dry_run=True,
            sandbox_only=True,
        )

        assert state["org_alias"] == "mydev"
        assert state["target_org"] == "mysandbox"
        assert state["dry_run"] is True
        assert state["sandbox_only"] is True

    def test_create_initial_state_target_defaults_to_source(self):
        """Test target_org defaults to org_alias when not specified."""
        state = create_initial_state(org_alias="mydev")
        assert state["target_org"] == "mydev"

    def test_initial_state_has_all_required_fields(self):
        """Test initial state contains all SFDCState fields."""
        state = create_initial_state()

        required_fields = [
            "cycle_id", "org_alias", "target_org",
            "current_phase", "phases_completed", "phase_results",
            "metadata_components", "change_set", "dependencies",
            "apex_classes", "lwc_components", "flows", "custom_objects",
            "test_results", "code_coverage", "coverage_met",
            "review_findings", "security_scan_passed",
            "deployment_id", "deployment_status", "deployment_errors",
            "post_deploy_checks", "validation_passed",
            "monitoring_alerts",
            "has_breaking_changes", "should_skip_monitor",
            "retry_count",
            "dry_run", "sandbox_only",
            "status", "error_message", "abort_reason", "rollback_reason",
            "started_at", "completed_at",
        ]

        for field in required_fields:
            assert field in state, f"Missing field: {field}"

    def test_constants_are_reasonable(self):
        """Test SFDC constants have sensible values."""
        assert MIN_CODE_COVERAGE == 75.0
        assert MAX_DEPLOY_RETRIES == 3
        assert MAX_COMPONENTS_PER_DEPLOY == 500
        assert BREAKING_CHANGE_THRESHOLD == 10


class TestSFDCNodes:
    """Tests for individual SFDC phase nodes."""

    def test_start_node_success(self):
        """Test start node with valid sandbox org."""
        state = create_initial_state(org_alias="mydev", target_org="mysandbox")

        result = start_node(state)

        assert result["current_phase"] == "started"
        assert result["status"] == "running"
        assert "start" in result["phases_completed"]
        assert result["started_at"] is not None

    def test_start_node_blocks_production_deploy(self):
        """Test start node blocks production when sandbox_only=True."""
        state = create_initial_state(
            org_alias="mydev",
            target_org="production",
            sandbox_only=True,
        )

        result = start_node(state)

        assert result["status"] == "failed"
        assert "sandbox_only" in result["error_message"]

    def test_start_node_allows_production_in_dry_run(self):
        """Test start node allows production target in dry_run mode."""
        state = create_initial_state(
            org_alias="mydev",
            target_org="production",
            sandbox_only=True,
            dry_run=True,
        )

        result = start_node(state)

        assert result["current_phase"] == "started"
        assert result["status"] == "running"

    def test_start_node_allows_sandbox_keywords(self):
        """Test start node allows known sandbox keywords."""
        for target in ["my-sandbox", "dev-org", "uat-environment", "sit-test", "qa-org"]:
            state = create_initial_state(target_org=target, sandbox_only=True)
            result = start_node(state)
            assert result["status"] == "running", f"Failed for target: {target}"

    def test_discover_node_dry_run(self):
        """Test discover node in dry run mode."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start"]

        result = discover_node(state)

        assert result["current_phase"] == "discovered"
        assert len(result["metadata_components"]) > 0
        assert len(result["apex_classes"]) > 0
        assert len(result["change_set"]) > 0

    def test_discover_node_categorizes_components(self):
        """Test discover node correctly categorizes component types."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start"]

        result = discover_node(state)

        # Should have ApexClass and ApexTrigger
        assert len(result["apex_classes"]) >= 2
        # Should have LWC
        assert len(result["lwc_components"]) >= 1
        # Should have Flow
        assert len(result["flows"]) >= 1

    def test_develop_node(self):
        """Test develop node tracks retry count."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "discover"]
        state["metadata_components"] = [
            {"name": "Test", "type": "ApexClass", "status": "modified"},
        ]

        result = develop_node(state)

        assert result["current_phase"] == "developed"
        assert "develop" in result["phases_completed"]

    def test_test_node_passes_with_coverage(self):
        """Test test node with sufficient coverage."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "discover", "develop"]
        state["apex_classes"] = ["AccountService", "ContactTrigger"]
        state["retry_count"] = 1  # Second attempt gets 82.5% in dry run

        result = run_tests_node(state)

        assert result["current_phase"] == "tested"
        assert result["code_coverage"] >= MIN_CODE_COVERAGE
        assert result["coverage_met"] is True

    def test_test_node_first_attempt_coverage(self):
        """Test test node first attempt gets 78% coverage."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "discover", "develop"]
        state["apex_classes"] = ["AccountService"]
        state["retry_count"] = 0

        result = run_tests_node(state)

        assert result["code_coverage"] == 78.0
        assert result["coverage_met"] is True  # 78 >= 75

    def test_review_node_passes(self):
        """Test review node passes security scan."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "discover", "develop", "test"]
        state["apex_classes"] = ["AccountService"]

        result = review_node(state)

        assert result["current_phase"] == "reviewed"
        assert result["security_scan_passed"] is True
        assert len(result["review_findings"]) > 0

    def test_deploy_node_dry_run(self):
        """Test deploy node in dry run mode."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "discover", "develop", "test", "review"]
        state["metadata_components"] = [{"name": "Test", "type": "ApexClass"}]

        result = deploy_node(state)

        assert result["current_phase"] == "deployed"
        assert result["deployment_status"] == "Succeeded"
        assert result["deployment_id"] is not None

    def test_validate_node_passes(self):
        """Test validate node with dry run."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "discover", "develop", "test", "review", "deploy"]

        result = validate_node(state)

        assert result["current_phase"] == "validated"
        assert result["validation_passed"] is True
        assert len(result["post_deploy_checks"]) > 0

    def test_monitor_node(self):
        """Test monitor node in dry run."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "discover", "develop", "test", "review", "deploy", "validate"]

        result = monitor_node(state)

        assert result["current_phase"] == "monitored"
        assert result["monitoring_alerts"] == []

    def test_report_node(self):
        """Test report node generates summary."""
        state = create_initial_state(dry_run=True)
        state["phases_completed"] = ["start", "discover", "develop", "test", "review", "deploy", "validate", "monitor"]
        state["metadata_components"] = [{"name": "Test", "type": "ApexClass"}]
        state["code_coverage"] = 82.5
        state["deployment_id"] = "0Af123"

        result = report_node(state)

        assert result["current_phase"] == "reported"
        assert "report" in result["phases_completed"]

    def test_complete_node_success(self):
        """Test complete node with successful state."""
        state = create_initial_state()
        state["phases_completed"] = ["start", "discover", "develop", "test", "review", "deploy", "validate", "monitor", "report"]

        result = complete_node(state)

        assert result["current_phase"] == "complete"
        assert result["status"] == "success"
        assert result["completed_at"] is not None

    def test_complete_node_with_rollback(self):
        """Test complete node preserves rolled_back status."""
        state = create_initial_state()
        state["phases_completed"] = ["start", "discover", "develop", "deploy", "rollback", "report"]
        state["rollback_reason"] = "Validation failed"

        result = complete_node(state)

        assert result["status"] == "rolled_back"

    def test_complete_node_with_error(self):
        """Test complete node with error state."""
        state = create_initial_state()
        state["phases_completed"] = ["start"]
        state["error_message"] = "Connection failed"

        result = complete_node(state)

        assert result["status"] == "failed"

    def test_abort_node(self):
        """Test abort node records reason."""
        state = create_initial_state()
        state["phases_completed"] = ["start"]
        state["error_message"] = "Org unavailable"

        result = abort_node(state)

        assert result["current_phase"] == "aborted"
        assert result["status"] == "aborted"
        assert result["abort_reason"] == "Org unavailable"

    def test_rollback_node(self):
        """Test rollback node with deployment errors."""
        state = create_initial_state()
        state["phases_completed"] = ["start", "discover", "develop", "deploy"]
        state["deployment_errors"] = ["Component X failed", "Missing dependency"]
        state["deployment_id"] = "0Af123"

        result = rollback_node(state)

        assert result["current_phase"] == "rolled_back"
        assert "Deploy errors: 2" in result["rollback_reason"]

    def test_rollback_node_with_failed_checks(self):
        """Test rollback node with validation failure details."""
        state = create_initial_state()
        state["phases_completed"] = ["start", "discover", "develop", "deploy", "validate"]
        state["post_deploy_checks"] = {
            "apex_compilation": True,
            "integration_tests": False,
        }
        state["deployment_errors"] = []

        result = rollback_node(state)

        assert "Failed checks: integration_tests" in result["rollback_reason"]

    def test_skip_to_report_node(self):
        """Test skip_to_report sets should_skip_monitor."""
        state = create_initial_state()
        state["phases_completed"] = ["start", "discover"]

        result = skip_to_report_node(state)

        assert result["current_phase"] == "skipped_to_report"
        assert result["should_skip_monitor"] is True


class TestSFDCEdges:
    """Tests for SFDC conditional edge routing."""

    def test_check_discover_status_normal(self):
        """Test discover routing for normal flow."""
        state = create_initial_state()
        state["status"] = "running"
        state["has_breaking_changes"] = False

        assert check_discover_status(state) == "develop"

    def test_check_discover_status_breaking_changes(self):
        """Test discover routing with breaking changes."""
        state = create_initial_state()
        state["status"] = "running"
        state["has_breaking_changes"] = True

        assert check_discover_status(state) == "skip_to_report"

    def test_check_discover_status_failed(self):
        """Test discover routing on failure."""
        state = create_initial_state()
        state["status"] = "failed"

        assert check_discover_status(state) == "abort"

    def test_check_phase_status_continue(self):
        """Test generic phase check passes."""
        state = create_initial_state()
        state["status"] = "running"

        assert check_phase_status(state) == "continue"

    def test_check_phase_status_failed(self):
        """Test generic phase check fails."""
        state = create_initial_state()
        state["status"] = "failed"

        assert check_phase_status(state) == "abort"

    def test_check_test_result_pass(self):
        """Test routing when tests pass."""
        state = create_initial_state()
        state["status"] = "running"
        state["coverage_met"] = True

        assert check_test_result(state) == "continue"

    def test_check_test_result_fail_loops(self):
        """Test routing when tests fail, retries remain."""
        state = create_initial_state()
        state["status"] = "running"
        state["coverage_met"] = False
        state["retry_count"] = 0

        assert check_test_result(state) == "loop_to_develop"

    def test_check_test_result_fail_exhausted(self):
        """Test routing when tests fail, retries exhausted."""
        state = create_initial_state()
        state["status"] = "running"
        state["coverage_met"] = False
        state["retry_count"] = MAX_DEPLOY_RETRIES

        assert check_test_result(state) == "abort"

    def test_check_review_result_pass(self):
        """Test routing when review passes."""
        state = create_initial_state()
        state["status"] = "running"
        state["security_scan_passed"] = True

        assert check_review_result(state) == "continue"

    def test_check_review_result_security_fail(self):
        """Test routing when security scan fails."""
        state = create_initial_state()
        state["status"] = "running"
        state["security_scan_passed"] = False
        state["retry_count"] = 0

        assert check_review_result(state) == "loop_to_develop"

    def test_check_review_result_security_fail_exhausted(self):
        """Test routing when security fails, retries exhausted."""
        state = create_initial_state()
        state["status"] = "running"
        state["security_scan_passed"] = False
        state["retry_count"] = MAX_DEPLOY_RETRIES

        assert check_review_result(state) == "abort"

    def test_check_deploy_result_success(self):
        """Test routing when deploy succeeds."""
        state = create_initial_state()
        state["status"] = "running"
        state["deployment_status"] = "Succeeded"

        assert check_deploy_result(state) == "validate"

    def test_check_deploy_result_failed(self):
        """Test routing when deploy fails."""
        state = create_initial_state()
        state["status"] = "running"
        state["deployment_status"] = "Failed"

        assert check_deploy_result(state) == "rollback"

    def test_check_validation_result_passed(self):
        """Test routing when validation passes."""
        state = create_initial_state()
        state["status"] = "running"
        state["validation_passed"] = True

        assert check_validation_result(state) == "monitor"

    def test_check_validation_result_failed(self):
        """Test routing when validation fails."""
        state = create_initial_state()
        state["status"] = "running"
        state["validation_passed"] = False

        assert check_validation_result(state) == "rollback"

    def test_check_validation_result_skip_monitor(self):
        """Test routing when should skip monitor."""
        state = create_initial_state()
        state["status"] = "running"
        state["validation_passed"] = True
        state["should_skip_monitor"] = True

        assert check_validation_result(state) == "skip_monitor"


class TestSFDCGraph:
    """Tests for SFDC graph construction."""

    def test_build_graph(self):
        """Test graph builds without error."""
        graph = build_sfdc_graph()

        assert graph is not None
        assert len(graph.nodes) == 13  # All SFDC phase nodes

    def test_graph_has_all_nodes(self):
        """Test graph contains all required nodes."""
        graph = build_sfdc_graph()

        expected_nodes = [
            "start", "discover", "develop", "test", "review",
            "deploy", "validate", "monitor", "report", "complete",
            "abort", "rollback", "skip_to_report",
        ]

        for node in expected_nodes:
            assert node in graph.nodes, f"Missing node: {node}"


class TestSFDCWorkflowExecution:
    """Tests for full workflow execution."""

    def test_run_workflow_dry_run(self):
        """Test full workflow in dry run mode."""
        result = run_sfdc_workflow(
            org_alias="mydev",
            dry_run=True,
        )

        assert result["status"] in ("success", "failed")
        assert len(result["phases_completed"]) > 0
        assert result["completed_at"] is not None

    def test_run_workflow_full_success_path(self):
        """Test dry run completes all phases."""
        result = run_sfdc_workflow(
            org_alias="mydev",
            target_org="mysandbox",
            dry_run=True,
        )

        # Should complete successfully through all phases
        assert result["status"] == "success"
        # Should have gone through core phases
        assert "start" in result["phases_completed"]
        assert "discover" in result["phases_completed"]
        assert "complete" in result["phases_completed"]

    def test_run_workflow_sandbox_only_blocks_production(self):
        """Test workflow blocks production deployment."""
        result = run_sfdc_workflow(
            org_alias="mydev",
            target_org="production",
            sandbox_only=True,
            dry_run=False,
        )

        # Should fail or abort
        assert result["status"] in ("failed", "aborted")

    def test_run_workflow_with_target_org(self):
        """Test workflow with explicit target org."""
        result = run_sfdc_workflow(
            org_alias="mydev",
            target_org="mysandbox",
            dry_run=True,
        )

        assert result["target_org"] == "mysandbox"


class TestLangGraphAvailability:
    """Tests for LangGraph availability handling."""

    def test_langgraph_available_flag(self):
        """Test LangGraph availability flag is set."""
        assert isinstance(LANGGRAPH_AVAILABLE, bool)

    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_workflow_with_langgraph(self):
        """Test workflow uses real LangGraph when available."""
        result = run_sfdc_workflow(
            org_alias="mydev",
            dry_run=True,
        )

        assert result is not None
        assert "cycle_id" in result
