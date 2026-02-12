"""
Unit tests for SFDC LangGraph State Schema.

Per DOC-SIZE-01-v1: Tests for sfdc/langgraph/state.py module.
Tests: PhaseResult, MetadataComponent, SFDCState, constants, create_initial_state().
"""

from governance.sfdc.langgraph.state import (
    PhaseResult,
    MetadataComponent,
    SFDCState,
    MIN_CODE_COVERAGE,
    RECOMMENDED_COVERAGE,
    MAX_DEPLOY_RETRIES,
    MAX_CYCLE_HOURS,
    MAX_COMPONENTS_PER_DEPLOY,
    BREAKING_CHANGE_THRESHOLD,
    create_initial_state,
)


class TestConstants:
    def test_coverage_thresholds(self):
        assert MIN_CODE_COVERAGE == 75.0
        assert RECOMMENDED_COVERAGE == 85.0
        assert RECOMMENDED_COVERAGE > MIN_CODE_COVERAGE

    def test_cycle_limits(self):
        assert MAX_DEPLOY_RETRIES == 3
        assert MAX_CYCLE_HOURS == 8

    def test_component_thresholds(self):
        assert MAX_COMPONENTS_PER_DEPLOY == 500
        assert BREAKING_CHANGE_THRESHOLD == 10


class TestTypedDicts:
    def test_phase_result(self):
        pr: PhaseResult = {
            "phase": "discover",
            "status": "success",
            "findings": 5,
            "metrics": {"count": 10},
            "error": None,
            "duration_ms": 1200,
        }
        assert pr["phase"] == "discover"
        assert pr["status"] == "success"

    def test_metadata_component(self):
        mc: MetadataComponent = {
            "name": "AccountTrigger",
            "type": "ApexClass",
            "status": "modified",
            "api_version": "59.0",
        }
        assert mc["type"] == "ApexClass"
        assert mc["status"] == "modified"


class TestCreateInitialState:
    def test_defaults(self):
        state = create_initial_state()
        assert state["org_alias"] == "default"
        assert state["target_org"] == "default"
        assert state["current_phase"] == "idle"
        assert state["status"] == "pending"
        assert state["dry_run"] is False
        assert state["sandbox_only"] is True
        assert state["retry_count"] == 0
        assert state["code_coverage"] == 0.0

    def test_custom_org(self):
        state = create_initial_state(org_alias="myorg", target_org="prod")
        assert state["org_alias"] == "myorg"
        assert state["target_org"] == "prod"

    def test_dry_run(self):
        state = create_initial_state(dry_run=True)
        assert state["dry_run"] is True

    def test_sandbox_false(self):
        state = create_initial_state(sandbox_only=False)
        assert state["sandbox_only"] is False

    def test_cycle_id_format(self):
        state = create_initial_state()
        assert state["cycle_id"].startswith("SFDC-")

    def test_empty_lists(self):
        state = create_initial_state()
        assert state["phases_completed"] == []
        assert state["phase_results"] == []
        assert state["metadata_components"] == []
        assert state["apex_classes"] == []
        assert state["deployment_errors"] == []

    def test_none_fields(self):
        state = create_initial_state()
        assert state["deployment_id"] is None
        assert state["error_message"] is None
        assert state["started_at"] is None

    def test_target_defaults_to_org(self):
        state = create_initial_state(org_alias="sandbox1")
        assert state["target_org"] == "sandbox1"

    def test_boolean_defaults(self):
        state = create_initial_state()
        assert state["has_breaking_changes"] is False
        assert state["should_skip_monitor"] is False
        assert state["coverage_met"] is False
        assert state["security_scan_passed"] is False
        assert state["validation_passed"] is False
