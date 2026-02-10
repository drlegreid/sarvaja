"""
Tests for 3-Tier Validation Spec Generator.

Per TEST-SPEC-01-v1: Validation produces 3-tier Gherkin-style specs:
  Tier 1 - Business Intent (what/why)
  Tier 2 - Technical Intent (what/how - validations/retries/cycles)
  Tier 3 - Low-Level Details (API requests/responses, UI interactions)

TDD RED phase — tests written before implementation.
"""

import pytest
from typing import Dict, Any


# ============================================================================
# Tier Structure Tests
# ============================================================================


class TestSpecTierStructure:
    """Verify the 3-tier spec structure and format."""

    def test_generate_spec_returns_three_tiers(self):
        """Spec generator produces exactly 3 tiers."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-TEST-001",
            description="Fix session lifecycle",
            endpoint="/api/sessions",
            method="GET",
        )
        assert "tier_1" in result
        assert "tier_2" in result
        assert "tier_3" in result

    def test_tier_1_has_business_intent(self):
        """Tier 1 contains Feature, As-a, I-want, So-that."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-TEST-001",
            description="Fix session lifecycle",
            endpoint="/api/sessions",
        )
        t1 = result["tier_1"]
        assert "Feature:" in t1
        assert "As a" in t1 or "As an" in t1
        assert "I want" in t1
        assert "So that" in t1

    def test_tier_2_has_technical_intent(self):
        """Tier 2 contains Scenario with Given/When/Then and technical details."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-TEST-001",
            description="Fix session lifecycle",
            endpoint="/api/sessions",
        )
        t2 = result["tier_2"]
        assert "Scenario:" in t2
        assert "Given" in t2
        assert "When" in t2
        assert "Then" in t2

    def test_tier_3_has_low_level_details(self):
        """Tier 3 contains request method, endpoint, expected status."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-TEST-001",
            description="Fix session lifecycle",
            endpoint="/api/sessions",
            method="GET",
        )
        t3 = result["tier_3"]
        assert "GET" in t3
        assert "/api/sessions" in t3
        assert "200" in t3 or "status" in t3.lower()

    def test_tier_3_includes_headers_for_post(self):
        """Tier 3 for POST includes Content-Type header."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-TEST-001",
            description="Create session",
            endpoint="/api/sessions",
            method="POST",
            request_body={"topic": "test"},
        )
        t3 = result["tier_3"]
        assert "Content-Type" in t3 or "application/json" in t3
        assert "POST" in t3

    def test_spec_includes_task_id(self):
        """All tiers reference the originating task_id."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-UI-005",
            description="Fix date display",
            endpoint="/api/sessions",
        )
        assert "GAP-UI-005" in result["tier_1"]
        assert "GAP-UI-005" in result["tier_2"]


# ============================================================================
# Robot Framework Export Tests
# ============================================================================


class TestSpecToRobotFramework:
    """Verify specs can be exported as Robot Framework test cases."""

    def test_export_produces_robot_syntax(self):
        """Exported Robot Framework contains *** Test Cases ***."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_spec,
            export_to_robot,
        )

        spec = generate_spec(
            task_id="GAP-TEST-001",
            description="Session CRUD",
            endpoint="/api/sessions",
        )
        robot_text = export_to_robot(spec)
        assert "*** Test Cases ***" in robot_text
        assert "*** Settings ***" in robot_text

    def test_export_includes_documentation(self):
        """Robot Framework export has Documentation with tier 1 business intent."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_spec,
            export_to_robot,
        )

        spec = generate_spec(
            task_id="GAP-TEST-001",
            description="Session CRUD",
            endpoint="/api/sessions",
        )
        robot_text = export_to_robot(spec)
        assert "Documentation" in robot_text

    def test_export_includes_tags(self):
        """Robot Framework export includes task_id as tag."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_spec,
            export_to_robot,
        )

        spec = generate_spec(
            task_id="GAP-TEST-001",
            description="Session CRUD",
            endpoint="/api/sessions",
        )
        robot_text = export_to_robot(spec)
        assert "GAP-TEST-001" in robot_text

    def test_export_has_given_when_then_keywords(self):
        """Robot Framework export uses Given/When/Then BDD keywords."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_spec,
            export_to_robot,
        )

        spec = generate_spec(
            task_id="GAP-TEST-001",
            description="Session CRUD",
            endpoint="/api/sessions",
            method="GET",
        )
        robot_text = export_to_robot(spec)
        # RF BDD: Given/When/Then as keyword prefixes
        assert "Given" in robot_text or "When" in robot_text


# ============================================================================
# Validation Integration Tests
# ============================================================================


