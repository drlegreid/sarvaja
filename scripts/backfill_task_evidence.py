#!/usr/bin/env python3
"""
Backfill evidence for historical tasks (EPIC-DR-008).

Per GAP-DATA-INTEGRITY-001: Task evidence is at 3% population.
This script generates meaningful evidence for completed tasks
that were done before evidence workflow was enforced.

Evidence Generation Strategy:
- DONE tasks with linked_sessions: "Completed in session {session_ids}"
- DONE tasks with linked_rules: "Implements {rule_ids}"
- DONE tasks with resolution: "Resolution: {resolution}"
- Other DONE tasks: "[Historical] Marked complete during migration"

Usage:
    python scripts/backfill_task_evidence.py [--dry-run] [--execute]

Created: 2026-01-17
Per: GAP-EPIC-DR-008
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.client import TypeDBClient


def generate_evidence(task) -> str:
    """
    Generate meaningful evidence based on task metadata.

    Args:
        task: Task entity with id, status, linked_sessions, linked_rules, resolution

    Returns:
        Generated evidence string
    """
    parts = []

    # Add resolution if present
    if hasattr(task, 'resolution') and task.resolution and task.resolution != "NONE":
        parts.append(f"Resolution: {task.resolution}")

    # Add linked sessions
    if hasattr(task, 'linked_sessions') and task.linked_sessions:
        if isinstance(task.linked_sessions, list):
            session_ids = ", ".join(task.linked_sessions[:3])  # Max 3 for brevity
            if len(task.linked_sessions) > 3:
                session_ids += f" (+{len(task.linked_sessions) - 3} more)"
        else:
            session_ids = str(task.linked_sessions)
        parts.append(f"Sessions: {session_ids}")

    # Add linked rules
    if hasattr(task, 'linked_rules') and task.linked_rules:
        if isinstance(task.linked_rules, list):
            rule_ids = ", ".join(task.linked_rules[:3])  # Max 3 for brevity
            if len(task.linked_rules) > 3:
                rule_ids += f" (+{len(task.linked_rules) - 3} more)"
        else:
            rule_ids = str(task.linked_rules)
        parts.append(f"Implements: {rule_ids}")

    # Add completion date if available
    if hasattr(task, 'completed_at') and task.completed_at:
        parts.append(f"Completed: {task.completed_at}")

    # Build evidence string
    if parts:
        evidence = " | ".join(parts)
        return f"[Historical backfill] {evidence}"
    else:
        return f"[Historical] Marked complete during EPIC-DR-008 migration ({datetime.now().strftime('%Y-%m-%d')})"


def backfill_task_evidence(dry_run: bool = True):
    """
    Backfill evidence for completed tasks that don't have evidence.

    Args:
        dry_run: If True, only report what would be done
    """
    client = TypeDBClient()
    if not client.connect():
        print("ERROR: Failed to connect to TypeDB")
        return {"error": "Connection failed"}

    try:
        # Get all tasks
        tasks = client.get_all_tasks()

        # Filter: DONE tasks without evidence
        completed_statuses = {"DONE", "completed", "CLOSED"}
        tasks_without_evidence = [
            t for t in tasks
            if t.status in completed_statuses
            and (not hasattr(t, 'evidence') or not t.evidence)
        ]

        # Also count tasks with evidence for stats
        tasks_with_evidence = [
            t for t in tasks
            if hasattr(t, 'evidence') and t.evidence
        ]

        total_completed = len([t for t in tasks if t.status in completed_statuses])

        print(f"=== EPIC-DR-008: Task Evidence Backfill ===")
        print()
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
            evidence = generate_evidence(task)

            if dry_run:
                print(f"  Would update: {task.id}")
                print(f"    Evidence: {evidence[:60]}...")
            else:
                try:
                    # Use update_task_status to set evidence
                    result = client.update_task_status(
                        task.id,
                        task.status,
                        agent_id=task.agent_id,
                        evidence=evidence
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

    finally:
        client.close()


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

    # --execute disables dry-run
    dry_run = not args.execute

    result = backfill_task_evidence(dry_run=dry_run)

    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
