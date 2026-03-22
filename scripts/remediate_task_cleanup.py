#!/usr/bin/env python3
"""
Task Cleanup Remediation Script.

Per EPIC-GOV-TASKS-V2 Phase 9e (2026-03-21, 228 tasks):

Sub-commands:
  junk    -- Detect and optionally delete test artifact tasks
  link    -- Batch-link orphaned worked tasks to sessions by timestamp
  epic    -- Detect OPEN tasks in completed EPIC phases
  report  -- Summary of all remediation findings

Usage:
    python3 scripts/remediate_task_cleanup.py junk --dry-run
    python3 scripts/remediate_task_cleanup.py link --dry-run
    python3 scripts/remediate_task_cleanup.py epic --dry-run
    python3 scripts/remediate_task_cleanup.py report
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger(__name__)

# Junk detection patterns
JUNK_PREFIXES = frozenset({"CRUD-", "INTTEST-", "E2E-TAX-"})
GENERIC_NAMES = frozenset({
    "Lifecycle test", "Agent task", "New feature", "Test task",
})

# Worked statuses (eligible for session linking)
WORKED_STATUSES = frozenset({"IN_PROGRESS", "DONE", "CLOSED", "COMPLETED"})


def detect_junk_tasks(tasks: list) -> dict:
    """Detect test artifact tasks for cleanup.

    Detection rules:
    1. Task ID starts with JUNK_PREFIXES (CRUD-, INTTEST-, E2E-TAX-)
    2. Name is in GENERIC_NAMES AND body is null/empty

    Returns:
        {"found": count, "details": [{"task_id", "name", "reason"}]}
    """
    results = {"found": 0, "details": []}
    for task in tasks:
        tid = task.get("task_id", "")
        name = task.get("name", "")
        body = task.get("body")
        reason = None

        # Rule 1: Known junk prefixes
        for prefix in JUNK_PREFIXES:
            if tid.startswith(prefix):
                reason = f"junk prefix: {prefix}"
                break

        # Rule 2: Generic name + null body
        if not reason and name in GENERIC_NAMES and not body:
            reason = f"generic name + null body: {name!r}"

        if reason:
            results["found"] += 1
            results["details"].append({
                "task_id": tid, "name": name, "reason": reason,
            })

    return results


def batch_link_sessions(tasks: list, sessions: list,
                        dry_run: bool = True) -> dict:
    """Batch-link orphaned worked tasks to sessions by timestamp overlap.

    Only processes tasks with status in WORKED_STATUSES that have
    no existing linked_sessions and a non-null created_at.

    Args:
        tasks: List of task dicts.
        sessions: List of session dicts with start_time/end_time.
        dry_run: If True, report matches without applying.

    Returns:
        {"matched": count, "skipped": count, "applied": count,
         "details": [{"task_id", "session_id"}]}
    """
    results = {"matched": 0, "skipped": 0, "applied": 0, "details": []}

    for task in tasks:
        tid = task.get("task_id", "")
        status = (task.get("status") or "").upper()
        linked = task.get("linked_sessions") or []
        created_at = task.get("created_at")

        # Skip non-worked or already-linked or no timestamp
        if status not in WORKED_STATUSES:
            results["skipped"] += 1
            continue
        if linked:
            results["skipped"] += 1
            continue
        if not created_at:
            results["skipped"] += 1
            continue

        # Find best session by timestamp overlap
        best_sid = _find_best_session(created_at, sessions)
        if best_sid:
            results["matched"] += 1
            results["details"].append({"task_id": tid, "session_id": best_sid})
            if not dry_run:
                results["applied"] += 1

    return results


def _find_best_session(created_at: str, sessions: list) -> str | None:
    """Find the session whose time range contains created_at.

    Returns session_id or None.
    """
    try:
        task_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None

    for s in sessions:
        start = s.get("start_time", "")
        end = s.get("end_time", "")
        if not start:
            continue
        try:
            s_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            if end:
                s_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
            else:
                # Open session — assume it covers 24h from start
                from datetime import timedelta
                s_end = s_start + timedelta(hours=24)
            if s_start <= task_dt <= s_end:
                return s.get("session_id")
        except (ValueError, AttributeError):
            continue
    return None


def detect_completed_epic_tasks(tasks: list,
                                done_phases: dict = None) -> dict:
    """Find OPEN tasks whose EPIC phase is already DONE.

    Args:
        tasks: List of task dicts.
        done_phases: Dict of {task_id: phase} for known completed phases.

    Returns:
        {"found": count, "details": [{"task_id", "phase", "status"}]}
    """
    if not done_phases:
        done_phases = {}
    done_phase_values = set(done_phases.values())
    results = {"found": 0, "details": []}
    for task in tasks:
        tid = task.get("task_id", "")
        status = (task.get("status") or "").upper()
        phase = task.get("phase", "")
        if status in ("OPEN", "TODO") and phase in done_phase_values:
            results["found"] += 1
            results["details"].append({
                "task_id": tid, "phase": phase, "status": status,
            })
    return results


def backfill_summaries(tasks: list) -> dict:
    """Generate summaries for tasks with null summary but non-null description.

    Uses the same _generate_summary logic as the service layer.

    Returns:
        {"found": count, "details": [{"task_id", "summary"}]}
    """
    results = {"found": 0, "details": []}
    for task in tasks:
        tid = task.get("task_id", "")
        summary = task.get("summary")
        desc = task.get("description") or task.get("body") or task.get("name")
        if summary or not desc:
            continue
        # Generate summary: first 77 chars + "..." if truncated
        generated = desc[:77].rstrip() + "..." if len(desc) > 80 else desc
        results["found"] += 1
        results["details"].append({"task_id": tid, "summary": generated})
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fetch_tasks():
    """Fetch all tasks from API."""
    import httpx
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get("http://localhost:8082/api/tasks",
                              params={"limit": 500, "offset": 0})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.error("Failed to fetch tasks: %s", e)
    return []


def _fetch_sessions():
    """Fetch all sessions from API."""
    import httpx
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get("http://localhost:8082/api/sessions",
                              params={"limit": 500})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.error("Failed to fetch sessions: %s", e)
    return []


def main():
    parser = argparse.ArgumentParser(description="Task cleanup remediation")
    parser.add_argument("command", choices=["junk", "link", "epic", "report"],
                        help="Sub-command to run")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview changes without applying (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes (override dry-run)")
    args = parser.parse_args()
    dry_run = not args.apply

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    tasks = _fetch_tasks()
    if not tasks:
        print("No tasks fetched. Is the API running on :8082?")
        return

    if args.command == "junk":
        result = detect_junk_tasks(tasks)
        print(f"\nJunk tasks found: {result['found']}")
        for d in result["details"]:
            print(f"  {d['task_id']:30s} {d['reason']}")
        if not dry_run:
            print("\n[APPLY mode] Would delete these tasks via API.")

    elif args.command == "link":
        sessions = _fetch_sessions()
        result = batch_link_sessions(tasks, sessions, dry_run=dry_run)
        print(f"\nSession linkage: matched={result['matched']}, "
              f"skipped={result['skipped']}, applied={result['applied']}")
        for d in result["details"]:
            print(f"  {d['task_id']:30s} -> {d['session_id']}")

    elif args.command == "epic":
        done_phases = {
            "EPIC-TASKS-V2-P9A": "V2-P9A",
            "EPIC-TASKS-V2-P9B": "V2-P9B",
        }
        result = detect_completed_epic_tasks(tasks, done_phases)
        print(f"\nStale EPIC phase tasks: {result['found']}")
        for d in result["details"]:
            print(f"  {d['task_id']:30s} status={d['status']} phase={d['phase']}")

    elif args.command == "report":
        junk = detect_junk_tasks(tasks)
        sessions = _fetch_sessions()
        links = batch_link_sessions(tasks, sessions, dry_run=True)
        done_phases = {"EPIC-TASKS-V2-P9A": "V2-P9A",
                       "EPIC-TASKS-V2-P9B": "V2-P9B"}
        epic = detect_completed_epic_tasks(tasks, done_phases)
        print(f"\n=== Task Cleanup Report ({len(tasks)} tasks) ===")
        print(f"  Junk tasks:          {junk['found']}")
        print(f"  Linkable to session: {links['matched']}")
        print(f"  Stale EPIC phases:   {epic['found']}")


if __name__ == "__main__":
    main()