class TestSpecFromValidation:
    """Verify specs generated from orchestrator validation results."""

    def test_generate_from_validation_result(self):
        """Given an orchestrator validation result, generate specs."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_specs_from_validation,
        )

        validation_result = {
            "tests_passed": True,
            "heuristics_passed": True,
            "task_id": "GAP-SESSION-001",
        }
        task = {
            "task_id": "GAP-SESSION-001",
            "priority": "HIGH",
            "description": "Fix session evidence capture",
        }
        specs = generate_specs_from_validation(validation_result, task)
        assert isinstance(specs, list)
        assert len(specs) >= 1
        assert "tier_1" in specs[0]

    def test_generate_from_validation_with_endpoint_hints(self):
        """Validation with endpoint hints produces targeted specs."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_specs_from_validation,
        )

        validation_result = {
            "tests_passed": True,
            "heuristics_passed": True,
            "task_id": "GAP-API-001",
        }
        task = {
            "task_id": "GAP-API-001",
            "priority": "CRITICAL",
            "description": "Session API returns 500 on empty body",
            "endpoints": [
                {"path": "/api/sessions", "method": "POST"},
                {"path": "/api/sessions", "method": "GET"},
            ],
        }
        specs = generate_specs_from_validation(validation_result, task)
        assert len(specs) >= 2  # One per endpoint
        methods = [s.get("method") for s in specs]
        assert "POST" in methods
        assert "GET" in methods

    def test_generate_with_ui_task_includes_playwright(self):
        """UI-related tasks should include Playwright interaction hints."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_specs_from_validation,
        )

        validation_result = {
            "tests_passed": True,
            "heuristics_passed": True,
            "task_id": "GAP-UI-001",
        }
        task = {
            "task_id": "GAP-UI-001",
            "priority": "HIGH",
            "description": "Dashboard sessions table not loading",
            "ui_path": "/sessions",
        }
        specs = generate_specs_from_validation(validation_result, task)
        assert len(specs) >= 1
        # UI specs should have playwright-relevant tier_3
        ui_spec = specs[0]
        t3 = ui_spec["tier_3"]
        assert "navigate" in t3.lower() or "click" in t3.lower() or "screenshot" in t3.lower()


# ============================================================================
# MCP Dynamic Test Hints
# ============================================================================


class TestMCPTestHints:
    """Verify specs include MCP tool references for dynamic testing."""

    def test_rest_api_spec_references_mcp(self):
        """REST API specs reference rest-api MCP for dynamic testing."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-TEST-001",
            description="Session API health",
            endpoint="/api/health",
            method="GET",
        )
        # Metadata should indicate MCP tool for dynamic execution
        assert result.get("mcp_tool") == "rest-api"

    def test_ui_spec_references_playwright_mcp(self):
        """UI specs reference playwright MCP for dynamic testing."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-UI-001",
            description="Dashboard loads",
            endpoint="http://localhost:8081",
            method="NAVIGATE",
            spec_type="ui",
        )
        assert result.get("mcp_tool") == "playwright"

    def test_spec_metadata_complete(self):
        """Spec includes complete metadata for MCP execution."""
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="GAP-TEST-001",
            description="Session CRUD",
            endpoint="/api/sessions",
            method="GET",
        )
        assert "task_id" in result
        assert "endpoint" in result
        assert "method" in result
        assert "mcp_tool" in result
        assert "tier_1" in result
        assert "tier_2" in result
        assert "tier_3" in result


# ============================================================================
# Batch Spec Generation
# ============================================================================


class TestBatchSpecGeneration:
    """Verify batch generation from orchestrator backlog."""

    def test_generate_batch_from_backlog(self):
        """Given a backlog, generate specs for all tasks."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_batch_specs,
        )

        backlog = [
            {"task_id": "GAP-001", "priority": "HIGH", "description": "Fix sessions"},
            {"task_id": "GAP-002", "priority": "MEDIUM", "description": "Fix tasks"},
        ]
        all_specs = generate_batch_specs(backlog)
        assert len(all_specs) == 2
        assert all_specs[0]["task_id"] == "GAP-001"
        assert all_specs[1]["task_id"] == "GAP-002"

    def test_batch_preserves_priority(self):
        """Batch specs maintain priority from backlog."""
        from governance.workflows.orchestrator.spec_tiers import (
            generate_batch_specs,
        )

        backlog = [
            {"task_id": "GAP-001", "priority": "CRITICAL", "description": "Critical fix"},
        ]
        all_specs = generate_batch_specs(backlog)
        assert all_specs[0].get("priority") == "CRITICAL"
