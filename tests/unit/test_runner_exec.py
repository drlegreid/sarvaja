"""
Unit tests for Test Execution Functions.

Per DOC-SIZE-01-v1: Tests for routes/tests/runner_exec.py module.
Tests: execute_tests, execute_regression, execute_heuristic, parse_robot_xml.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from unittest.mock import patch, MagicMock

from governance.routes.tests.runner_exec import (
    execute_tests,
    execute_regression,
    execute_heuristic,
    parse_robot_xml,
)

_P_STORE = "governance.routes.tests.runner_exec._test_results"
_P_PERSIST = "governance.routes.tests.runner_exec._persist_result"
_P_ROOT = "governance.routes.tests.runner_exec._resolve_test_root"
_P_PARSE_OUT = "governance.routes.tests.runner_exec.parse_pytest_output"
_P_PARSE_SUM = "governance.routes.tests.runner_exec.parse_pytest_summary"
_P_EVIDENCE = "governance.routes.tests.runner_exec.generate_evidence_file"


class TestExecuteTests:
    @patch(_P_EVIDENCE, return_value=None)
    @patch(_P_PARSE_SUM, return_value={"passed": 5, "failed": 0, "skipped": 1})
    @patch(_P_PARSE_OUT, return_value=[{"name": "test_a", "status": "passed"}])
    @patch(_P_ROOT, return_value="/tmp")
    @patch("subprocess.run")
    def test_success(self, mock_run, _root, _out, _sum, _ev):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="5 passed", stderr="",
        )
        store = {}
        with patch(_P_STORE, store), patch(_P_PERSIST):
            execute_tests("RUN-1", ["pytest", "-q"])
            assert store["RUN-1"]["status"] == "completed"
            assert store["RUN-1"]["passed"] == 5
            assert store["RUN-1"]["total"] == 6

    @patch(_P_EVIDENCE, return_value=None)
    @patch(_P_PARSE_SUM, return_value={"passed": 3, "failed": 2, "skipped": 0})
    @patch(_P_PARSE_OUT, return_value=[])
    @patch(_P_ROOT, return_value="/tmp")
    @patch("subprocess.run")
    def test_failure(self, mock_run, _root, _out, _sum, _ev):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="3 passed, 2 failed", stderr="",
        )
        store = {}
        with patch(_P_STORE, store), patch(_P_PERSIST):
            execute_tests("RUN-2", ["pytest", "-q"])
            assert store["RUN-2"]["status"] == "failed"

    @patch(_P_ROOT, return_value="/tmp")
    @patch("subprocess.run", side_effect=Exception("boom"))
    def test_exception(self, _run, _root):
        store = {}
        with patch(_P_STORE, store), patch(_P_PERSIST):
            execute_tests("RUN-3", ["pytest"])
            assert store["RUN-3"]["status"] == "error"
            assert "Test execution failed: Exception" in store["RUN-3"]["error"]

    @patch(_P_ROOT, return_value="/tmp")
    def test_timeout(self, _root):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 300)):
            store = {}
            with patch(_P_STORE, store), patch(_P_PERSIST):
                execute_tests("RUN-4", ["pytest"])
                assert store["RUN-4"]["status"] == "timeout"


class TestExecuteHeuristic:
    def test_success(self):
        mock_result = {
            "summary": {"total": 10, "passed": 8, "failed": 0, "skipped": 2, "errors": 0},
            "checks": [{"id": "H-001", "status": "PASS"}],
        }
        store = {}
        with patch("governance.routes.tests.heuristic_runner.run_heuristic_checks",
                   return_value=mock_result), \
             patch(_P_STORE, store), patch(_P_PERSIST):
            execute_heuristic("HEUR-1")
            assert store["HEUR-1"]["status"] == "completed"
            assert store["HEUR-1"]["total"] == 10

    def test_with_failures(self):
        mock_result = {
            "summary": {"total": 10, "passed": 7, "failed": 3, "skipped": 0, "errors": 0},
            "checks": [],
        }
        store = {}
        with patch("governance.routes.tests.heuristic_runner.run_heuristic_checks",
                   return_value=mock_result), \
             patch(_P_STORE, store), patch(_P_PERSIST):
            execute_heuristic("HEUR-2")
            assert store["HEUR-2"]["status"] == "failed"


class TestParseRobotXml:
    def test_no_file(self, tmp_path):
        result = parse_robot_xml(str(tmp_path))
        assert result["available"] is False

    def test_valid_xml(self, tmp_path):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<robot generated="2026-02-11T10:00:00">
  <statistics>
    <total>
      <stat pass="5" fail="1" skip="2">All Tests</stat>
    </total>
    <suite>
      <stat pass="3" fail="0" name="Suite A">Suite A</stat>
      <stat pass="2" fail="1" name="Suite B">Suite B</stat>
    </suite>
  </statistics>
</robot>"""
        (tmp_path / "output.xml").write_text(xml_content)
        result = parse_robot_xml(str(tmp_path))
        assert result["available"] is True
        assert result["total"] == 8
        assert result["passed"] == 5
        assert result["failed"] == 1
        assert len(result["suites"]) == 2

    def test_invalid_xml(self, tmp_path):
        (tmp_path / "output.xml").write_text("not xml")
        result = parse_robot_xml(str(tmp_path))
        assert result["available"] is False
