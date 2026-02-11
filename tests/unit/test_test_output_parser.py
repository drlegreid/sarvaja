"""
Unit tests for Test Output Parser and Evidence Generator.

Per DOC-SIZE-01-v1: Tests for extracted routes/tests/parser.py.
Tests: parse_pytest_summary, parse_pytest_output, generate_evidence_file.
"""

import pytest
from pathlib import Path

from governance.routes.tests.parser import (
    parse_pytest_summary,
    parse_pytest_output,
    generate_evidence_file,
)


class TestParsePytestSummary:
    """Tests for parse_pytest_summary()."""

    def test_all_passed(self):
        output = "====== 96 passed in 2.49s ======"
        result = parse_pytest_summary(output)
        assert result["passed"] == 96
        assert result["failed"] == 0

    def test_mixed_results(self):
        output = "====== 3 failed, 96 passed, 5 deselected in 2.49s ======"
        result = parse_pytest_summary(output)
        assert result["passed"] == 96
        assert result["failed"] == 3
        assert result["deselected"] == 5

    def test_with_skipped(self):
        output = "====== 90 passed, 5 skipped in 1.5s ======"
        result = parse_pytest_summary(output)
        assert result["passed"] == 90
        assert result["skipped"] == 5

    def test_empty_output(self):
        result = parse_pytest_summary("")
        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_multiline_output(self):
        output = """FAILED tests/test_foo.py::test_bar
short test summary info
====== 1 failed, 99 passed in 5.00s ======"""
        result = parse_pytest_summary(output)
        assert result["failed"] == 1
        assert result["passed"] == 99


class TestParsePytestOutput:
    """Tests for parse_pytest_output()."""

    def test_verbose_output(self):
        output = """tests/test_foo.py::test_bar PASSED
tests/test_foo.py::test_baz FAILED
tests/test_foo.py::test_qux SKIPPED"""
        result = parse_pytest_output(output)
        assert len(result) == 3
        assert result[0]["outcome"] == "passed"
        assert result[1]["outcome"] == "failed"
        assert result[2]["outcome"] == "skipped"

    def test_empty_output(self):
        result = parse_pytest_output("")
        assert result == []

    def test_quiet_mode_failures(self):
        output = """
======================== FAILURES ========================
___________________ test_something ___________________
    def test_something():
>       assert False
"""
        result = parse_pytest_output(output)
        assert len(result) >= 1
        assert result[0]["outcome"] == "failed"

    def test_nodeids_extracted(self):
        output = "tests/unit/test_foo.py::TestBar::test_baz PASSED"
        result = parse_pytest_output(output)
        assert result[0]["nodeid"] == "tests/unit/test_foo.py::TestBar::test_baz"


class TestGenerateEvidenceFile:
    """Tests for generate_evidence_file()."""

    def test_generates_file(self, tmp_path, monkeypatch):
        import governance.routes.tests.parser as parser_mod
        monkeypatch.setattr(parser_mod, "EVIDENCE_DIR", tmp_path)

        result_data = {
            "status": "completed",
            "passed": 10,
            "failed": 0,
            "total": 10,
            "timestamp": "2026-02-11T10:00:00",
            "duration_seconds": 5.0,
            "command": "pytest tests/",
            "output": "10 passed",
            "tests": [{"nodeid": "test_a", "outcome": "passed"}],
        }
        filepath = generate_evidence_file("RUN-001", result_data)
        assert filepath is not None
        assert Path(filepath).exists()
        content = Path(filepath).read_text()
        assert "RUN-001" in content
        assert "PASSED" in content

    def test_with_category(self, tmp_path, monkeypatch):
        import governance.routes.tests.parser as parser_mod
        monkeypatch.setattr(parser_mod, "EVIDENCE_DIR", tmp_path)

        result_data = {"status": "completed", "passed": 5, "failed": 0, "total": 5}
        filepath = generate_evidence_file("RUN-002", result_data, category="unit")
        assert filepath is not None
        assert "UNIT" in Path(filepath).name

    def test_failed_tests_partial(self, tmp_path, monkeypatch):
        import governance.routes.tests.parser as parser_mod
        monkeypatch.setattr(parser_mod, "EVIDENCE_DIR", tmp_path)

        result_data = {"status": "completed", "passed": 8, "failed": 2, "total": 10}
        filepath = generate_evidence_file("RUN-003", result_data)
        content = Path(filepath).read_text()
        assert "PARTIAL" in content

    def test_error_returns_none(self, tmp_path, monkeypatch):
        import governance.routes.tests.parser as parser_mod
        monkeypatch.setattr(parser_mod, "EVIDENCE_DIR", tmp_path / "nonexistent" / "deep")

        # Force an error by using a path that can't be created
        # Actually mkdir(parents=True) would succeed, so let's make it a file
        blocker = tmp_path / "blocker"
        blocker.write_text("not a dir")
        monkeypatch.setattr(parser_mod, "EVIDENCE_DIR", blocker / "sub")

        result_data = {"status": "completed", "passed": 0, "failed": 0, "total": 0}
        filepath = generate_evidence_file("RUN-ERR", result_data)
        assert filepath is None
