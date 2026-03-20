#!/usr/bin/env python3
"""
Remediate orphaned tasks: link to sessions by timestamp overlap.

Per EPIC-GOV-TASKS-V2 Phase 7:
- Finds IN_PROGRESS/DONE tasks with no linked_sessions
- Matches to sessions by overlapping time windows
- Idempotent: skips tasks that already have linked_sessions

Usage:
    python3 scripts/remediate_orphaned_tasks.py --dry-run
    python3 scripts/remediate_orphaned_tasks.py --apply
"""
import sys
import argparse
from datetime import datetime, timezone

sys.path.insert(0, ".")

from governance.stores import get_typedb_client


def _parse_ts(ts_str: str) -> datetime | None:
    """Parse ISO timestamp string to datetime, returns None on failure."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _find_best_session(task, sessions) -> str | None:
    """Find the best matching session for a task by timestamp overlap.

    Strategy:
    1. If task has created_at, find session whose (start_time, end_time) overlaps
    2. Prefer sessions that are ENDED/COMPLETED over ACTIVE
    3. If multiple match, pick the one with closest start_time
    """
    task_created = _parse_ts(
        getattr(task, "created_at", None) or getattr(task, "claimed_at", None)
    )
    if not task_created:
        return None

    candidates = []
    for session in sessions:
        s_start = _parse_ts(getattr(session, "start_time", None))
        s_end = _parse_ts(getattr(session, "end_time", None))
        if not s_start:
            continue
        # Check overlap: task_created falls within session window
        if s_end:
            if s_start <= task_created <= s_end:
                candidates.append((session, abs((task_created - s_start).total_seconds())))
        else:
            # No end_time means session might still be active or unclosed
            if s_start <= task_created:
                candidates.append((session, abs((task_created - s_start).total_seconds())))

    if not candidates:
        return None
    # Sort by time distance (closest first)
    candidates.sort(key=lambda x: x[1])
    return getattr(candidates[0][0], "session_id", None)


def remediate(dry_run: bool = True) -> dict:
    """Find and fix orphaned tasks (no linked_sessions).

    Args:
        dry_run: If True, report what would change without modifying data.

    Returns:
        Summary dict with counts and details.
    """
    client = get_typedb_client()
    if not client or not client.connect():
        print("ERROR: Failed to connect to TypeDB")
        return {"error": "TypeDB connection failed"}

    try:
        tasks = client.get_all_tasks()
        print(f"Found {len(tasks)} tasks in TypeDB")
    except Exception as e:
        print(f"ERROR: Failed to get tasks: {type(e).__name__}")
        return {"error": str(e)}

    # Filter to worked tasks without sessions
    worked_statuses = {"IN_PROGRESS", "DONE", "COMPLETED"}
    orphans = [
        t for t in tasks
        if getattr(t, "status", "") in worked_statuses
        and not getattr(t, "linked_sessions", None)
        and not getattr(t, "id", "").startswith("TEST-")
    ]
    print(f"Found {len(orphans)} orphaned tasks (worked, no linked_sessions)")

    if not orphans:
        print("Nothing to remediate.")
        return {"orphans": 0, "linked": 0, "failed": 0, "skipped": 0}

    # Get all sessions for matching
    try:
        sessions = client.get_all_sessions()
        print(f"Found {len(sessions)} sessions for matching")
    except Exception as e:
        print(f"ERROR: Failed to get sessions: {type(e).__name__}")
        return {"error": str(e)}

    linked = 0
    failed = 0
    skipped = 0
    details = []

    for task in orphans:
        task_id = getattr(task, "id", "unknown")
        best_session = _find_best_session(task, sessions)

        if not best_session:
            skipped += 1
            details.append({"task_id": task_id, "action": "skipped", "reason": "no matching session"})
            print(f"  SKIP {task_id}: no matching session by timestamp")
            continue

        if dry_run:
            linked += 1
            details.append({"task_id": task_id, "action": "planned", "session": best_session})
            print(f"  PLAN {task_id} → {best_session}")
        else:
            try:
                result = client.link_task_to_session(task_id, best_session)
                if result:
                    linked += 1
                    details.append({"task_id": task_id, "action": "linked", "session": best_session})
                    print(f"  LINKED {task_id} → {best_session}")
                else:
                    failed += 1
                    details.append({"task_id": task_id, "action": "failed", "session": best_session})
                    print(f"  FAIL {task_id} → {best_session}")
            except Exception as e:
                failed += 1
                details.append({"task_id": task_id, "action": "error", "error": type(e).__name__})
                print(f"  ERROR {task_id}: {type(e).__name__}")

    summary = {
        "orphans": len(orphans),
        "linked": linked,
        "failed": failed,
        "skipped": skipped,
        "dry_run": dry_run,
        "details": details,
    }
    print(f"\nSummary: {linked} linked, {failed} failed, {skipped} skipped")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Remediate orphaned tasks")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview changes")
    group.add_argument("--apply", action="store_true", help="Apply changes")
    args = parser.parse_args()

    result = remediate(dry_run=not args.apply)
    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
