"""
RF-004: Robot Framework Library for Certification Report.

Wraps tests/evidence/certification_report.py for Robot Framework tests.
Per RD-TESTING-STRATEGY TEST-005: GitHub milestone certification reporting.
"""

import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CertificationReportLibrary:
    """Robot Framework library for Certification Report testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._generator = None
        self._temp_dirs = []

    # =========================================================================
    # TestResult Tests
    # =========================================================================

    def create_test_result(self) -> Dict[str, Any]:
        """Create a TestResult with all fields."""
        from tests.evidence.certification_report import TestResult

        result = TestResult(
            test_id="tests/test_rules.py::test_rule_creation",
            name="test_rule_creation",
            category="unit",
            status="passed",
            duration_ms=150.5,
            intent="Verify rule creation works",
            linked_rules=["RULE-001"],
            linked_gaps=["GAP-001"],
        )
        return {
            "category": result.category,
            "status": result.status,
            "has_rule": "RULE-001" in result.linked_rules
        }

    def test_result_defaults(self) -> Dict[str, Any]:
        """Create TestResult with defaults."""
        from tests.evidence.certification_report import TestResult

        result = TestResult(
            test_id="test_example",
            name="test_example",
            category="unit",
            status="passed",
            duration_ms=0.0,
        )
        return {
            "linked_rules": result.linked_rules,
            "linked_gaps": result.linked_gaps,
            "error_message": result.error_message
        }

    # =========================================================================
    # CertificationReport Tests
    # =========================================================================

    def create_certification_report(self) -> Dict[str, Any]:
        """Create a CertificationReport."""
        from tests.evidence.certification_report import CertificationReport

        report = CertificationReport(
            report_id="CERT-2026-01-21",
            milestone="v1.0",
            total_tests=100,
            passed=95,
            failed=3,
            skipped=2,
        )
        return {
            "report_id": report.report_id,
            "milestone": report.milestone,
            "passed": report.passed
        }

    def report_to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        from tests.evidence.certification_report import CertificationReport

        report = CertificationReport(
            report_id="CERT-TEST",
            total_tests=10,
            passed=8,
            failed=2,
            skipped=0,
            success_rate="80.0%",
            rules_covered=["RULE-001", "RULE-002"],
        )
        data = report.to_dict()
        return {
            "report_id": data["report_id"],
            "passed": data["statistics"]["passed"],
            "rules_covered": data["coverage"]["rules_covered"]
        }

    def report_defaults(self) -> Dict[str, Any]:
        """Check report default values."""
        from tests.evidence.certification_report import CertificationReport

        report = CertificationReport(report_id="TEST")
        return {
            "total_tests": report.total_tests,
            "success_rate": report.success_rate,
            "rules_covered": report.rules_covered
        }

    # =========================================================================
    # CertificationReportGenerator Tests
    # =========================================================================

    def generator_initialization(self) -> Dict[str, Any]:
        """Test generator initialization."""
        from tests.evidence.certification_report import CertificationReportGenerator

        generator = CertificationReportGenerator(
            evidence_dir="evidence/tests",
            milestone="v1.0",
            commit_sha="abc123",
        )
        return {
            "milestone": generator.milestone,
            "commit_sha": generator.commit_sha
        }

    def format_duration(self) -> Dict[str, Any]:
        """Test duration formatting."""
        from tests.evidence.certification_report import CertificationReportGenerator

        generator = CertificationReportGenerator()
        return {
            "500ms": generator._format_duration(500),
            "5000ms": generator._format_duration(5000),
            "90000ms": generator._format_duration(90000)
        }

    def generate_empty_report(self) -> Dict[str, Any]:
        """Generate report with no evidence."""
        from tests.evidence.certification_report import CertificationReportGenerator

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = CertificationReportGenerator(evidence_dir=tmpdir)
            report = generator.generate_report()
            return {
                "total_tests": report.total_tests,
                "success_rate": report.success_rate
            }

    def generate_report_from_evidence(self) -> Dict[str, Any]:
        """Generate report from evidence files."""
        from tests.evidence.certification_report import CertificationReportGenerator

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create evidence structure
            run_dir = Path(tmpdir) / "2026-01-21_150000"
            (run_dir / "unit").mkdir(parents=True)
            (run_dir / "integration").mkdir(parents=True)

            # Create sample evidence files
            unit_test = {
                "test_id": "test_example",
                "name": "test_example",
                "status": "passed",
                "duration_ms": 100,
                "linked_rules": ["RULE-001"],
                "linked_gaps": ["GAP-001"],
            }
            with open(run_dir / "unit" / "test_example.json", "w") as f:
                json.dump(unit_test, f)

            int_test = {
                "test_id": "test_integration",
                "name": "test_integration",
                "status": "failed",
                "duration_ms": 500,
                "error_message": "Connection timeout",
                "linked_rules": ["RULE-002"],
            }
            with open(run_dir / "integration" / "test_integration.json", "w") as f:
                json.dump(int_test, f)

            # Generate report
            generator = CertificationReportGenerator(
                evidence_dir=tmpdir,
                milestone="v1.0",
            )
            report = generator.generate_report(run_id="2026-01-21_150000")

            return {
                "total_tests": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "unit_tests": report.unit_tests,
                "integration_tests": report.integration_tests,
                "has_rule_001": "RULE-001" in report.rules_covered,
                "has_rule_002": "RULE-002" in report.rules_covered,
                "failed_tests_count": len(report.failed_tests)
            }

    def write_markdown_report(self) -> Dict[str, Any]:
        """Test writing markdown report."""
        from tests.evidence.certification_report import (
            CertificationReportGenerator,
            CertificationReport
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            report = CertificationReport(
                report_id="CERT-TEST",
                milestone="v1.0",
                commit_sha="abc123def",
                total_tests=100,
                passed=95,
                failed=3,
                skipped=2,
                success_rate="95.0%",
                rules_covered=["RULE-001", "RULE-002"],
                gaps_addressed=["GAP-001"],
                rule_coverage_count=2,
                gap_coverage_count=1,
            )

            generator = CertificationReportGenerator()
            output_path = Path(tmpdir) / "CERT.md"
            generator.write_markdown_report(report, str(output_path))

            content = output_path.read_text()
            return {
                "file_exists": output_path.exists(),
                "has_header": "# Certification Report" in content,
                "has_report_id": "CERT-TEST" in content,
                "has_milestone": "v1.0" in content,
                "has_rate": "95.0%" in content,
                "has_rule": "RULE-001" in content
            }

    def write_json_report(self) -> Dict[str, Any]:
        """Test writing JSON report."""
        from tests.evidence.certification_report import (
            CertificationReportGenerator,
            CertificationReport
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            report = CertificationReport(
                report_id="CERT-TEST",
                total_tests=10,
                passed=8,
                failed=2,
            )

            generator = CertificationReportGenerator()
            output_path = Path(tmpdir) / "cert.json"
            generator.write_json_report(report, str(output_path))

            with open(output_path) as f:
                data = json.load(f)

            return {
                "file_exists": output_path.exists(),
                "report_id": data["report_id"],
                "passed": data["statistics"]["passed"]
            }

    def find_latest_run_dir(self) -> bool:
        """Test finding the latest run directory."""
        from tests.evidence.certification_report import CertificationReportGenerator
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple run directories
            for i in range(3):
                (Path(tmpdir) / f"run_{i}").mkdir()
                time.sleep(0.01)

            generator = CertificationReportGenerator(evidence_dir=tmpdir)
            run_dir = generator._find_run_dir()

            return run_dir is not None and run_dir.name == "run_2"

    def generate_certification_function(self) -> Dict[str, Any]:
        """Test the CLI-compatible function."""
        from tests.evidence.certification_report import generate_certification

        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir) / "evidence"
            output_dir = Path(tmpdir) / "output"

            # Create minimal evidence
            run_dir = evidence_dir / "test_run"
            (run_dir / "unit").mkdir(parents=True)

            test_data = {
                "test_id": "test_example",
                "name": "test_example",
                "status": "passed",
                "duration_ms": 50,
                "linked_rules": ["RULE-001"],
            }
            with open(run_dir / "unit" / "test.json", "w") as f:
                json.dump(test_data, f)

            # Generate certification
            result = generate_certification(
                evidence_dir=str(evidence_dir),
                output_dir=str(output_dir),
                milestone="v1.0",
                commit_sha="abc123",
                run_id="test_run",
            )

            return {
                "total_tests": result["total_tests"],
                "passed": result["passed"],
                "rules_covered": result["rules_covered"],
                "markdown_exists": Path(result["markdown_report"]).exists(),
                "json_exists": Path(result["json_report"]).exists()
            }
