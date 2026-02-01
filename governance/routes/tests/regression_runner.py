"""
Full Regression Runner.

Orchestrates a three-phase regression cycle:
  Phase 1 (STATIC):  pytest unit tests
  Phase 2 (HEURISTIC): Data integrity checks across all domains
  Phase 3 (DYNAMIC): Playwright MCP browser checks on live UI

Returns unified results with per-phase breakdown and overall verdict.

Per WORKFLOW-SHELL-01-v1: Self-assessment via containerized tests.
Per TEST-FIX-01-v1: Produce traceable evidence.

Created: 2026-02-01
"""
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from governance.routes.tests.parser import parse_pytest_summary

logger = logging.getLogger(__name__)


def _resolve_test_root() -> str:
    """Resolve project root containing tests/."""
    if Path("/app/tests").is_dir():
        return "/app"
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "tests").is_dir() and (parent / "tests" / "unit").is_dir():
            return str(parent)
    return str(Path.cwd())


def run_regression(
    api_base_url: str = None,
    dashboard_url: str = None,
    skip_dynamic: bool = False,
    record_session: bool = True,
) -> dict:
    """
    Run full regression cycle.

    Args:
        api_base_url: REST API base URL (default: env or localhost:8082)
        dashboard_url: Dashboard URL for Playwright checks (default: localhost:8081)
        skip_dynamic: Skip Phase 3 Playwright checks
        record_session: Record to governance session

    Returns:
        Dict with phases[], summary, and overall verdict.
    """
    if not api_base_url:
        api_base_url = os.getenv("GOVERNANCE_API_URL", "http://localhost:8082")
    if not dashboard_url:
        dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:8081")

    # Session recording
    collector = None
    if record_session:
        try:
            from governance.routes.chat.session_bridge import (
                start_chat_session,
                record_chat_tool_call,
                end_chat_session,
            )
            collector = start_chat_session(
                "regression-runner",
                "Full regression cycle",
                session_type="test",
            )
        except Exception as e:
            logger.debug(f"Session bridge unavailable: {e}")

    phases = []
    overall_start = time.time()

    # === PHASE 1: Static Tests (pytest unit) ===
    phase1 = _run_static_phase(collector)
    phases.append(phase1)

    # === PHASE 2: Heuristic Data Integrity ===
    phase2 = _run_heuristic_phase(api_base_url, collector)
    phases.append(phase2)

    # === PHASE 3: Dynamic Playwright UI Checks ===
    if not skip_dynamic:
        phase3 = _run_dynamic_phase(dashboard_url, api_base_url, collector)
        phases.append(phase3)

    total_duration = round(time.time() - overall_start, 1)

    # Compute overall verdict
    all_pass = all(p["verdict"] == "PASS" for p in phases)
    any_error = any(p["verdict"] == "ERROR" for p in phases)

    if all_pass:
        verdict = "PASS"
    elif any_error:
        verdict = "ERROR"
    else:
        verdict = "FAIL"

    result = {
        "timestamp": datetime.now().isoformat(),
        "verdict": verdict,
        "duration_seconds": total_duration,
        "phases": phases,
        "summary": {
            "total_phases": len(phases),
            "passed_phases": sum(1 for p in phases if p["verdict"] == "PASS"),
            "failed_phases": sum(1 for p in phases if p["verdict"] == "FAIL"),
            "error_phases": sum(1 for p in phases if p["verdict"] == "ERROR"),
        },
    }

    # End session
    if collector:
        try:
            end_chat_session(
                collector,
                summary=f"Regression {verdict}: {result['summary']}",
            )
        except Exception:
            pass

    return result


