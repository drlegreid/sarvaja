"""
Unit tests for certification report generator.

Per RD-TESTING-STRATEGY TEST-005: GitHub milestone certification reporting.

Tests:
- Report generation from evidence
- Markdown report formatting
- JSON report output
- Coverage statistics
"""

import json
import pytest
import tempfile
from pathlib import Path

from tests.evidence.certification_report import (
    CertificationReportGenerator,
    CertificationReport,
    TestResult,
    generate_certification,
)


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_test_result_creation(self):
        """Test creating a TestResult."""
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

        assert result.category == "unit"
        assert result.status == "passed"
        assert "RULE-001" in result.linked_rules

    def test_test_result_defaults(self):
        """Test TestResult default values."""
        result = TestResult(
            test_id="test_example",
            name="test_example",
            category="unit",
            status="passed",
            duration_ms=0.0,
        )

        assert result.linked_rules == []
        assert result.linked_gaps == []
        assert result.error_message is None


class TestCertificationReport:
    """Tests for CertificationReport dataclass."""

    def test_report_creation(self):
        """Test creating a CertificationReport."""
        report = CertificationReport(
            report_id="CERT-2026-01-21",
            milestone="v1.0",
            total_tests=100,
            passed=95,
            failed=3,
            skipped=2,
        )

        assert report.report_id == "CERT-2026-01-21"
        assert report.milestone == "v1.0"
        assert report.passed == 95

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
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

        assert data["report_id"] == "CERT-TEST"
        assert data["statistics"]["passed"] == 8
        assert data["coverage"]["rules_covered"] == ["RULE-001", "RULE-002"]

    def test_report_defaults(self):
        """Test CertificationReport default values."""
        report = CertificationReport(report_id="TEST")

        assert report.total_tests == 0
        assert report.success_rate == "0%"
        assert report.rules_covered == []


class TestCertificationReportGenerator:
    """Tests for CertificationReportGenerator class."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = CertificationReportGenerator(
            evidence_dir="evidence/tests",
            milestone="v1.0",
            commit_sha="abc123",
        )

        assert generator.milestone == "v1.0"
        assert generator.commit_sha == "abc123"

    def test_format_duration(self):
        """Test duration formatting."""
        generator = CertificationReportGenerator()

        assert generator._format_duration(500) == "0.5s"
        assert generator._format_duration(5000) == "5.0s"
        assert "m" in generator._format_duration(90000)  # 1.5 minutes

    def test_generate_empty_report(self):
        """Test generating report with no evidence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = CertificationReportGenerator(evidence_dir=tmpdir)
            report = generator.generate_report()

            assert report.total_tests == 0
            assert report.success_rate == "0%"

    def test_generate_report_from_evidence(self):
        """Test generating report from evidence files."""
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

            # Verify
            assert report.total_tests == 2
            assert report.passed == 1
            assert report.failed == 1
            assert report.unit_tests == 1
            assert report.integration_tests == 1
            assert "RULE-001" in report.rules_covered
            assert "RULE-002" in report.rules_covered
            assert len(report.failed_tests) == 1

    def test_write_markdown_report(self):
        """Test writing markdown report."""
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

            # Verify file created
            assert output_path.exists()

            # Verify content
            content = output_path.read_text()
            assert "# Certification Report" in content
            assert "CERT-TEST" in content
            assert "v1.0" in content
            assert "95.0%" in content
            assert "RULE-001" in content

    def test_write_json_report(self):
        """Test writing JSON report."""
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

            # Verify file created
            assert output_path.exists()

            # Verify content is valid JSON
            with open(output_path) as f:
                data = json.load(f)

            assert data["report_id"] == "CERT-TEST"
            assert data["statistics"]["passed"] == 8

    def test_find_latest_run_dir(self):
        """Test finding the latest run directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple run directories
            import time

            for i in range(3):
                (Path(tmpdir) / f"run_{i}").mkdir()
                time.sleep(0.01)  # Small delay to ensure different mtimes

            generator = CertificationReportGenerator(evidence_dir=tmpdir)
            run_dir = generator._find_run_dir()

            assert run_dir is not None
            assert run_dir.name == "run_2"  # Most recent


class TestGenerateCertification:
    """Tests for the generate_certification function."""

    def test_generate_certification_function(self):
        """Test the CLI-compatible function."""
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

            # Verify result
            assert result["total_tests"] == 1
            assert result["passed"] == 1
            assert result["rules_covered"] == 1
            assert Path(result["markdown_report"]).exists()
            assert Path(result["json_report"]).exists()


class TestIntegration:
    """Integration tests for certification reporting."""

    def test_full_workflow(self):
        """Test complete certification workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir) / "evidence"
            output_dir = Path(tmpdir) / "output"

            # Create realistic evidence structure
            run_id = "2026-01-21_150000"
            run_dir = evidence_dir / run_id

            # Unit tests
            (run_dir / "unit").mkdir(parents=True)
            for i in range(5):
                test_data = {
                    "test_id": f"test_unit_{i}",
                    "name": f"test_unit_{i}",
                    "status": "passed" if i < 4 else "failed",
                    "duration_ms": 100 * i,
                    "linked_rules": [f"RULE-{i:03d}"],
                    "error_message": "Assertion failed" if i == 4 else None,
                }
                with open(run_dir / "unit" / f"test_{i}.json", "w") as f:
                    json.dump(test_data, f)

            # Integration tests
            (run_dir / "integration").mkdir()
            test_data = {
                "test_id": "test_integration",
                "name": "test_integration",
                "status": "passed",
                "duration_ms": 1000,
                "linked_rules": ["RULE-010"],
                "linked_gaps": ["GAP-001"],
            }
            with open(run_dir / "integration" / "test_int.json", "w") as f:
                json.dump(test_data, f)

            # Generate certification
            generator = CertificationReportGenerator(
                evidence_dir=str(evidence_dir),
                milestone="TEST-MILESTONE",
                commit_sha="abc123def456",
            )

            report = generator.generate_report(run_id=run_id)

            # Verify statistics
            assert report.total_tests == 6
            assert report.passed == 5
            assert report.failed == 1
            assert report.unit_tests == 5
            assert report.integration_tests == 1
            assert report.rule_coverage_count >= 5
            assert report.gap_coverage_count == 1
            assert len(report.failed_tests) == 1

            # Write reports
            md_path = generator.write_markdown_report(
                report, str(output_dir / "CERT.md")
            )
            json_path = generator.write_json_report(
                report, str(output_dir / "cert.json")
            )

            # Verify outputs
            assert md_path.exists()
            assert json_path.exists()

            # Verify markdown content
            md_content = md_path.read_text()
            assert "TEST-MILESTONE" in md_content
            assert "5" in md_content  # passed
            assert "1" in md_content  # failed
            assert "Failed Tests" in md_content

            # Verify JSON content
            with open(json_path) as f:
                json_data = json.load(f)
            assert json_data["statistics"]["passed"] == 5
            assert len(json_data["failed_tests"]) == 1
