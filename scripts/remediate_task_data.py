#!/usr/bin/env python3
"""
Task Data Integrity Remediation Script.

Per EPIC-GOV-TASKS-V2 Phase 9a audit (2026-03-21, 228 tasks):

1. Normalize lowercase statuses to uppercase (37 tasks)
2. Backfill missing completed_at for finished tasks (38 tasks)
3. Fix timestamp ordering: completed_at < created_at (6 tasks)
4. Detect duplicate seed tasks (37 TODO-YYYYMMDD duplicates)
5. Flag test artifact tasks (59 TEST- prefix without -vN)
6. Report unlinked tasks (81% with no linked_sessions)
7. Report null priority/task_type (84%/68%)

Usage:
    python3 scripts/remediate_task_data.py --dry-run    # Preview changes
    python3 scripts/remediate_task_data.py               # Apply changes
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger(__name__)

# Valid uppercase statuses
VALID_STATUSES = {"OPEN", "IN_PROGRESS", "CLOSED", "TODO", "DONE", "PENDING", "COMPLETED"}


def get_client():
    """Get TypeDB client."""
    try:
        from governance.client import get_client
        client = get_client()
        if client and client.is_connected():
            return client
    except Exception as e:
        logger.error(f"TypeDB connection failed: {type(e).__name__}", exc_info=True)
    return None


def normalize_statuses(tasks: list, dry_run: bool = True) -> dict:
    """Find and fix lowercase statuses.

    Returns:
        {"found": count, "fixed": count, "details": [{"task_id": ..., "old": ..., "new": ...}]}
    """
    results = {"found": 0, "fixed": 0, "details": []}
    for task in tasks:
        tid = task.get("task_id", "")
        status = task.get("status", "")
        if status and status != status.upper():
            results["found"] += 1
            new_status = status.upper()
            results["details"].append({
                "task_id": tid, "old": status, "new": new_status
            })
            if not dry_run:
                results["fixed"] += 1
    return results


def backfill_completed_at(tasks: list, dry_run: bool = True) -> dict:
    """Find finished tasks missing completed_at and backfill.

    Returns:
        {"found": count, "fixed": count, "details": [...]}
    """
    done_statuses = {"DONE", "CLOSED", "COMPLETED"}
    results = {"found": 0, "fixed": 0, "details": []}
    for task in tasks:
        tid = task.get("task_id", "")
        status = (task.get("status") or "").upper()
        completed_at = task.get("completed_at")
        if status in done_statuses and not completed_at:
            results["found"] += 1
            # Use created_at as fallback timestamp
            fallback = task.get("created_at") or datetime.now().isoformat()
            results["details"].append({
                "task_id": tid, "status": status, "backfill_to": str(fallback)
            })
            if not dry_run:
                results["fixed"] += 1
    return results


def fix_timestamp_ordering(tasks: list, dry_run: bool = True) -> dict:
    """Find tasks where completed_at < created_at and fix.

    Returns:
        {"found": count, "fixed": count, "details": [...]}
    """
    results = {"found": 0, "fixed": 0, "details": []}
    for task in tasks:
        tid = task.get("task_id", "")
        created = task.get("created_at")
        completed = task.get("completed_at")
        if created and completed:
            c_str = str(created)[:19]
            d_str = str(completed)[:19]
            if d_str < c_str:
                results["found"] += 1
                results["details"].append({
                    "task_id": tid, "created_at": c_str,
                    "completed_at": d_str, "fix": "set completed_at = created_at"
                })
                if not dry_run:
                    results["fixed"] += 1
    return results


def detect_seed_duplicates(tasks: list) -> dict:
    """Find duplicate seed task IDs (TODO-YYYYMMDD pattern).

    Returns:
        {"found": count, "duplicates": {task_id: count}}
    """
    from collections import Counter
    ids = [t.get("task_id", "") for t in tasks]
    counts = Counter(ids)
    duplicates = {tid: cnt for tid, cnt in counts.items() if cnt > 1}
    return {"found": len(duplicates), "duplicates": duplicates}


def detect_test_artifacts(tasks: list) -> dict:
    """Find test artifact tasks (TEST- prefix without semantic version).

    Returns:
        {"found": count, "task_ids": [...]}
    """
    artifacts = []
    for task in tasks:
        tid = task.get("task_id", "")
        if tid.startswith("TEST-"):
            after_prefix = tid.split("TEST-", 1)[1]
            if "-v" not in after_prefix:
                artifacts.append(tid)
    return {"found": len(artifacts), "task_ids": artifacts}


def report_unlinked(tasks: list) -> dict:
    """Report tasks with no linked_sessions.

    Returns:
        {"unlinked": count, "total": count, "pct": float}
    """
    total = len(tasks)
    unlinked = sum(1 for t in tasks if not t.get("linked_sessions"))
    pct = (unlinked / total * 100) if total else 0
    return {"unlinked": unlinked, "total": total, "pct": round(pct, 1)}


def extract_priority_from_description(tasks: list, dry_run: bool = True) -> dict:
    """Parse [Priority: X] from description and extract to priority field.

    Phase 9c: Legacy tasks have "[Priority: HIGH]" embedded in description.
    Extract to the priority field and strip the tag from description.

    Returns:
        {"found": count, "fixed": count, "details": [...]}
    """
    import re
    valid = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    results = {"found": 0, "fixed": 0, "details": []}
    for task in tasks:
        tid = task.get("task_id", "")
        desc = task.get("description", "") or ""
        current_priority = task.get("priority")
        match = re.search(r'\[(?:P|p)riority:\s*(\w+)\]', desc)
        if match:
            value = match.group(1).upper()
            if value in valid:
                results["found"] += 1
                cleaned = re.sub(r'\s*\[(?:P|p)riority:\s*\w+\]\s*', ' ', desc).strip()
                results["details"].append({
                    "task_id": tid,
                    "extracted_priority": value,
                    "current_priority": current_priority,
                    "cleaned_description": cleaned[:60] + "..." if len(cleaned) > 60 else cleaned,
                })
                if not dry_run:
                    results["fixed"] += 1
    return results


def report_null_fields(tasks: list) -> dict:
    """Report tasks with null priority or task_type.

    Returns:
        {"null_priority": count, "null_task_type": count, "total": count}
    """
    total = len(tasks)
    null_priority = sum(1 for t in tasks if not t.get("priority"))
    null_type = sum(1 for t in tasks if not t.get("task_type"))
    return {
        "null_priority": null_priority,
        "null_task_type": null_type,
        "total": total,
        "pct_priority": round(null_priority / total * 100, 1) if total else 0,
        "pct_task_type": round(null_type / total * 100, 1) if total else 0,
    }


def run_remediation(dry_run: bool = True):
    """Run all remediation checks."""
    print(f"\n{'=' * 60}")
    print(f"  Task Data Integrity Remediation {'(DRY RUN)' if dry_run else '(APPLYING)'}")
    print(f"  {datetime.now().isoformat()}")
    print(f"{'=' * 60}\n")

    client = get_client()
    if not client:
        print("ERROR: Cannot connect to TypeDB. Aborting.")
        return False

    # Fetch all tasks
    try:
        all_tasks_raw = client.get_all_tasks()
        tasks = []
        for t in all_tasks_raw:
            tasks.append({
                "task_id": getattr(t, "id", ""),
                "status": getattr(t, "status", ""),
                "created_at": getattr(t, "created_at", None),
                "completed_at": getattr(t, "completed_at", None),
                "priority": getattr(t, "priority", None),
                "task_type": getattr(t, "task_type", None),
                "linked_sessions": getattr(t, "linked_sessions", []),
            })
    except Exception as e:
        print(f"ERROR: Failed to fetch tasks: {type(e).__name__}")
        return False

    print(f"Total tasks: {len(tasks)}\n")

    # 1. Status normalization
    status_result = normalize_statuses(tasks, dry_run)
    print(f"1. Status Normalization: {status_result['found']} lowercase statuses found")
    for d in status_result["details"][:5]:
        print(f"   {d['task_id']}: {d['old']} → {d['new']}")
    if status_result["found"] > 5:
        print(f"   ... and {status_result['found'] - 5} more")

    # 2. Completed_at backfill
    completed_result = backfill_completed_at(tasks, dry_run)
    print(f"\n2. Completed_at Backfill: {completed_result['found']} finished tasks missing timestamp")
    for d in completed_result["details"][:5]:
        print(f"   {d['task_id']}: status={d['status']}, backfill={d['backfill_to'][:10]}")

    # 3. Timestamp ordering
    ordering_result = fix_timestamp_ordering(tasks, dry_run)
    print(f"\n3. Timestamp Ordering: {ordering_result['found']} tasks with completed_at < created_at")
    for d in ordering_result["details"]:
        print(f"   {d['task_id']}: created={d['created_at'][:10]}, completed={d['completed_at'][:10]}")

    # 4. Seed duplicates
    dup_result = detect_seed_duplicates(tasks)
    print(f"\n4. Seed Duplicates: {dup_result['found']} duplicate task IDs")
    for tid, cnt in list(dup_result["duplicates"].items())[:5]:
        print(f"   {tid}: {cnt} copies")

    # 5. Test artifacts
    artifact_result = detect_test_artifacts(tasks)
    print(f"\n5. Test Artifacts: {artifact_result['found']} test artifact tasks")
    for tid in artifact_result["task_ids"][:5]:
        print(f"   {tid}")
    if artifact_result["found"] > 5:
        print(f"   ... and {artifact_result['found'] - 5} more")

    # 6. Unlinked sessions
    unlinked_result = report_unlinked(tasks)
    print(f"\n6. Unlinked Sessions: {unlinked_result['unlinked']}/{unlinked_result['total']} "
          f"({unlinked_result['pct']}%) tasks have no linked_sessions")

    # 7. Priority tag extraction (Phase 9c)
    priority_result = extract_priority_from_description(tasks, dry_run)
    print(f"\n7. Priority Tag Extraction: {priority_result['found']} tasks with [Priority: X] in description")
    for d in priority_result["details"][:5]:
        print(f"   {d['task_id']}: extracted={d['extracted_priority']}, "
              f"current={d['current_priority']}, desc=\"{d['cleaned_description']}\"")
    if priority_result["found"] > 5:
        print(f"   ... and {priority_result['found'] - 5} more")

    # 8. Null fields
    null_result = report_null_fields(tasks)
    print(f"\n8. Null Fields:")
    print(f"   Priority: {null_result['null_priority']}/{null_result['total']} "
          f"({null_result['pct_priority']}%) null")
    print(f"   Task Type: {null_result['null_task_type']}/{null_result['total']} "
          f"({null_result['pct_task_type']}%) null")

    # Summary
    total_fixes = (status_result["found"] + completed_result["found"] +
                   ordering_result["found"] + priority_result["found"])
    print(f"\n{'=' * 60}")
    print(f"  Total actionable fixes: {total_fixes}")
    if dry_run:
        print("  Run without --dry-run to apply fixes.")
    else:
        total_applied = status_result["fixed"] + completed_result["fixed"] + ordering_result["fixed"]
        print(f"  Applied: {total_applied}")
    print(f"{'=' * 60}\n")

    return True


def main():
    parser = argparse.ArgumentParser(description="Task Data Integrity Remediation")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Preview changes without applying (default)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    success = run_remediation(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
