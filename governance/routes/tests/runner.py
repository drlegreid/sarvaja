"""
Test Runner API - Self-Assessment Endpoints
Per WORKFLOW-SHELL-01-v1: Run tests in container for health evidence
Per TEST-FIX-01-v1: Tests produce traceable evidence files
Per UI-AUDIT-010: Evidence file linkage for Test Runner

Created: 2026-01-17
Updated: 2026-01-20 - Added evidence file generation
"""
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Query, BackgroundTasks
from pydantic import BaseModel

from governance.routes.tests.parser import (
    parse_pytest_summary,
    parse_pytest_output,
    generate_evidence_file,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/tests", tags=["tests"])


class TestResult(BaseModel):
    """Individual test result."""
    nodeid: str
    outcome: str  # passed, failed, skipped
    duration: float
    error: Optional[str] = None


class TestRunSummary(BaseModel):
    """Test run summary."""
    timestamp: str
    status: str  # running, completed, failed
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    tests: List[TestResult]


# In-memory store for test results (simple approach)
_test_results: dict = {}


@router.get("/categories")
async def list_test_categories():
    """
    List available test categories.

    Returns categories mapped to test file patterns.
    """
    return {
        "categories": [
            {"id": "unit", "name": "Unit Tests", "pattern": "tests/test_*.py", "description": "Fast unit tests"},
            {"id": "governance", "name": "Governance", "pattern": "tests/test_governance*.py", "description": "TypeDB governance tests"},
            {"id": "ui", "name": "UI Tests", "pattern": "tests/test_*_ui.py", "description": "Dashboard UI tests"},
            {"id": "kanren", "name": "Kanren", "pattern": "tests/test_kanren*.py", "description": "Constraint engine tests"},
            {"id": "api", "name": "API Tests", "pattern": "tests/test_api*.py", "description": "REST API tests"},
            {"id": "e2e", "name": "E2E Health", "pattern": "tests/e2e/test_platform_health_e2e.py", "description": "Platform health E2E"},
        ]
    }


@router.post("/run")
async def run_tests(
    background_tasks: BackgroundTasks,
    category: Optional[str] = Query(None, description="Test category to run"),
    pattern: Optional[str] = Query(None, description="Custom test pattern"),
    markers: Optional[str] = Query(None, description="Pytest markers (e.g., 'not slow')"),
):
    """
    Run tests and return results.

    Uses pytest in JSON output mode for structured results.
    """
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Build pytest command
    cmd = ["python3", "-m", "pytest", "--tb=short", "-q"]

    # Determine test pattern
    if pattern:
        cmd.append(pattern)
    elif category:
        patterns = {
            "unit": "tests/test_governance.py",
            "governance": "tests/test_governance.py tests/test_governance_ui.py",
            "ui": "tests/test_governance_ui.py tests/test_task_ui.py",
            "kanren": "tests/test_kanren_constraints.py",
            "api": "tests/test_data_integrity.py",
            "e2e": "tests/e2e/test_platform_health_e2e.py",
        }
        cmd.extend(patterns.get(category, "tests/").split())
    else:
        cmd.append("tests/test_governance.py")  # Default: fast governance tests

    # Add markers if specified
    if markers:
        cmd.extend(["-m", markers])

    # Skip slow/integration tests by default for quick feedback
    if not markers and category not in ["e2e"]:
        cmd.extend(["-k", "not Integration and not slow"])

    # Initialize result
    _test_results[run_id] = {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "command": " ".join(cmd),
    }

    # Run in background for async response
    background_tasks.add_task(_execute_tests, run_id, cmd, category)

    return {"run_id": run_id, "status": "started", "command": " ".join(cmd), "category": category}


@router.get("/results/{run_id}")
async def get_test_results(run_id: str):
    """Get results for a specific test run."""
    if run_id not in _test_results:
        return {"error": "Run not found", "run_id": run_id}
    return _test_results[run_id]


@router.get("/results")
async def list_test_results(limit: int = Query(10, le=50)):
    """List recent test run results."""
    sorted_runs = sorted(_test_results.items(), key=lambda x: x[0], reverse=True)
    return {"runs": [{"run_id": k, **v} for k, v in sorted_runs[:limit]]}


@router.get("/robot/summary")
async def get_robot_summary():
    """Parse Robot Framework output.xml for summary stats."""
    project_root = Path("/app") if Path("/app").exists() else Path(".")
    output_xml = project_root / "output.xml"

    if not output_xml.exists():
        return {"available": False, "message": "No Robot Framework output.xml found"}

    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(str(output_xml))
        root = tree.getroot()

        # Parse <statistics> section
        stats_elem = root.find(".//statistics/total/stat")
        total_pass = int(stats_elem.get("pass", 0)) if stats_elem is not None else 0
        total_fail = int(stats_elem.get("fail", 0)) if stats_elem is not None else 0
        total_skip = int(stats_elem.get("skip", 0)) if stats_elem is not None else 0

        # Get generation timestamp
        generated = root.get("generated", "")

        # Get suite-level stats
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


@router.get("/robot/report")
async def serve_robot_report(file: str = Query("report.html")):
    """Serve Robot Framework report HTML files."""
    from fastapi.responses import FileResponse

    allowed_files = {"report.html", "log.html"}
    if file not in allowed_files:
        return {"error": f"File not allowed. Choose from: {allowed_files}"}

    project_root = Path("/app") if Path("/app").exists() else Path(".")
    file_path = project_root / file

    if not file_path.exists():
        return {"error": f"{file} not found"}

    return FileResponse(str(file_path), media_type="text/html")


def _execute_tests(run_id: str, cmd: list, category: str = None):
    """Execute pytest and store results with evidence generation."""
    start_time = datetime.now()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(Path("/app") if Path("/app").exists() else Path(".")),
        )
        duration = (datetime.now() - start_time).total_seconds()

        # Parse pytest output
        output = result.stdout + result.stderr
        tests = parse_pytest_output(output)

        # Parse summary line for accurate counts (works with -q mode)
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
            "output": output[-5000:] if len(output) > 5000 else output,  # Truncate long output
            "command": " ".join(cmd),
            "category": category,
        }

        # Generate evidence file (per TEST-FIX-01-v1, UI-AUDIT-010)
        evidence_path = generate_evidence_file(run_id, test_result, category)
        if evidence_path:
            test_result["evidence_file"] = evidence_path

        _test_results[run_id] = test_result

    except subprocess.TimeoutExpired:
        _test_results[run_id] = {
            "status": "timeout",
            "timestamp": start_time.isoformat(),
            "error": "Test run exceeded 5 minute timeout",
            "category": category,
        }
    except Exception as e:
        _test_results[run_id] = {
            "status": "error",
            "timestamp": start_time.isoformat(),
            "error": str(e),
            "category": category,
        }
