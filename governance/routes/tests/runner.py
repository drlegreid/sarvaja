"""
Test Runner API - Self-Assessment Endpoints
Per WORKFLOW-SHELL-01-v1: Run tests in container for health evidence
Per TEST-FIX-01-v1: Tests produce traceable evidence files
Per DOC-SIZE-01-v1: Execution logic in runner_exec.py, storage in runner_store.py

Created: 2026-01-17
Updated: 2026-02-01 - Split per DOC-SIZE-01-v1 (528→280 lines)
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from governance.routes.tests.runner_store import (
    _resolve_test_root,
    _test_results,
)
from governance.routes.tests.runner_exec import (
    execute_tests,
    execute_regression,
    parse_robot_xml,
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


@router.get("/categories")
async def list_test_categories():
    """List available test categories."""
    return {
        "categories": [
            {"id": "unit", "name": "Unit Tests", "pattern": "tests/unit/", "description": "Fast unit tests"},
            {"id": "governance", "name": "Governance", "pattern": "tests/test_governance.py tests/test_rules_governance.py", "description": "TypeDB governance tests"},
            {"id": "ui", "name": "UI Tests", "pattern": "tests/unit/ui/", "description": "Dashboard UI tests"},
            {"id": "kanren", "name": "Kanren", "pattern": "tests/test_kanren_constraints.py", "description": "Constraint engine tests"},
            {"id": "api", "name": "API Tests", "pattern": "tests/test_data_integrity.py tests/test_chat.py", "description": "REST API tests"},
            {"id": "e2e", "name": "E2E Tests", "pattern": "tests/e2e/", "description": "End-to-end pytest tests"},
            {"id": "robot", "name": "Robot Framework", "pattern": "tests/robot/e2e/", "description": "Robot Framework E2E suites"},
            {"id": "rules", "name": "Rules Tests", "pattern": "tests/rules/", "description": "Rule validation tests"},
            {"id": "regression", "name": "Full Regression", "pattern": "all", "description": "Static + Heuristic + Dynamic Playwright (default)"},
        ]
    }


@router.get("/preflight")
async def preflight_check():
    """
    Verify test files are accessible before running.

    Returns discovered test files per category, resolved root path,
    and total file count. Use this to diagnose test runner issues.
    """
    test_root = _resolve_test_root()
    root_path = Path(test_root)
    tests_dir = root_path / "tests"

    categories = []
    total_files = 0

    # Unit tests
    unit_dir = tests_dir / "unit"
    unit_files = sorted(unit_dir.glob("test_*.py")) if unit_dir.is_dir() else []
    if (unit_dir / "ui").is_dir():
        unit_files.extend(sorted((unit_dir / "ui").glob("test_*.py")))
    categories.append({
        "id": "unit", "name": "Unit Tests",
        "file_count": len(unit_files),
        "files": [str(f.relative_to(root_path)) for f in unit_files[:20]],
    })
    total_files += len(unit_files)

    # Robot Framework tests
    robot_dirs = [tests_dir / "robot" / "e2e", tests_dir / "robot"]
    robot_files = []
    for rd in robot_dirs:
        if rd.is_dir():
            robot_files.extend(sorted(rd.glob("*.robot")))
    categories.append({
        "id": "robot", "name": "Robot Framework",
        "file_count": len(robot_files),
        "files": [str(f.relative_to(root_path)) for f in robot_files[:20]],
    })
    total_files += len(robot_files)

    # E2E pytest tests
    e2e_dir = tests_dir / "e2e"
    e2e_files = sorted(e2e_dir.glob("test_*.py")) if e2e_dir.is_dir() else []
    categories.append({
        "id": "e2e", "name": "E2E Tests",
        "file_count": len(e2e_files),
        "files": [str(f.relative_to(root_path)) for f in e2e_files[:20]],
    })
    total_files += len(e2e_files)

    # Root-level test files
    root_tests = sorted(tests_dir.glob("test_*.py"))
    categories.append({
        "id": "root", "name": "Root Tests",
        "file_count": len(root_tests),
        "files": [str(f.relative_to(root_path)) for f in root_tests[:20]],
    })
    total_files += len(root_tests)

    # Rules tests
    rules_dir = tests_dir / "rules"
    rules_files = sorted(rules_dir.glob("test_*.py")) if rules_dir.is_dir() else []
    categories.append({
        "id": "rules", "name": "Rules Tests",
        "file_count": len(rules_files),
        "files": [str(f.relative_to(root_path)) for f in rules_files[:20]],
    })
    total_files += len(rules_files)

    return {
        "test_root": test_root,
        "tests_dir_exists": tests_dir.is_dir(),
        "total_files": total_files,
        "categories": categories,
    }


@router.post("/run")
async def run_tests(
    background_tasks: BackgroundTasks,
    category: Optional[str] = Query(None, description="Test category to run"),
    pattern: Optional[str] = Query(None, description="Custom test pattern"),
    markers: Optional[str] = Query(None, description="Pytest markers (e.g., 'not slow')"),
):
    """Run tests and return results."""
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    cmd = ["python3", "-m", "pytest", "--tb=short", "-q"]

    if pattern:
        cmd.append(pattern)
    elif category:
        patterns = {
            "unit": "tests/unit/",
            "governance": "tests/test_governance.py tests/test_rules_governance.py",
            "ui": "tests/unit/ui/",
            "kanren": "tests/test_kanren_constraints.py",
            "api": "tests/test_data_integrity.py tests/test_chat.py",
            "e2e": "tests/e2e/",
            "robot": "tests/robot/e2e/",
            "rules": "tests/rules/",
        }
        cmd.extend(patterns.get(category, "tests/").split())
    else:
        cmd.append("tests/unit/")

    if markers:
        cmd.extend(["-m", markers])
    if not markers and category not in ["e2e"]:
        cmd.extend(["-k", "not Integration and not slow"])

    _test_results[run_id] = {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "command": " ".join(cmd),
    }

    background_tasks.add_task(execute_tests, run_id, cmd, category)

    return {"run_id": run_id, "status": "started", "command": " ".join(cmd), "category": category}


@router.get("/results/{run_id}")
async def get_test_results(run_id: str):
    """Get results for a specific test run."""
    if run_id not in _test_results:
        return {"error": "Run not found", "run_id": run_id}
    return {"run_id": run_id, **_test_results[run_id]}


@router.get("/results")
async def list_test_results(limit: int = Query(10, le=50)):
    """List recent test run results."""
    sorted_runs = sorted(_test_results.items(), key=lambda x: x[0], reverse=True)
    return {"runs": [{"run_id": k, **v} for k, v in sorted_runs[:limit]]}


@router.post("/heuristic/run")
async def run_heuristic_tests(
    domain: Optional[str] = Query(None, description="Domain filter: TASK, SESSION, RULE, AGENT"),
):
    """Run heuristic data integrity checks. Per D.4."""
    import os
    from governance.routes.tests.heuristic_runner import run_heuristic_checks
    api_url = os.getenv("GOVERNANCE_API_URL", "http://localhost:8082")
    results = run_heuristic_checks(api_base_url=api_url, domain=domain)
    return results


@router.post("/regression/run")
async def run_regression_tests(
    background_tasks: BackgroundTasks,
    skip_dynamic: bool = Query(False, description="Skip Playwright dynamic checks"),
):
    """
    Run full regression cycle: static + heuristic + dynamic Playwright.

    Returns run_id for polling via /tests/results/{run_id}.
    """
    run_id = f"REG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    _test_results[run_id] = {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "category": "regression",
        "command": f"regression (skip_dynamic={skip_dynamic})",
    }

    background_tasks.add_task(execute_regression, run_id, skip_dynamic)

    return {
        "run_id": run_id,
        "status": "started",
        "category": "regression",
        "phases": ["static", "heuristic"] + ([] if skip_dynamic else ["dynamic"]),
    }


@router.get("/robot/summary")
async def get_robot_summary():
    """Parse Robot Framework output.xml for summary stats."""
    return parse_robot_xml(_resolve_test_root())


@router.get("/robot/report")
async def serve_robot_report(file: str = Query("report.html")):
    """Serve Robot Framework report HTML files."""
    allowed_files = {"report.html", "log.html"}
    if file not in allowed_files:
        return {"error": f"File not allowed. Choose from: {allowed_files}"}

    file_path = Path(_resolve_test_root()) / file
    if not file_path.exists():
        return {"error": f"{file} not found"}

    return FileResponse(str(file_path), media_type="text/html")
