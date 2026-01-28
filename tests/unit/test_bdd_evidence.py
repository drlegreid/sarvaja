"""
Unit Tests for BDD Evidence Module.

Per GAP-TEST-EVIDENCE-001: File-based test evidence with BDD structure.
Per TDD: Tests written before implementation validation.

Created: 2026-01-21
"""

import json
import tempfile
from pathlib import Path

import pytest

from tests.evidence.collector import (
    BDDEvidenceCollector,
    BDDStep,
    StepType,
    EvidenceRecord,
)
from tests.evidence.rule_linker import RuleLinker


# =============================================================================
# BDDStep Tests
# =============================================================================

class TestBDDStep:
    """Tests for BDDStep dataclass."""

    def test_step_creation(self):
        """BDDStep creates with required fields."""
        step = BDDStep(
            step_type=StepType.GIVEN,
            description="a user exists"
        )
        assert step.step_type == StepType.GIVEN
        assert step.description == "a user exists"
        assert step.passed is True
        assert step.data is None

    def test_step_with_data(self):
        """BDDStep accepts optional data dictionary."""
        step = BDDStep(
            step_type=StepType.WHEN,
            description="user submits form",
            data={"email": "test@example.com"}
        )
        assert step.data == {"email": "test@example.com"}

    def test_step_to_dict(self):
        """BDDStep serializes to dictionary."""
        step = BDDStep(
            step_type=StepType.THEN,
            description="user is logged in",
            passed=True,
            duration_ms=50.0
        )
        result = step.to_dict()

        assert result["type"] == "then"
        assert result["description"] == "user is logged in"
        assert result["passed"] is True
        assert result["duration_ms"] == 50.0

    def test_step_failed_with_error(self):
        """Failed step includes error message."""
        step = BDDStep(
            step_type=StepType.THEN,
            description="assertion fails",
            passed=False,
            error="Expected True but got False"
        )
        result = step.to_dict()

        assert result["passed"] is False
        assert result["error"] == "Expected True but got False"


# =============================================================================
# EvidenceRecord Tests
# =============================================================================

class TestEvidenceRecord:
    """Tests for EvidenceRecord dataclass."""

    def test_evidence_creation(self):
        """EvidenceRecord creates with required fields."""
        evidence = EvidenceRecord(
            test_id="tests/test_example.py::test_login",
            name="test_login",
            category="unit",
            status="passed",
            duration_ms=150.0,
            intent="User login validates credentials"
        )

        assert evidence.test_id == "tests/test_example.py::test_login"
        assert evidence.name == "test_login"
        assert evidence.status == "passed"
        assert evidence.intent == "User login validates credentials"
        assert evidence.steps == []

    def test_evidence_with_steps(self):
        """EvidenceRecord includes BDD steps."""
        evidence = EvidenceRecord(
            test_id="test_login",
            name="test_login",
            category="unit",
            status="passed",
            duration_ms=150.0,
            intent="Login test",
            steps=[
                BDDStep(StepType.GIVEN, "user exists"),
                BDDStep(StepType.WHEN, "user logs in"),
                BDDStep(StepType.THEN, "user is authenticated"),
            ]
        )

        assert len(evidence.steps) == 3
        assert evidence.steps[0].step_type == StepType.GIVEN

    def test_evidence_with_rule_links(self):
        """EvidenceRecord includes rule and gap links."""
        evidence = EvidenceRecord(
            test_id="test_rule_compliance",
            name="test_rule_compliance",
            category="integration",
            status="passed",
            duration_ms=200.0,
            intent="RULE-001 compliance test",
            linked_rules=["RULE-001", "SESSION-EVID-01-v1"],
            linked_gaps=["GAP-TEST-001"]
        )

        assert "RULE-001" in evidence.linked_rules
        assert "SESSION-EVID-01-v1" in evidence.linked_rules
        assert "GAP-TEST-001" in evidence.linked_gaps

    def test_evidence_to_dict(self):
        """EvidenceRecord serializes to dictionary."""
        evidence = EvidenceRecord(
            test_id="test_example",
            name="test_example",
            category="unit",
            status="passed",
            duration_ms=100.0,
            intent="Example test",
            linked_rules=["RULE-001"],
            linked_gaps=["GAP-001"]
        )
        result = evidence.to_dict()

        assert result["test_id"] == "test_example"
        assert result["status"] == "passed"
        assert result["linked_rules"] == ["RULE-001"]
        assert result["linked_gaps"] == ["GAP-001"]
        assert "bdd_steps" in result
        assert "timestamp" in result


