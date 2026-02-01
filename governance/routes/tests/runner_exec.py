"""
Test Execution Functions (DOC-SIZE-01-v1 split from runner.py)

Background task functions for running pytest and regression suites.
Separated from router endpoints for clarity and size compliance.

Created: 2026-02-01
"""
import logging
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from governance.routes.tests.parser import (
    parse_pytest_summary,
    parse_pytest_output,
    generate_evidence_file,
)
from governance.routes.tests.runner_store import (
    _resolve_test_root,
    _test_results,
    _persist_result,
)

logger = logging.getLogger(__name__)


def execute_tests(run_id: str, cmd: list, category: str = None):
    """Execute pytest and store results with evidence generation."""
    start_time = datetime.now()
    test_root = _resolve_test_root()
    logger.info(f"Test run {run_id}: cmd={cmd}, cwd={test_root}, category={category}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=test_root,
        )
        duration = (datetime.now() - start_time).total_seconds()

        output = result.stdout + result.stderr
        tests = parse_pytest_output(output)
        summary = parse_pytest_summary(output)
        passed = summary["passed"]
        failed = summary["failed"]
        skipped = summary["skipped"]
        total = passed + failed + skipped

        test_result = {
            "status": "completed" if result.returncode == 0 else "failed",
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "exit_code": result.returncode,
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "tests": tests,
            "output": output[-5000:] if len(output) > 5000 else output,
            "command": " ".join(cmd),
            "category": category,
        }

        evidence_path = generate_evidence_file(run_id, test_result, category)
        if evidence_path:
            test_result["evidence_file"] = evidence_path

        _test_results[run_id] = test_result
        try:
            _persist_result(run_id, test_result)
        except Exception as pe:
            logger.warning(f"Failed to persist test result: {pe}")

    except subprocess.TimeoutExpired:
        timeout_result = {
            "status": "timeout",
            "timestamp": start_time.isoformat(),
            "error": "Test run exceeded 5 minute timeout",
            "category": category,
        }
        _test_results[run_id] = timeout_result
        try:
            _persist_result(run_id, timeout_result)
        except Exception:
            pass
    except Exception as e:
        error_result = {
            "status": "error",
            "timestamp": start_time.isoformat(),
            "error": str(e),
            "category": category,
        }
        _test_results[run_id] = error_result
        try:
            _persist_result(run_id, error_result)
        except Exception:
            pass


def execute_regression(run_id: str, skip_dynamic: bool = False):
    """Execute full regression and store results."""
    start_time = datetime.now()
    try:
        from governance.routes.tests.regression_runner import run_regression

        result = run_regression(skip_dynamic=skip_dynamic)
        duration = (datetime.now() - start_time).total_seconds()

        test_result = {
            "status": "completed" if result["verdict"] == "PASS" else "failed",
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "category": "regression",
            "verdict": result["verdict"],
            "total": sum(p.get("total", 0) for p in result["phases"]),
            "passed": sum(p.get("passed", 0) for p in result["phases"]),
            "failed": sum(p.get("failed", 0) for p in result["phases"]),
            "skipped": sum(p.get("skipped", 0) for p in result["phases"]),
            "phases": result["phases"],
            "summary": result["summary"],
            "command": f"regression (skip_dynamic={skip_dynamic})",
        }

        evidence_path = generate_evidence_file(run_id, test_result, "regression")
        if evidence_path:
            test_result["evidence_file"] = evidence_path

        _test_results[run_id] = test_result
        try:
            _persist_result(run_id, test_result)
        except Exception as pe:
            logger.warning(f"Failed to persist regression result: {pe}")

    except Exception as e:
        _test_results[run_id] = {
            "status": "error",
            "timestamp": start_time.isoformat(),
            "error": str(e),
            "category": "regression",
        }
        try:
            _persist_result(run_id, _test_results[run_id])
        except Exception:
            pass


def parse_robot_xml(test_root: str) -> dict:
    """Parse Robot Framework output.xml for summary stats."""
    project_root = Path(test_root)
    output_xml = project_root / "output.xml"

    if not output_xml.exists():
        return {"available": False, "message": "No Robot Framework output.xml found"}

    try:
        tree = ET.parse(str(output_xml))
        root = tree.getroot()

        stats_elem = root.find(".//statistics/total/stat")
        total_pass = int(stats_elem.get("pass", 0)) if stats_elem is not None else 0
        total_fail = int(stats_elem.get("fail", 0)) if stats_elem is not None else 0
        total_skip = int(stats_elem.get("skip", 0)) if stats_elem is not None else 0

        generated = root.get("generated", "")

        suites = []
        for suite_stat in root.findall(".//statistics/suite/stat"):
            suites.append({
                "name": suite_stat.text or suite_stat.get("name", ""),
                "pass": int(suite_stat.get("pass", 0)),
                "fail": int(suite_stat.get("fail", 0)),
            })

        return {
            "available": True,
            "generated": generated,
            "total": total_pass + total_fail + total_skip,
            "passed": total_pass,
            "failed": total_fail,
            "skipped": total_skip,
            "suites": suites,
            "report_exists": (project_root / "report.html").exists(),
            "log_exists": (project_root / "log.html").exists(),
        }
    except Exception as e:
        return {"available": False, "message": f"Error parsing output.xml: {e}"}
