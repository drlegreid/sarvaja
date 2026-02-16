"""
Heuristic Data Integrity Runner.

Per D.4: Execute heuristic checks and produce structured results.
Loads check definitions from heuristic_checks.py and runs them
against the REST API.

Per A.2: Records results to a governance session via session bridge.

Created: 2026-02-01
"""
import logging
import os
import time
from datetime import datetime

from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS

logger = logging.getLogger(__name__)


def run_heuristic_checks(
    api_base_url: str = None,
    domain: str = None,
    record_session: bool = True,
) -> dict:
    """
    Run all heuristic data integrity checks.

    Args:
        api_base_url: Base URL for REST API
        domain: Optional domain filter (TASK, SESSION, RULE, AGENT)
        record_session: Whether to record results to governance session

    Returns:
        Dict with 'checks' list and 'summary' stats.
    """
    if not api_base_url:
        api_base_url = os.getenv("GOVERNANCE_API_URL", "http://localhost:8082")

    # Start governance session for recording (A.2 bridge)
    collector = None
    if record_session:
        try:
            from governance.routes.chat.session_bridge import (
                start_chat_session,
                record_chat_tool_call,
                end_chat_session,
            )
            domain_label = domain.upper() if domain else "ALL"
            collector = start_chat_session(
                "heuristic-runner",
                f"Heuristic integrity check ({domain_label})",
                session_type="test",
            )
        except Exception as e:
            logger.debug(f"Session bridge unavailable: {e}")

    checks_to_run = HEURISTIC_CHECKS
    if domain:
        checks_to_run = [c for c in checks_to_run if c["domain"] == domain.upper()]

    results = []
    passed = 0
    failed = 0
    errors = 0
    skipped = 0

    for check_def in checks_to_run:
        start = time.time()
        try:
            result = check_def["check_fn"](api_base_url)
            duration_ms = int((time.time() - start) * 1000)
            result["id"] = check_def["id"]
            result["domain"] = check_def["domain"]
            result["name"] = check_def["name"]
            result["duration_ms"] = duration_ms

            if result["status"] == "PASS":
                passed += 1
            elif result["status"] == "FAIL":
                failed += 1
            elif result["status"] == "SKIP":
                skipped += 1
            else:
                errors += 1

            results.append(result)

            # Record to session
            if collector:
                try:
                    record_chat_tool_call(
                        collector,
                        tool_name=f"heuristic/{check_def['id']}",
                        arguments={"domain": check_def["domain"]},
                        result=f"{result['status']}: {result.get('message', '')}",
                        duration_ms=duration_ms,
                        success=result["status"] in ("PASS", "SKIP"),
                    )
                except Exception as e:
                    # BUG-HEURISTIC-001: Log instead of silently swallowing
                    logger.debug(f"Failed to record heuristic tool call: {e}")

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            results.append({
                "id": check_def["id"],
                "domain": check_def["domain"],
                "name": check_def["name"],
                "status": "ERROR",
                "message": str(e),
                "violations": [],
                "duration_ms": duration_ms,
            })
            errors += 1

    # End session with summary
    if collector:
        try:
            summary_text = (
                f"Heuristic checks: {passed} pass, {failed} fail, "
                f"{skipped} skip, {errors} error"
            )
            end_chat_session(collector, summary=summary_text)
        except Exception as e:
            # BUG-HEURISTIC-001: Log instead of silently swallowing
            logger.debug(f"Failed to end heuristic session: {e}")

    return {
        "timestamp": datetime.now().isoformat(),
        "checks": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
        },
    }
