#!/usr/bin/env python3
"""
Backfill Task Evidence Script
=============================
Populates evidence field for DONE tasks that have body content.

Per GAP-EPIC-DR-008: Task evidence population (3%→50%)

Usage:
    python3 scripts/backfill_task_evidence.py [--live]

Created: 2026-01-17
"""

import sys
import argparse
import json
import urllib.request
import urllib.error
from datetime import datetime

API_BASE = "http://localhost:8082/api"


def get_all_tasks():
    """Fetch all tasks via REST API."""
    url = f"{API_BASE}/tasks?limit=200"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data.get("items", [])
    except urllib.error.URLError as e:
        print(f"ERROR: Failed to fetch tasks: {e}", file=sys.stderr)
        return []


def update_task_evidence(task_id: str, evidence: str, status: str = "DONE") -> bool:
    """Update task evidence via REST API."""
    url = f"{API_BASE}/tasks/{task_id}"
    payload = json.dumps({"evidence": evidence, "status": status}).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="PUT"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 200
    except urllib.error.URLError as e:
        print(f"  Error updating {task_id}: {e}", file=sys.stderr)
        return False


def backfill_evidence(dry_run: bool = True):
    """Backfill evidence for DONE tasks."""
    # Get all tasks via REST API
    all_tasks = get_all_tasks()
    if not all_tasks:
        print("ERROR: No tasks retrieved", file=sys.stderr)
        return 1

    # Filter DONE tasks without evidence
    done_without_evidence = [
        t for t in all_tasks
        if t.get("status") == "DONE" and not t.get("evidence")
    ]

    print(f"Total tasks: {len(all_tasks)}")
    print(f"DONE tasks: {len([t for t in all_tasks if t.get('status') == 'DONE'])}")
    print(f"DONE without evidence: {len(done_without_evidence)}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)

    updated = 0
    errors = 0

    for task in done_without_evidence:
        task_id = task.get("task_id")
        body = task.get("body") or ""
        name = task.get("description") or task.get("name", task_id)

        # Generate evidence from body or name
        if body and len(body) > 10:
            evidence = f"Completed: {body[:200]}..."
        else:
            evidence = f"Completed: {name}"

        # Add linked sessions if available
        linked_sessions = task.get("linked_sessions")
        if linked_sessions:
            sessions = ", ".join(linked_sessions)
            evidence += f" | Sessions: {sessions}"

        # Add backfill marker
        evidence += f" | Backfilled: {datetime.now().strftime('%Y-%m-%d')}"

        print(f"\n{task_id}: {name[:40]}...")
        print(f"  Evidence: {evidence[:80]}...")

        if not dry_run:
            if update_task_evidence(task_id, evidence):
                print(f"  ✓ Updated")
                updated += 1
            else:
                print(f"  ✗ Failed to update")
                errors += 1
        else:
            print(f"  [dry-run] Would update")
            updated += 1

    print("\n" + "=" * 60)
    print(f"Summary: {updated} {'would be ' if dry_run else ''}updated, {errors} errors")

    if dry_run and updated > 0:
        print("\nRun with --live to apply changes")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill evidence for DONE tasks"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Apply changes (default is dry-run)"
    )
    args = parser.parse_args()

    sys.exit(backfill_evidence(dry_run=not args.live))
