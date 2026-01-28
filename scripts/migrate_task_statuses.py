#!/usr/bin/env python3
"""
Migrate task statuses to TASK-LIFE-01-v1 compliance.

Status mapping:
- TODO/pending → OPEN
- IN_PROGRESS/in_progress → IN_PROGRESS
- DONE/completed → CLOSED

Resolution for CLOSED tasks:
- DONE/completed → IMPLEMENTED

Per GAP-TASK-DATA-QUALITY-001
"""
import sys
sys.path.insert(0, '.')

from governance.stores import get_typedb_client

# Status mapping per TASK-LIFE-01-v1
STATUS_MAP = {
    'TODO': 'OPEN',
    'pending': 'OPEN',
    'OPEN': 'OPEN',  # Already correct
    'IN_PROGRESS': 'IN_PROGRESS',  # Already correct
    'in_progress': 'IN_PROGRESS',
    'DONE': 'CLOSED',
    'completed': 'CLOSED',
    'CLOSED': 'CLOSED',  # Already correct
}

def migrate_statuses(dry_run: bool = True):
    """Migrate all task statuses to TASK-LIFE-01-v1 values."""
    client = get_typedb_client()

    if not client.connect():
        print("ERROR: Failed to connect to TypeDB")
        return

    try:
        # Get all tasks
        tasks = client.get_all_tasks()
        print(f"Found {len(tasks)} tasks in TypeDB")

        # Count statuses
        status_counts = {}
        for task in tasks:
            status = task.status
            status_counts[status] = status_counts.get(status, 0) + 1

        print("\nCurrent status distribution:")
        for status, count in sorted(status_counts.items()):
            new_status = STATUS_MAP.get(status, status)
            marker = " → " + new_status if status != new_status else " (OK)"
            print(f"  {status}: {count}{marker}")

        # Migrate
        migrated = 0
        errors = 0

        for task in tasks:
            old_status = task.status
            new_status = STATUS_MAP.get(old_status)

            if new_status and old_status != new_status:
                if dry_run:
                    print(f"  [DRY RUN] {task.id}: {old_status} → {new_status}")
                else:
                    try:
                        success = client.update_task(task.id, status=new_status)
                        if success:
                            print(f"  [MIGRATED] {task.id}: {old_status} → {new_status}")
                            migrated += 1
                        else:
                            print(f"  [ERROR] {task.id}: Failed to update")
                            errors += 1
                    except Exception as e:
                        print(f"  [ERROR] {task.id}: {e}")
                        errors += 1

        print(f"\n{'[DRY RUN] ' if dry_run else ''}Migration complete:")
        print(f"  Migrated: {migrated}")
        print(f"  Errors: {errors}")
        print(f"  Already correct: {len(tasks) - migrated - errors}")

    finally:
        client.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate task statuses to TASK-LIFE-01-v1")
    parser.add_argument("--execute", action="store_true", help="Execute migration (default: dry run)")
    args = parser.parse_args()

    if args.execute:
        print("=== EXECUTING MIGRATION ===")
        migrate_statuses(dry_run=False)
    else:
        print("=== DRY RUN (use --execute to apply) ===")
        migrate_statuses(dry_run=True)