# =============================================================================
# BDDEvidenceCollector Tests
# =============================================================================

class TestBDDEvidenceCollector:
    """Tests for BDDEvidenceCollector class."""

    def test_collector_initialization(self):
        """Collector initializes with defaults."""
        collector = BDDEvidenceCollector()

        assert collector.base_dir == Path("evidence/tests")
        assert collector.session_id is None
        assert collector.run_id is None

    def test_collector_with_session(self):
        """Collector accepts session ID for linking."""
        collector = BDDEvidenceCollector(
            session_id="SESSION-2026-01-21-TEST"
        )

        assert collector.session_id == "SESSION-2026-01-21-TEST"

    def test_start_run_creates_directory(self, tmp_path):
        """start_run creates run directory structure."""
        collector = BDDEvidenceCollector(base_dir=str(tmp_path))
        run_id = collector.start_run()

        assert run_id is not None
        assert collector.run_dir is not None
        assert collector.run_dir.exists()
        assert (collector.run_dir / "unit").exists()
        assert (collector.run_dir / "integration").exists()
        assert (collector.run_dir / "e2e").exists()

    def test_record_bdd_steps(self, tmp_path):
        """Collector records BDD Given/When/Then steps."""
        collector = BDDEvidenceCollector(base_dir=str(tmp_path))
        collector.start_run()
        collector.start_test("test_login", "unit", "User login test")

        collector.given("a registered user exists", {"email": "test@example.com"})
        collector.when("the user submits valid credentials")
        collector.then("the user is logged in")

        evidence = collector.end_test("passed", duration_ms=100.0)

        assert evidence is not None
        assert len(evidence.steps) == 3
        assert evidence.steps[0].step_type == StepType.GIVEN
        assert evidence.steps[0].data == {"email": "test@example.com"}
        assert evidence.steps[1].step_type == StepType.WHEN
        assert evidence.steps[2].step_type == StepType.THEN

    def test_end_test_saves_evidence_file(self, tmp_path):
        """end_test writes evidence JSON file."""
        collector = BDDEvidenceCollector(base_dir=str(tmp_path))
        collector.start_run()
        collector.start_test("test_example", "unit", "Example test")
        collector.given("setup complete")
        collector.end_test("passed", duration_ms=50.0)

        # Check file was created
        evidence_files = list((collector.run_dir / "unit").glob("*.json"))
        assert len(evidence_files) == 1

        # Verify content
        with open(evidence_files[0]) as f:
            data = json.load(f)
        assert data["test_id"] == "test_example"
        assert data["status"] == "passed"
        assert len(data["bdd_steps"]) == 1

    def test_end_run_generates_summary(self, tmp_path):
        """end_run generates summary.json with statistics."""
        collector = BDDEvidenceCollector(
            base_dir=str(tmp_path),
            session_id="SESSION-TEST"
        )
        collector.start_run()

        # Record a few tests
        collector.start_test("test_1", "unit", "Test 1", rules=["RULE-001"])
        collector.end_test("passed", duration_ms=100.0)

        collector.start_test("test_2", "unit", "Test 2", gaps=["GAP-001"])
        collector.end_test("failed", duration_ms=50.0, error="Assertion failed")

        collector.start_test("test_3", "integration", "Test 3")
        collector.end_test("skipped")

        summary = collector.end_run()

        assert summary["total_tests"] == 3
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["skipped"] == 1
        assert summary["session_id"] == "SESSION-TEST"
        assert "RULE-001" in summary["linked_rules"]
        assert "GAP-001" in summary["linked_gaps"]

        # Verify summary file exists
        assert (collector.run_dir / "summary.json").exists()


# =============================================================================
# RuleLinker Tests
# =============================================================================

