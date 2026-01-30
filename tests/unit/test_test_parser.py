"""
Tests for test output parser and evidence generator.

Per DOC-SIZE-01-v1: parser.py extracted from runner.py.
Validates pytest output parsing and evidence file generation.

Created: 2026-01-30
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from governance.routes.tests.parser import (
    parse_pytest_summary,
    parse_pytest_output,
    generate_evidence_file,
)


class TestParsePytestSummary:
    """Test pytest summary line parsing."""

    def test_all_passed(self):
        """Parse output with only passed tests."""
        output = "96 passed in 2.49s"
        result = parse_pytest_summary(output)
        assert result["passed"] == 96
        assert result["failed"] == 0
        assert result["skipped"] == 0

    def test_mixed_results(self):
        """Parse output with mixed results."""
        output = "3 failed, 96 passed, 5 skipped in 4.12s"
        result = parse_pytest_summary(output)
        assert result["passed"] == 96
        assert result["failed"] == 3
        assert result["skipped"] == 5

    def test_with_deselected(self):
        """Parse output with deselected tests."""
        output = "3 failed, 96 passed, 5 deselected in 2.49s"
        result = parse_pytest_summary(output)
        assert result["passed"] == 96
        assert result["failed"] == 3
        assert result["deselected"] == 5

    def test_no_summary_line(self):
        """Return zeros when no summary line found."""
        output = "some random output\nno summary here"
        result = parse_pytest_summary(output)
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_empty_output(self):
        """Handle empty output gracefully."""
        result = parse_pytest_summary("")
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_summary_with_extra_text(self):
        """Parse summary embedded in larger output."""
        output = """
collecting ... collected 100 items
test_foo.py ..F.s
FAILURES...
=== 1 failed, 97 passed, 2 skipped in 3.14s ===
"""
        result = parse_pytest_summary(output)
        assert result["passed"] == 97
        assert result["failed"] == 1
        assert result["skipped"] == 2


class TestParsePytestOutput:
    """Test verbose pytest output parsing."""

    def test_verbose_passed(self):
        """Parse verbose mode PASSED tests."""
        output = "tests/test_foo.py::test_bar PASSED\ntests/test_foo.py::test_baz PASSED"
        result = parse_pytest_output(output)
        assert len(result) == 2
        assert result[0]["outcome"] == "passed"
        assert result[1]["outcome"] == "passed"

    def test_verbose_failed(self):
        """Parse verbose mode FAILED tests."""
        output = "tests/test_foo.py::test_bar FAILED"
        result = parse_pytest_output(output)
        assert len(result) == 1
        assert result[0]["outcome"] == "failed"
        assert result[0]["nodeid"] == "tests/test_foo.py::test_bar"

    def test_verbose_skipped(self):
        """Parse verbose mode SKIPPED tests."""
        output = "tests/test_foo.py::test_bar SKIPPED"
        result = parse_pytest_output(output)
        assert len(result) == 1
        assert result[0]["outcome"] == "skipped"

    def test_mixed_verbose(self):
        """Parse mixed verbose output."""
        output = """tests/test_a.py::test_one PASSED
tests/test_a.py::test_two FAILED
tests/test_a.py::test_three SKIPPED"""
        result = parse_pytest_output(output)
        assert len(result) == 3
        assert result[0]["outcome"] == "passed"
        assert result[1]["outcome"] == "failed"
        assert result[2]["outcome"] == "skipped"

    def test_quiet_mode_failures(self):
        """Parse quiet mode FAILURES section."""
        output = """...F.
FAILURES
_________________________________ test_broken _________________________________
...
short test summary info
"""
        result = parse_pytest_output(output)
        assert len(result) == 1
        assert result[0]["nodeid"] == "test_broken"
        assert result[0]["outcome"] == "failed"

    def test_empty_output(self):
        """Handle empty output."""
        result = parse_pytest_output("")
        assert result == []

    def test_no_test_results(self):
        """Handle output with no recognizable test results."""
        output = "collecting items...\nno tests ran"
        result = parse_pytest_output(output)
        assert result == []


class TestGenerateEvidenceFile:
    """Test evidence file generation."""

    def test_generates_file(self, tmp_path):
        """Generate evidence file in specified directory."""
        with patch("governance.routes.tests.parser.EVIDENCE_DIR", tmp_path):
            result_data = {
                "status": "completed",
                "timestamp": "2026-01-30T10:00:00",
                "duration_seconds": 5.0,
                "total": 10,
                "passed": 10,
                "failed": 0,
                "skipped": 0,
                "tests": [{"nodeid": "test_foo", "outcome": "passed"}],
                "command": "pytest tests/",
                "output": "10 passed",
            }
            filepath = generate_evidence_file("20260130-100000", result_data, "unit")
            assert filepath is not None
            assert os.path.exists(filepath)
            content = Path(filepath).read_text()
            assert "PASSED" in content
            assert "20260130-100000" in content

    def test_failed_status(self, tmp_path):
        """Generate evidence for failed test run."""
        with patch("governance.routes.tests.parser.EVIDENCE_DIR", tmp_path):
            result_data = {
                "status": "failed",
                "timestamp": "2026-01-30T10:00:00",
                "duration_seconds": 2.0,
                "total": 5,
                "passed": 3,
                "failed": 2,
                "skipped": 0,
                "tests": [],
                "command": "pytest tests/",
                "output": "2 failed",
            }
            filepath = generate_evidence_file("run-001", result_data)
            assert filepath is not None
            content = Path(filepath).read_text()
            assert "FAILED" in content

    def test_partial_status(self, tmp_path):
        """Generate evidence for partial (completed with failures) run."""
        with patch("governance.routes.tests.parser.EVIDENCE_DIR", tmp_path):
            result_data = {
                "status": "completed",
                "total": 10,
                "passed": 8,
                "failed": 2,
                "tests": [],
            }
            filepath = generate_evidence_file("run-002", result_data)
            assert filepath is not None
            content = Path(filepath).read_text()
            assert "PARTIAL" in content

    def test_no_tests_captured(self, tmp_path):
        """Handle case with no individual test results."""
        with patch("governance.routes.tests.parser.EVIDENCE_DIR", tmp_path):
            result_data = {
                "status": "completed",
                "total": 5,
                "passed": 5,
                "failed": 0,
                "tests": [],
            }
            filepath = generate_evidence_file("run-003", result_data)
            content = Path(filepath).read_text()
            assert "No individual test results captured" in content

    def test_returns_none_on_error(self):
        """Return None when evidence generation fails."""
        with patch("governance.routes.tests.parser.EVIDENCE_DIR", Path("/nonexistent/readonly")):
            result = generate_evidence_file("run-fail", {"status": "error"})
            assert result is None
