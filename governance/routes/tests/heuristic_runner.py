"""
Heuristic Data Integrity Runner.

Per D.4: Execute heuristic checks and produce structured results.
Loads check definitions from heuristic_checks.py and runs them
against the REST API.

Created: 2026-02-01
"""
import logging
import os
from datetime import datetime

from governance.routes.tests.heuristic_checks import HEURISTIC_CHECKS

logger = logging.getLogger(__name__)


def run_heuristic_checks(
    api_base_url: str = None,
    domain: str = None,
) -> dict:
    """
    Run all heuristic data integrity checks.

    Args:
        api_base_url: Base URL for REST API
        domain: Optional domain filter (TASK, SESSION, RULE, AGENT)

    Returns:
        Dict with 'checks' list and 'summary' stats.
    """
    if not api_base_url:
        api_base_url = os.getenv("GOVERNANCE_API_URL", "http://localhost:8082")

    checks_to_run = HEURISTIC_CHECKS
    if domain:
        checks_to_run = [c for c in checks_to_run if c["domain"] == domain.upper()]

    results = []
    passed = 0
    failed = 0
    errors = 0
    skipped = 0

    for check_def in checks_to_run:
        try:
            result = check_def["check_fn"](api_base_url)
            result["id"] = check_def["id"]
            result["domain"] = check_def["domain"]
            result["name"] = check_def["name"]

            if result["status"] == "PASS":
                passed += 1
            elif result["status"] == "FAIL":
                failed += 1
            elif result["status"] == "SKIP":
                skipped += 1
            else:
                errors += 1

            results.append(result)

        except Exception as e:
            results.append({
                "id": check_def["id"],
                "domain": check_def["domain"],
                "name": check_def["name"],
                "status": "ERROR",
                "message": str(e),
                "violations": [],
            })
            errors += 1

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
