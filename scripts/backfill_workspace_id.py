#!/usr/bin/env python3
"""
FIX-COL-007: Backfill workspace_id for existing tasks.

All tasks in TypeDB belong to the Sarvaja Platform workspace (WS-9147535A).
This script links tasks with null workspace_id to that workspace via PUT API.

Usage:
    python3 scripts/backfill_workspace_id.py --dry-run    # Preview
    python3 scripts/backfill_workspace_id.py               # Apply
"""

import argparse
import sys
import httpx

API_BASE = "http://localhost:8082"
WORKSPACE_ID = "WS-9147535A"  # Sarvaja Platform Dev


def get_all_tasks():
    """Fetch all tasks from API."""
    tasks = []
    offset = 0
    limit = 50
    while True:
        resp = httpx.get(f"{API_BASE}/api/tasks?offset={offset}&limit={limit}", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        tasks.extend(data["items"])
        if not data["pagination"]["has_more"]:
            break
        offset += limit
    return tasks


def backfill(dry_run=True):
    """Backfill workspace_id for tasks missing it."""
    print(f"Fetching all tasks from {API_BASE}...")
    tasks = get_all_tasks()
    print(f"Total tasks: {len(tasks)}")

    null_ws = [t for t in tasks if not t.get("workspace_id")]
    already_set = len(tasks) - len(null_ws)
    print(f"Already have workspace_id: {already_set}")
    print(f"Missing workspace_id: {len(null_ws)}")

    if dry_run:
        print(f"\nDRY RUN — would link {len(null_ws)} tasks to {WORKSPACE_ID}")
        for t in null_ws[:10]:
            print(f"  {t['task_id']}")
        if len(null_ws) > 10:
            print(f"  ... and {len(null_ws) - 10} more")
        return

    print(f"\nLinking {len(null_ws)} tasks to workspace {WORKSPACE_ID}...")
    success = 0
    failed = 0
    for i, t in enumerate(null_ws):
        tid = t["task_id"]
        try:
            resp = httpx.put(
                f"{API_BASE}/api/tasks/{tid}",
                json={"workspace_id": WORKSPACE_ID},
                timeout=10,
            )
            if resp.status_code == 200:
                success += 1
            else:
                failed += 1
                print(f"  FAIL {tid}: HTTP {resp.status_code}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {tid}: {type(e).__name__}")
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(null_ws)} (ok={success}, fail={failed})")

    print(f"\nDone: {success} linked, {failed} failed out of {len(null_ws)}")


def main():
    parser = argparse.ArgumentParser(description="FIX-COL-007: Backfill workspace_id")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()
    backfill(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
