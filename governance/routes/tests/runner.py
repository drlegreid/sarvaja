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


def _resolve_test_root() -> str:
    """Resolve the project root directory containing tests/.

    Checks /app (container), then walks up from this file to find tests/ dir.
    Returns absolute path string.
    """
    # Container path
    if Path("/app/tests").is_dir():
        return "/app"

    # Walk up from this file to find project root with tests/
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "tests").is_dir() and (parent / "tests" / "unit").is_dir():
            return str(parent)

    # Fallback to cwd
    return str(Path.cwd())


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


# Default persistence directory
_RESULTS_DIR = str(Path(_resolve_test_root()) / "evidence" / "test-results")

# In-memory store for test results (D.2: also persisted to disk)
_test_results: dict = {}


def _persist_result(run_id: str, result: dict, results_dir: str = None) -> None:
    """Persist a test result to JSON file. Per D.2."""
    import json
    target_dir = Path(results_dir or _RESULTS_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / f"{run_id}.json"
    filepath.write_text(json.dumps(result, indent=2, default=str))


def _load_persisted_results(results_dir: str = None) -> dict:
    """Load persisted test results from disk. Per D.2."""
    import json
    target_dir = Path(results_dir or _RESULTS_DIR)
    results = {}
    if target_dir.is_dir():
        for filepath in sorted(target_dir.glob("*.json"), reverse=True)[:50]:
            try:
                data = json.loads(filepath.read_text())
                run_id = filepath.stem
                results[run_id] = data
            except Exception:
                continue
    return results


# Load persisted results on import (D.2: survive restarts)
try:
    _test_results.update(_load_persisted_results())
except Exception:
    pass


@router.get("/categories")
async def list_test_categories():
    """
    List available test categories.

    Returns categories mapped to test file patterns.
    """
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
    # Also include unit/ui/ tests
    if (unit_dir / "ui").is_dir():
        unit_files.extend(sorted((unit_dir / "ui").glob("test_*.py")))
    categories.append({
        "id": "unit",
        "name": "Unit Tests",
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
        "id": "robot",
        "name": "Robot Framework",
        "file_count": len(robot_files),
        "files": [str(f.relative_to(root_path)) for f in robot_files[:20]],
    })
    total_files += len(robot_files)

    # E2E pytest tests
    e2e_dir = tests_dir / "e2e"
    e2e_files = sorted(e2e_dir.glob("test_*.py")) if e2e_dir.is_dir() else []
    categories.append({
        "id": "e2e",
        "name": "E2E Tests",
        "file_count": len(e2e_files),
        "files": [str(f.relative_to(root_path)) for f in e2e_files[:20]],
    })
    total_files += len(e2e_files)

    # Root-level test files
    root_tests = sorted(tests_dir.glob("test_*.py"))
    categories.append({
        "id": "root",
        "name": "Root Tests",
        "file_count": len(root_tests),
        "files": [str(f.relative_to(root_path)) for f in root_tests[:20]],
    })
    total_files += len(root_tests)

    # Rules tests
    rules_dir = tests_dir / "rules"
    rules_files = sorted(rules_dir.glob("test_*.py")) if rules_dir.is_dir() else []
    categories.append({
        "id": "rules",
        "name": "Rules Tests",
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
        cmd.append("tests/unit/")  # Default: fast unit tests

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
    """
    Run heuristic data integrity checks. Per D.4.

    Returns structured results with per-check status and summary.
    """
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

    This is the default regression run. Phases:
      1. Static: pytest unit tests
      2. Heuristic: data integrity checks across all domains
      3. Dynamic: Playwright browser checks (chat, all screens, data integrity)

    Returns run_id for polling via /tests/results/{run_id}.
    """
    run_id = f"REG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    _test_results[run_id] = {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "category": "regression",
        "command": f"regression (skip_dynamic={skip_dynamic})",
    }

    background_tasks.add_task(
        _execute_regression, run_id, skip_dynamic
    )

    return {
        "run_id": run_id,
        "status": "started",
        "category": "regression",
        "phases": ["static", "heuristic"] + ([] if skip_dynamic else ["dynamic"]),
    }


def _execute_regression(run_id: str, skip_dynamic: bool = False):
    """Execute full regression and store results."""
    start_time = datetime.now()
    try:
        from governance.routes.tests.regression_runner import run_regression

        result = run_regression(skip_dynamic=skip_dynamic)
        duration = (datetime.now() - start_time).total_seconds()

        # Map regression result to standard test result shape
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

        # Generate evidence
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


@router.get("/robot/summary")
async def get_robot_summary():
    """Parse Robot Framework output.xml for summary stats."""
    project_root = Path(_resolve_test_root())
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

    project_root = Path(_resolve_test_root())
    file_path = project_root / file

    if not file_path.exists():
        return {"error": f"{file} not found"}

    return FileResponse(str(file_path), media_type="text/html")


def _execute_tests(run_id: str, cmd: list, category: str = None):
    """Execute pytest and store results with evidence generation."""
    start_time = datetime.now()
    test_root = _resolve_test_root()
    logger.info(f"Test run {run_id}: cmd={cmd}, cwd={test_root}, category={category}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=test_root,
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
        # D.2: Persist to disk
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