def _run_static_phase(collector=None) -> dict:
    """Phase 1: Run pytest unit tests."""
    start = time.time()
    test_root = _resolve_test_root()
    cmd = ["python3", "-m", "pytest", "tests/unit/", "--tb=short", "-q",
           "-k", "not Integration and not slow"]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=300, cwd=test_root,
        )
        duration = round(time.time() - start, 1)
        output = proc.stdout + proc.stderr
        summary = parse_pytest_summary(output)

        verdict = "PASS" if proc.returncode == 0 else "FAIL"
        phase = {
            "name": "Static Tests",
            "phase": 1,
            "verdict": verdict,
            "duration_seconds": duration,
            "passed": summary["passed"],
            "failed": summary["failed"],
            "skipped": summary["skipped"],
            "total": summary["passed"] + summary["failed"] + summary["skipped"],
            "output_tail": output[-2000:] if len(output) > 2000 else output,
        }

        _record_phase(collector, "regression/static", phase)
        return phase

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start, 1)
        phase = {
            "name": "Static Tests",
            "phase": 1,
            "verdict": "ERROR",
            "duration_seconds": duration,
            "error": "Timeout after 300s",
        }
        _record_phase(collector, "regression/static", phase)
        return phase
    except Exception as e:
        duration = round(time.time() - start, 1)
        phase = {
            "name": "Static Tests",
            "phase": 1,
            "verdict": "ERROR",
            "duration_seconds": duration,
            "error": str(e),
        }
        _record_phase(collector, "regression/static", phase)
        return phase


def _run_heuristic_phase(api_base_url: str, collector=None) -> dict:
    """Phase 2: Run heuristic data integrity checks."""
    start = time.time()
    try:
        from governance.routes.tests.heuristic_runner import run_heuristic_checks
        results = run_heuristic_checks(
            api_base_url=api_base_url,
            record_session=False,  # Parent session handles recording
        )
        duration = round(time.time() - start, 1)
        s = results.get("summary", {})
        verdict = "PASS" if s.get("failed", 0) == 0 and s.get("errors", 0) == 0 else "FAIL"

        phase = {
            "name": "Heuristic Integrity",
            "phase": 2,
            "verdict": verdict,
            "duration_seconds": duration,
            "passed": s.get("passed", 0),
            "failed": s.get("failed", 0),
            "skipped": s.get("skipped", 0),
            "errors": s.get("errors", 0),
            "total": s.get("total", 0),
            "checks": results.get("checks", []),
        }
        _record_phase(collector, "regression/heuristic", phase)
        return phase

    except Exception as e:
        duration = round(time.time() - start, 1)
        phase = {
            "name": "Heuristic Integrity",
            "phase": 2,
            "verdict": "ERROR",
            "duration_seconds": duration,
            "error": str(e),
        }
        _record_phase(collector, "regression/heuristic", phase)
        return phase


def _run_dynamic_phase(
    dashboard_url: str,
    api_base_url: str,
    collector=None,
) -> dict:
    """Phase 3: Dynamic Playwright MCP browser checks."""
    start = time.time()
    try:
        from governance.routes.tests.playwright_checks import run_playwright_checks
        results = run_playwright_checks(
            dashboard_url=dashboard_url,
            api_base_url=api_base_url,
        )
        duration = round(time.time() - start, 1)
        s = results.get("summary", {})
        verdict = "PASS" if s.get("failed", 0) == 0 and s.get("errors", 0) == 0 else "FAIL"

        phase = {
            "name": "Dynamic UI (Playwright)",
            "phase": 3,
            "verdict": verdict,
            "duration_seconds": duration,
            "passed": s.get("passed", 0),
            "failed": s.get("failed", 0),
            "skipped": s.get("skipped", 0),
            "errors": s.get("errors", 0),
            "total": s.get("total", 0),
            "checks": results.get("checks", []),
        }
        _record_phase(collector, "regression/dynamic", phase)
        return phase

    except Exception as e:
        duration = round(time.time() - start, 1)
        phase = {
            "name": "Dynamic UI (Playwright)",
            "phase": 3,
            "verdict": "ERROR",
            "duration_seconds": duration,
            "error": str(e),
        }
        _record_phase(collector, "regression/dynamic", phase)
        return phase


def _record_phase(collector, tool_name: str, phase: dict) -> None:
    """Record phase result to governance session."""
    if not collector:
        return
    try:
        from governance.routes.chat.session_bridge import record_chat_tool_call
        record_chat_tool_call(
            collector,
            tool_name=tool_name,
            arguments={"phase": phase.get("phase")},
            result=f"{phase['verdict']}: {phase['name']}",
            duration_ms=int(phase.get("duration_seconds", 0) * 1000),
            success=phase["verdict"] == "PASS",
        )
    except Exception:
        pass