class TestRuleLinker:
    """Tests for RuleLinker class."""

    def test_extract_legacy_rule_ids(self):
        """Linker extracts legacy RULE-XXX IDs."""
        linker = RuleLinker()
        rules, gaps = linker.extract_references(
            "This test validates RULE-001 and RULE-012 compliance."
        )

        assert "RULE-001" in rules
        assert "RULE-012" in rules

    def test_extract_semantic_rule_ids(self):
        """Linker extracts semantic rule IDs."""
        linker = RuleLinker()
        rules, gaps = linker.extract_references(
            "Per SESSION-EVID-01-v1: Evidence collection test."
        )

        assert "SESSION-EVID-01-v1" in rules

    def test_extract_gap_ids(self):
        """Linker extracts GAP-XXX IDs."""
        linker = RuleLinker()
        rules, gaps = linker.extract_references(
            "Addresses GAP-MCP-001 and GAP-UI-AUDIT-001."
        )

        assert "GAP-MCP-001" in gaps
        assert "GAP-UI-AUDIT-001" in gaps

    def test_register_test_combines_sources(self):
        """register_test combines docstring and explicit markers."""
        linker = RuleLinker()
        rules, gaps = linker.register_test(
            test_id="test_combined",
            docstring="Tests RULE-001 compliance.",
            rules=["RULE-002"],
            gaps=["GAP-001"]
        )

        assert "RULE-001" in rules  # From docstring
        assert "RULE-002" in rules  # From explicit
        assert "GAP-001" in gaps

    def test_get_tests_for_rule(self):
        """get_tests_for_rule returns tests validating a rule."""
        linker = RuleLinker()
        linker.register_test("test_a", rules=["RULE-001", "RULE-002"])
        linker.register_test("test_b", rules=["RULE-001"])
        linker.register_test("test_c", rules=["RULE-003"])

        tests = linker.get_tests_for_rule("RULE-001")

        assert "test_a" in tests
        assert "test_b" in tests
        assert "test_c" not in tests

    def test_coverage_summary(self):
        """get_coverage_summary returns statistics."""
        linker = RuleLinker()
        linker.register_test("test_a", rules=["RULE-001"])
        linker.register_test("test_b", gaps=["GAP-001"])
        linker.register_test("test_c")  # No links

        summary = linker.get_coverage_summary()

        assert summary["total_tests"] == 3
        assert summary["linked_tests"] == 2
        assert summary["unique_rules"] == 1
        assert summary["unique_gaps"] == 1


# =============================================================================
# Integration Test: Full Workflow
# =============================================================================

class TestFullWorkflow:
    """Integration test for complete BDD evidence workflow."""

    @pytest.mark.rules("GAP-TEST-EVIDENCE-001")
    @pytest.mark.intent("Full BDD evidence collection workflow")
    def test_complete_evidence_workflow(self, tmp_path):
        """
        Complete workflow: collect evidence, link rules, generate summary.

        Per GAP-TEST-EVIDENCE-001: File-based evidence with BDD structure.
        """
        # Setup
        collector = BDDEvidenceCollector(
            base_dir=str(tmp_path),
            session_id="SESSION-2026-01-21-TEST"
        )
        linker = RuleLinker()

        # Start run
        run_id = collector.start_run("test-run-001")
        assert run_id == "test-run-001"

        # Register and run test 1 (passing)
        test1_id = "tests/unit/test_auth.py::test_login_success"
        rules, gaps = linker.register_test(
            test1_id,
            docstring="Per RULE-001: Authentication test.",
            rules=["SESSION-EVID-01-v1"]
        )

        collector.start_test(
            test1_id, "unit",
            "User login with valid credentials succeeds",
            rules=rules, gaps=gaps
        )
        collector.given("a registered user exists", {"email": "user@test.com"})
        collector.when("the user submits valid credentials")
        collector.then("the user receives an auth token")
        collector.and_step("the token is valid for 24 hours")

        evidence1 = collector.end_test("passed", duration_ms=150.0)
        assert evidence1.status == "passed"
        assert len(evidence1.steps) == 4

        # Register and run test 2 (failing)
        test2_id = "tests/unit/test_auth.py::test_login_invalid_password"
        collector.start_test(
            test2_id, "unit",
            "User login with invalid password fails",
            gaps=["GAP-TEST-EVIDENCE-001"]
        )
        collector.given("a registered user exists")
        collector.when("the user submits invalid password")
        collector.then("the login attempt fails")
        collector.mark_step_failed("Expected 401, got 200")

        evidence2 = collector.end_test(
            "failed",
            duration_ms=100.0,
            error="AssertionError: Expected 401, got 200"
        )
        assert evidence2.status == "failed"
        assert evidence2.steps[-1].passed is False

        # End run
        summary = collector.end_run()

        # Verify summary
        assert summary["total_tests"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["success_rate"] == "50.0%"
        assert "RULE-001" in summary["linked_rules"]
        assert "SESSION-EVID-01-v1" in summary["linked_rules"]
        assert "GAP-TEST-EVIDENCE-001" in summary["linked_gaps"]

        # Verify files exist
        run_dir = tmp_path / "test-run-001"
        assert (run_dir / "summary.json").exists()
        assert len(list((run_dir / "unit").glob("*.json"))) == 2
