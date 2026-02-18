"""
Test Runner API - Self-Assessment Endpoints
Per WORKFLOW-SHELL-01-v1: Run tests in container for health evidence
Per TEST-FIX-01-v1: Tests produce traceable evidence files
Per DOC-SIZE-01-v1: Execution logic in runner_exec.py, storage in runner_store.py,
    discovery/preflight in runner_preflight.py

Created: 2026-01-17
Updated: 2026-02-01 - Split per DOC-SIZE-01-v1 (528→280 lines)
Updated: 2026-02-11 - Extract preflight per DOC-SIZE-01-v1 (338→210 lines)
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse

from governance.routes.tests.runner_store import (
    _resolve_test_root,
    _test_results,
)
from governance.routes.tests.runner_exec import (
    execute_tests,
    execute_regression,
    execute_heuristic,
    parse_robot_xml,
)

# Re-export for backward compatibility
from governance.routes.tests.runner_preflight import (  # noqa: F401
    TestResult,
    TestRunSummary,
    list_test_categories,
    preflight_check,
    register_preflight_routes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tests", tags=["tests"])

# Register preflight + discovery routes
register_preflight_routes(router)


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

    # BUG-243-RUN-001: Validate pattern to prevent path traversal
    if pattern:
        import re as _re
        if not _re.match(r'^tests/[\w/\-\.]+$', pattern):
            raise HTTPException(status_code=400, detail="Invalid test pattern: must start with tests/")
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

    # BUG-243-RUN-002: Validate markers to prevent injection
    if markers:
        import re as _re
        if not _re.match(r'^[\w\s\(\)]+$', markers):
            raise HTTPException(status_code=400, detail="Invalid marker expression")
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
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {"run_id": run_id, **_test_results[run_id]}


@router.get("/results")
async def list_test_results(limit: int = Query(10, le=50)):
    """List recent test run results."""
    sorted_runs = sorted(_test_results.items(), key=lambda x: x[0], reverse=True)
    return {"runs": [{"run_id": k, **v} for k, v in sorted_runs[:limit]]}


@router.post("/heuristic/run")
async def run_heuristic_tests(
    background_tasks: BackgroundTasks,
    domain: Optional[str] = Query(None, description="Domain filter: TASK, SESSION, RULE, AGENT"),
):
    """Run heuristic data integrity checks in background. Per D.4.

    Returns run_id for polling via /tests/results/{run_id}.
    Runs in background thread to avoid deadlock from self-referential API calls.
    """
    run_id = f"HEUR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    _test_results[run_id] = {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "category": "heuristic",
        "command": f"heuristic (domain={domain})",
    }

    background_tasks.add_task(execute_heuristic, run_id, domain)

    return {"run_id": run_id, "status": "started", "category": "heuristic"}


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


@router.post("/cvp/sweep")
async def run_cvp_sweep(
    background_tasks: BackgroundTasks,
    tier: int = Query(3, ge=1, le=3, description="CVP tier: 1=inline, 2=post-session, 3=full sweep"),
):
    """
    Run CVP (Continuous Validation Pipeline) sweep. Per TEST-CVP-01-v1.

    Tier 3 runs all heuristic checks + cross-entity validation.
    Returns run_id for polling via /tests/results/{run_id}.
    """
    run_id = f"CVP-T{tier}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    _test_results[run_id] = {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "category": f"cvp-tier-{tier}",
        "command": f"CVP sweep tier={tier}",
    }

    # Tier 3 runs full heuristic sweep across all domains
    background_tasks.add_task(execute_heuristic, run_id, None)

    return {
        "run_id": run_id,
        "status": "started",
        "category": f"cvp-tier-{tier}",
        "tier": tier,
    }


@router.get("/cvp/status")
async def get_cvp_status():
    """
    Get CVP pipeline status summary. Per TEST-CVP-01-v1.

    Returns latest results from each tier and overall health.
    """
    cvp_runs = {
        k: v for k, v in _test_results.items()
        if k.startswith("CVP-") or k.startswith("HEUR-")
    }
    sorted_runs = sorted(cvp_runs.items(), key=lambda x: x[0], reverse=True)

    last_run = sorted_runs[0] if sorted_runs else None
    last_status = last_run[1].get("status", "unknown") if last_run else "never_run"

    return {
        "pipeline_health": "healthy" if last_status == "completed" else "unknown",
        "last_run_id": last_run[0] if last_run else None,
        "last_run_status": last_status,
        "total_cvp_runs": len(cvp_runs),
        "recent_runs": [
            {"run_id": k, "status": v.get("status"), "timestamp": v.get("timestamp")}
            for k, v in sorted_runs[:5]
        ],
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
