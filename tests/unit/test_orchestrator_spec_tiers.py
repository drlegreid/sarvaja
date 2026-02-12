"""
Unit tests for 3-Tier Validation Spec Generator.

Per DOC-SIZE-01-v1: Tests for workflows/orchestrator/spec_tiers.py module.
Tests: generate_spec(), export_to_robot(), generate_specs_from_validation(),
       generate_batch_specs().
"""

from governance.workflows.orchestrator.spec_tiers import (
    generate_spec,
    export_to_robot,
    generate_specs_from_validation,
    generate_batch_specs,
)


class TestGenerateSpec:
    def test_api_spec(self):
        spec = generate_spec("T-1", "Health check", "/api/health")
        assert spec["task_id"] == "T-1"
        assert spec["mcp_tool"] == "rest-api"
        assert spec["spec_type"] == "api"
        assert "Feature:" in spec["tier_1"]
        assert "Scenario:" in spec["tier_2"]
        assert "Request:" in spec["tier_3"]

    def test_ui_spec(self):
        spec = generate_spec("T-2", "Dashboard", "/dashboard", spec_type="ui")
        assert spec["mcp_tool"] == "playwright"
        assert "dashboard" in spec["tier_1"]
        assert "navigate" in spec["tier_2"].lower()

    def test_post_method(self):
        body = {"name": "test"}
        spec = generate_spec("T-3", "Create", "/api/tasks",
                              method="POST", request_body=body)
        assert "Content-Type" in spec["tier_3"]
        assert '"name"' in spec["tier_3"]

    def test_tier_1_structure(self):
        spec = generate_spec("T-4", "Test desc", "/api/test")
        tier1 = spec["tier_1"]
        assert "Feature:" in tier1
        assert "As a" in tier1
        assert "I want to" in tier1
        assert "So that" in tier1

    def test_tier_2_api(self):
        spec = generate_spec("T-5", "Check", "/api/check", method="GET")
        assert "Given the governance API is running" in spec["tier_2"]
        assert "When I send GET to /api/check" in spec["tier_2"]

    def test_expected_status(self):
        spec = generate_spec("T-6", "Create", "/api/tasks",
                              method="POST", expected_status=201)
        assert "201" in spec["tier_3"]


class TestExportToRobot:
    def test_api_robot(self):
        spec = generate_spec("T-10", "Health", "/api/health")
        robot = export_to_robot(spec)
        assert "*** Settings ***" in robot
        assert "RequestsLibrary" in robot
        assert "T-10" in robot
        assert "Send GET Request" in robot

    def test_ui_robot(self):
        spec = generate_spec("T-11", "Dashboard", "/dashboard", spec_type="ui")
        robot = export_to_robot(spec)
        assert "Browser" in robot
        assert "Navigate To" in robot
        assert "Take Screenshot" in robot

    def test_tags(self):
        spec = generate_spec("T-12", "Test", "/api/test")
        robot = export_to_robot(spec)
        assert "spec-tier" in robot
        assert "TEST-SPEC-01-v1" in robot


class TestGenerateSpecsFromValidation:
    def test_with_endpoints(self):
        task = {
            "task_id": "T-20",
            "description": "Multi endpoint",
            "endpoints": [
                {"path": "/api/a", "method": "GET"},
                {"path": "/api/b", "method": "POST", "body": {"x": 1}},
            ],
        }
        specs = generate_specs_from_validation({}, task)
        assert len(specs) == 2
        assert specs[0]["endpoint"] == "/api/a"

    def test_with_ui_path(self):
        task = {"task_id": "T-21", "ui_path": "/dashboard/sessions"}
        specs = generate_specs_from_validation({}, task)
        assert len(specs) == 1
        assert specs[0]["spec_type"] == "ui"

    def test_default_health(self):
        task = {"task_id": "T-22"}
        specs = generate_specs_from_validation({}, task)
        assert len(specs) == 1
        assert specs[0]["endpoint"] == "/api/health"


class TestGenerateBatchSpecs:
    def test_batch(self):
        backlog = [
            {"task_id": "T-30", "description": "A", "priority": "HIGH"},
            {"task_id": "T-31", "description": "B", "priority": "LOW"},
        ]
        specs = generate_batch_specs(backlog)
        assert len(specs) == 2
        assert specs[0]["priority"] == "HIGH"
        assert specs[1]["priority"] == "LOW"

    def test_empty_backlog(self):
        assert generate_batch_specs([]) == []
