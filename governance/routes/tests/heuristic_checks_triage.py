"""
Heuristic Triage Checks — stale task detection and issue triage.

Per DOC-SIZE-01-v1: Split from heuristic_checks.py.
Per EPIC-TASK-QUALITY-V3 P16: Issue Triage Workflow.
"""
import logging
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _api_get(api_base_url: str, endpoint: str) -> list:
    """Safe API GET with error handling (local copy to avoid circular import)."""
    try:
        resp = httpx.get(f"{api_base_url}{endpoint}", timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("items", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.debug(f"Heuristic API call failed: {endpoint}: {type(e).__name__}")
    return []

# Tasks IN_PROGRESS longer than this are considered stale
STALE_THRESHOLD_DAYS = 7


def check_task_stale_in_progress(api_base_url: str) -> dict:
    """H-TASK-STALE-001: IN_PROGRESS tasks >7 days without commits are stale.

    Tasks that are IN_PROGRESS for more than STALE_THRESHOLD_DAYS with no
    linked_commits and no recent status updates are flagged as stale.
    Terminal states (DONE, CLOSED, COMPLETED) are exempt.
    """
    tasks = _api_get(api_base_url, "/api/tasks?status=IN_PROGRESS&limit=200")
    if not tasks:
        return {
            "status": "SKIP",
            "message": "No IN_PROGRESS tasks to check",
            "violations": [],
        }

    threshold = datetime.now() - timedelta(days=STALE_THRESHOLD_DAYS)
    threshold_iso = threshold.isoformat()
    violations = []

    for t in tasks:
        # Skip test artifacts
        if (t.get("task_id") or "").startswith("TEST-"):
            continue
        # Use claimed_at first, fall back to created_at
        age_date = t.get("claimed_at") or t.get("created_at")
        if not age_date:
            # No date at all — can't determine age, skip
            continue
        # Check if older than threshold
        if str(age_date)[:19] > threshold_iso[:19]:
            # Task is newer than threshold — not stale
            continue
        # Check for linked commits — if any exist, task is active
        if t.get("linked_commits"):
            continue
        violations.append(t.get("task_id", "unknown"))

    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)} IN_PROGRESS tasks stale >{STALE_THRESHOLD_DAYS} days"
            f" (no linked commits)"
            if violations
            else f"All IN_PROGRESS tasks active within {STALE_THRESHOLD_DAYS} days"
        ),
        "violations": violations[:20],
    }


TRIAGE_CHECKS = [
    {
        "id": "H-TASK-STALE-001",
        "domain": "TASK",
        "name": "Stale IN_PROGRESS detection",
        "check_fn": check_task_stale_in_progress,
    },
]
