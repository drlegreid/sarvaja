"""
Test Runner API - Self-Assessment Endpoints
Per WORKFLOW-SHELL-01-v1: Run tests in container for health evidence
Created: 2026-01-17
"""
import subprocess
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, BackgroundTasks
from pydantic import BaseModel


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
    cmd = ["python", "-m", "pytest", "--tb=short", "-q"]

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
    background_tasks.add_task(_execute_tests, run_id, cmd)

    return {"run_id": run_id, "status": "started", "command": " ".join(cmd)}


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


def _execute_tests(run_id: str, cmd: list):
    """Execute pytest and store results."""
    start_time = datetime.now()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd="/app",
        )
        duration = (datetime.now() - start_time).total_seconds()

        # Parse pytest output
        output = result.stdout + result.stderr
        tests = _parse_pytest_output(output)

        # Parse summary line for accurate counts (works with -q mode)
        summary = _parse_pytest_summary(output)
        passed = summary["passed"]
        failed = summary["failed"]
        skipped = summary["skipped"]
        total = passed + failed + skipped

        _test_results[run_id] = {
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
        }
    except subprocess.TimeoutExpired:
        _test_results[run_id] = {
            "status": "timeout",
            "timestamp": start_time.isoformat(),
            "error": "Test run exceeded 5 minute timeout",
        }
    except Exception as e:
        _test_results[run_id] = {
            "status": "error",
            "timestamp": start_time.isoformat(),
            "error": str(e),
        }


def _parse_pytest_summary(output: str) -> dict:
    """
    Parse pytest summary line to extract counts.

    Handles formats like:
    - "3 failed, 96 passed, 5 deselected in 2.49s"
    - "96 passed in 2.49s"
    - "3 failed, 96 passed, 5 skipped in 2.49s"
    """
    import re
    counts = {"passed": 0, "failed": 0, "skipped": 0, "deselected": 0}

    # Find summary line (usually last few lines)
    for line in reversed(output.split("\n")):
        # Match patterns like "3 failed" or "96 passed"
        if " passed" in line or " failed" in line:
            for key in counts.keys():
                match = re.search(rf"(\d+)\s+{key}", line)
                if match:
                    counts[key] = int(match.group(1))
            break
    return counts


def _parse_pytest_output(output: str) -> list:
    """Parse pytest output to extract test results."""
    tests = []

    # Try verbose format first (for -v mode)
    for line in output.split("\n"):
        line = line.strip()
        if " PASSED" in line or " FAILED" in line or " SKIPPED" in line:
            parts = line.split()
            if len(parts) >= 2:
                nodeid = parts[0]
                if " PASSED" in line:
                    outcome = "passed"
                elif " FAILED" in line:
                    outcome = "failed"
                else:
                    outcome = "skipped"
                tests.append({"nodeid": nodeid, "outcome": outcome, "duration": 0.0})

    # If no tests found (quiet mode), parse FAILURES section for failed test names
    if not tests:
        import re
        # Find failed test names from FAILURES section
        failure_pattern = re.compile(r"_+\s+([\w.:\[\]]+)\s+_+")
        for match in failure_pattern.finditer(output):
            tests.append({"nodeid": match.group(1), "outcome": "failed", "duration": 0.0})

    return tests
