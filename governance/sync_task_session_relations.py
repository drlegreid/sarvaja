#!/usr/bin/env python3
"""
Sync Task-Session Relations via REST API.

Per GAP-DATA-INTEGRITY-001: Sync `linked_sessions` attribute to TypeDB `completed-in` relations.
This fixes session `tasks_completed` counts showing 0 instead of actual values.

Usage:
    python governance/sync_task_session_relations.py

Created: 2026-01-17
"""

import requests

API_BASE = "http://localhost:8082"


def sync_task_session_relations():
    """Sync linked_sessions from tasks to TypeDB completed-in relations via REST API."""

    # Get all tasks
    response = requests.get(f"{API_BASE}/api/tasks?limit=200")
    if response.status_code != 200:
        print(f"ERROR: Failed to get tasks: {response.status_code}")
        return 1

    data = response.json()
    tasks = data.get("items", [])
    total = len(tasks)
    synced = 0
    already_linked = 0
    errors = 0
    skipped = 0

    print(f"Found {total} tasks to check")

    for task in tasks:
        task_id = task.get("task_id")
        linked = task.get("linked_sessions") or []

        if not linked:
            skipped += 1
            continue

        for session_id in linked:
            try:
                # Create the relation via API (POST /tasks/{task_id}/sessions/{session_id})
                link_response = requests.post(
                    f"{API_BASE}/api/tasks/{task_id}/sessions/{session_id}"
                )

                if link_response.status_code in (200, 201):
                    synced += 1
                    print(f"  Linked: {task_id} -> {session_id}")
                elif link_response.status_code == 409:
                    # Already exists or conflict
                    already_linked += 1
                elif link_response.status_code == 404:
                    # Session doesn't exist in TypeDB
                    print(f"  SKIP (no session): {task_id} -> {session_id}")
                    skipped += 1
                else:
                    errors += 1
                    print(f"  FAILED ({link_response.status_code}): {task_id} -> {session_id}")
            except Exception as e:
                errors += 1
                print(f"  ERROR: {task_id} -> {session_id}: {e}")

    print("\nSync complete:")
    print(f"  Total tasks: {total}")
    print(f"  Skipped (no sessions): {skipped}")
    print(f"  Already linked: {already_linked}")
    print(f"  Newly synced: {synced}")
    print(f"  Errors: {errors}")

    # Verify by checking a session
    print("\nVerification:")
    verify_response = requests.get(f"{API_BASE}/api/sessions/SESSION-2026-01-11-B2A608")
    if verify_response.status_code == 200:
        session = verify_response.json()
        print(f"  SESSION-2026-01-11-B2A608: tasks_completed = {session.get('tasks_completed')}")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(sync_task_session_relations())
