#!/usr/bin/env python3
"""
Backfill agent_id for historical tasks (EPIC-DR-007).

Per GAP-DATA-INTEGRITY-001: Task agent_id is at 0% population.
This script assigns a default agent to tasks that were completed
before the workflow claim system was implemented.

Usage:
    python scripts/backfill_agent_id.py [--dry-run] [--agent claude-code]

Created: 2026-01-17
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.client import TypeDBClient


def backfill_agent_ids(default_agent: str = "claude-code", dry_run: bool = True):
    """
    Backfill agent_id for tasks that don't have one assigned.

    Args:
        default_agent: Default agent ID to assign (default: claude-code)
        dry_run: If True, only report what would be done
    """
    client = TypeDBClient()
    if not client.connect():
        print("ERROR: Failed to connect to TypeDB")
        return {"error": "Connection failed"}

    try:
        # Get all tasks
        tasks = client.get_all_tasks()

        # Filter tasks without agent_id
        tasks_without_agent = [t for t in tasks if not t.agent_id]

        print(f"Total tasks: {len(tasks)}")
        print(f"Tasks without agent_id: {len(tasks_without_agent)}")
        print(f"Default agent: {default_agent}")
        print(f"Dry run: {dry_run}")
        print()

        if dry_run:
            print("=== DRY RUN - No changes will be made ===")
            print()

        updated = 0
        errors = 0

        for task in tasks_without_agent:
            if dry_run:
                print(f"  Would update: {task.id} (status={task.status})")
            else:
                try:
                    # Use update_task_status to set agent_id
                    # Keep existing status
                    result = client.update_task_status(
                        task.id,
                        task.status,
                        agent_id=default_agent
                    )
                    if result:
                        print(f"  Updated: {task.id}")
                        updated += 1
                    else:
                        print(f"  FAILED: {task.id} (update returned None)")
                        errors += 1
                except Exception as e:
                    print(f"  ERROR: {task.id} - {e}")
                    errors += 1

        print()
        print("=== Summary ===")
        print(f"Tasks processed: {len(tasks_without_agent)}")
        if not dry_run:
            print(f"Successfully updated: {updated}")
            print(f"Errors: {errors}")

        return {
            "total_tasks": len(tasks),
            "tasks_without_agent": len(tasks_without_agent),
            "updated": updated if not dry_run else 0,
            "errors": errors if not dry_run else 0,
            "dry_run": dry_run
        }

    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill agent_id for historical tasks (EPIC-DR-007)"
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
    parser.add_argument(
        "--agent",
        default="claude-code",
        help="Default agent ID to assign (default: claude-code)"
    )

    args = parser.parse_args()

    # --execute disables dry-run
    dry_run = not args.execute

    result = backfill_agent_ids(
        default_agent=args.agent,
        dry_run=dry_run
    )

    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
