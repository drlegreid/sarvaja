#!/usr/bin/env python3
"""
Backfill evidence for historical tasks via REST API (EPIC-DR-008).

Uses REST API to work around TypeDB driver Python 3.13 incompatibility.

Usage:
    python scripts/backfill_task_evidence_rest.py [--dry-run] [--execute]

Created: 2026-01-17
Per: GAP-EPIC-DR-008
"""

import argparse
import sys
import requests
from datetime import datetime

API_BASE = "http://localhost:8082"


def get_tasks():
    """Get all tasks via REST API."""
    response = requests.get(f"{API_BASE}/api/tasks?limit=200", timeout=30)
    if response.status_code != 200:
        print(f"ERROR: Failed to get tasks: {response.status_code}")
        return []

    data = response.json()
    # Handle paginated response
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data


def generate_evidence(task: dict) -> str:
    """Generate meaningful evidence based on task metadata."""
    parts = []

    # Add resolution if present
    resolution = task.get("resolution")
    if resolution and resolution != "NONE":
        parts.append(f"Resolution: {resolution}")

    # Add linked sessions
    linked_sessions = task.get("linked_sessions")
    if linked_sessions:
        if isinstance(linked_sessions, list):
            session_ids = ", ".join(linked_sessions[:3])
            if len(linked_sessions) > 3:
                session_ids += f" (+{len(linked_sessions) - 3} more)"
        else:
            session_ids = str(linked_sessions)
        parts.append(f"Sessions: {session_ids}")

    # Add linked rules
    linked_rules = task.get("linked_rules")
    if linked_rules:
        if isinstance(linked_rules, list):
            rule_ids = ", ".join(linked_rules[:3])
            if len(linked_rules) > 3:
                rule_ids += f" (+{len(linked_rules) - 3} more)"
        else:
            rule_ids = str(linked_rules)
        parts.append(f"Implements: {rule_ids}")

    # Add completion date if available
    completed_at = task.get("completed_at")
    if completed_at:
        parts.append(f"Completed: {completed_at[:10]}")

    # Build evidence string
    if parts:
        evidence = " | ".join(parts)
        return f"[Historical backfill] {evidence}"
    else:
        return f"[Historical] Marked complete during EPIC-DR-008 migration ({datetime.now().strftime('%Y-%m-%d')})"


def update_task_evidence(task_id: str, evidence: str) -> bool:
    """Update task evidence via REST API."""
    # Use PUT /api/tasks/{task_id} to update
    response = requests.put(
        f"{API_BASE}/api/tasks/{task_id}",
        json={"evidence": evidence},
        timeout=10
    )
    return response.status_code == 200


def backfill_task_evidence(dry_run: bool = True):
    """Backfill evidence for completed tasks without evidence."""

    print("=== EPIC-DR-008: Task Evidence Backfill (REST API) ===")
    print()

    tasks = get_tasks()
    if not tasks:
        return {"error": "No tasks found"}

    # Filter: DONE tasks without evidence
    completed_statuses = {"DONE", "completed", "CLOSED"}
    tasks_without_evidence = [
        t for t in tasks
        if t.get("status") in completed_statuses
        and not t.get("evidence")
    ]

    tasks_with_evidence = [
        t for t in tasks
        if t.get("evidence")
    ]

    total_completed = len([t for t in tasks if t.get("status") in completed_statuses])

    print(f"Total tasks: {len(tasks)}")
    print(f"Completed tasks: {total_completed}")
    print(f"With evidence: {len(tasks_with_evidence)} ({100*len(tasks_with_evidence)//max(1, total_completed)}%)")
    print(f"Without evidence: {len(tasks_without_evidence)}")
    print(f"Dry run: {dry_run}")
    print()

    if dry_run:
        print("=== DRY RUN - No changes will be made ===")
        print()

    updated = 0
    errors = 0

    for task in tasks_without_evidence:
        task_id = task.get("task_id") or task.get("id")
        evidence = generate_evidence(task)

        if dry_run:
            print(f"  Would update: {task_id}")
            print(f"    Evidence: {evidence[:70]}...")
        else:
            try:
                if update_task_evidence(task_id, evidence):
                    print(f"  Updated: {task_id}")
                    updated += 1
                else:
                    print(f"  FAILED: {task_id}")
                    errors += 1
            except Exception as e:
                print(f"  ERROR: {task_id} - {e}")
                errors += 1

    print()
    print("=== Summary ===")
    print(f"Tasks processed: {len(tasks_without_evidence)}")
    if not dry_run:
        print(f"Successfully updated: {updated}")
        print(f"Errors: {errors}")
        new_with_evidence = len(tasks_with_evidence) + updated
        new_percent = 100 * new_with_evidence // max(1, total_completed)
        print(f"New evidence coverage: {new_with_evidence}/{total_completed} ({new_percent}%)")

    return {
        "total_tasks": len(tasks),
        "total_completed": total_completed,
        "tasks_with_evidence_before": len(tasks_with_evidence),
        "tasks_without_evidence": len(tasks_without_evidence),
        "updated": updated if not dry_run else 0,
        "errors": errors if not dry_run else 0,
        "dry_run": dry_run
    }


def main():
    parser = argparse.ArgumentParser(
        description="Backfill evidence for historical tasks (EPIC-DR-008)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Only show what would be done (default: True)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the backfill (disables dry-run)"
    )

    args = parser.parse_args()
    dry_run = not args.execute

    result = backfill_task_evidence(dry_run=dry_run)

    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
