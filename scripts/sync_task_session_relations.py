#!/usr/bin/env python3
"""
Sync Task-Session Relations to TypeDB.

Per GAP-DATA-INTEGRITY-001: Sync `linked_sessions` attribute to TypeDB `completed-in` relations.
This fixes session `tasks_completed` counts showing 0 instead of actual values.

Usage:
    scripts/pytest.sh scripts/sync_task_session_relations.py
    # Or directly in container:
    python scripts/sync_task_session_relations.py

Created: 2026-01-17
"""

import sys
sys.path.insert(0, "/app")

from governance.stores import get_typedb_client


def sync_task_session_relations():
    """Sync linked_sessions from tasks to TypeDB completed-in relations."""
    client = get_typedb_client()
    if not client:
        print("ERROR: TypeDB client not available")
        return 1

    # Get all tasks with linked_sessions
    tasks = client.get_all_tasks()
    total = len(tasks)
    synced = 0
    already_linked = 0
    errors = 0

    print(f"Found {total} tasks to check")

    for task in tasks:
        linked = task.linked_sessions or []
        if not linked:
            continue

        for session_id in linked:
            try:
                # Check if relation already exists
                existing = client._execute_query(f"""
                    match
                        $t isa task, has task-id "{task.task_id}";
                        $s isa work-session, has session-id "{session_id}";
                        (completed-task: $t, hosting-session: $s) isa completed-in;
                    get $t;
                """)
                if existing:
                    already_linked += 1
                    continue

                # Create the relation
                success = client.link_task_to_session(task.task_id, session_id)
                if success:
                    synced += 1
                    print(f"  Linked: {task.task_id} -> {session_id}")
                else:
                    errors += 1
                    print(f"  FAILED: {task.task_id} -> {session_id}")
            except Exception as e:
                errors += 1
                print(f"  ERROR: {task.task_id} -> {session_id}: {e}")

    print(f"\nSync complete:")
    print(f"  Total tasks: {total}")
    print(f"  Already linked: {already_linked}")
    print(f"  Newly synced: {synced}")
    print(f"  Errors: {errors}")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(sync_task_session_relations())
