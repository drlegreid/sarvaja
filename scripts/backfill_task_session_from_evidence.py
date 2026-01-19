#!/usr/bin/env python3
"""
Backfill Task→Session Linkages from Evidence Files.

Per GAP-UI-AUDIT-2026-01-18: Parse evidence/SESSION-*.md files
to extract task IDs mentioned and link them to sessions in TypeDB.

Usage:
    python3 scripts/backfill_task_session_from_evidence.py --dry-run
    python3 scripts/backfill_task_session_from_evidence.py --apply

Created: 2026-01-18
"""

import argparse
import re
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Task ID patterns to match
TASK_PATTERNS = [
    r'\b(P\d+\.\d+)\b',           # P4.1, P10.2
    r'\b(FH-\d+)\b',               # FH-001
    r'\b(RD-\d+)\b',               # RD-001
    r'\b(KAN-\d+)\b',              # KAN-001
    r'\b(GAP-[A-Z]+-\d+)\b',       # GAP-UI-001
    r'\b(UI-AUDIT-\d+)\b',         # UI-AUDIT-001
    r'\b(ATEST-\d+)\b',            # ATEST-001
]

# Compile patterns
TASK_REGEX = re.compile('|'.join(TASK_PATTERNS))


def extract_session_id_from_filename(filename: str) -> str | None:
    """Extract session ID from evidence filename."""
    # SESSION-YYYY-MM-DD-TOPIC.md -> SESSION-YYYY-MM-DD-TOPIC
    match = re.match(r'(SESSION-\d{4}-\d{2}-\d{2}[^.]*)', filename)
    return match.group(1) if match else None


def extract_task_ids_from_content(content: str) -> set[str]:
    """Extract unique task IDs from evidence file content."""
    matches = TASK_REGEX.findall(content)
    # Flatten tuples from alternation groups
    task_ids = set()
    for match in matches:
        if isinstance(match, tuple):
            for m in match:
                if m:
                    task_ids.add(m)
        elif match:
            task_ids.add(match)
    return task_ids


def scan_evidence_files(evidence_dir: Path) -> dict[str, set[str]]:
    """Scan evidence directory for session→tasks mappings."""
    mappings = {}

    for evidence_file in evidence_dir.glob("SESSION-*.md"):
        session_id = extract_session_id_from_filename(evidence_file.name)
        if not session_id:
            continue

        content = evidence_file.read_text(encoding='utf-8', errors='ignore')
        task_ids = extract_task_ids_from_content(content)

        if task_ids:
            mappings[session_id] = task_ids

    return mappings


def get_existing_linkages() -> dict[str, set[str]]:
    """Get existing task→session linkages from API."""
    import requests

    existing = {}
    try:
        response = requests.get("http://localhost:8082/api/tasks?limit=200", timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', data)
            for task in items:
                task_id = task.get('task_id')
                sessions = task.get('linked_sessions') or []
                if sessions:
                    existing[task_id] = set(sessions)
    except Exception as e:
        print(f"Warning: Could not fetch existing linkages: {e}")

    return existing


def get_existing_tasks() -> set[str]:
    """Get set of task IDs that exist in TypeDB."""
    import requests

    existing = set()
    try:
        response = requests.get("http://localhost:8082/api/tasks?limit=200", timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', data)
            for task in items:
                existing.add(task.get('task_id'))
    except Exception as e:
        print(f"Warning: Could not fetch existing tasks: {e}")

    return existing


def get_existing_sessions() -> set[str]:
    """Get set of session IDs that exist in TypeDB."""
    import requests

    existing = set()
    try:
        response = requests.get("http://localhost:8082/api/sessions?limit=200", timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', data)
            for session in items:
                existing.add(session.get('session_id'))
    except Exception as e:
        print(f"Warning: Could not fetch existing sessions: {e}")

    return existing


def create_session_via_api(session_id: str, description: str = None) -> bool:
    """Create a session via REST API."""
    import requests

    try:
        response = requests.post(
            "http://localhost:8082/api/sessions",
            json={
                "session_id": session_id,
                "description": description or f"Backfilled from evidence file"
            },
            timeout=10
        )
        return response.status_code in (200, 201)
    except Exception as e:
        print(f"Failed to create session {session_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Backfill task→session linkages from evidence')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be linked without applying')
    parser.add_argument('--apply', action='store_true', help='Apply linkages to TypeDB via MCP')
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Error: Specify --dry-run or --apply")
        sys.exit(1)

    evidence_dir = PROJECT_ROOT / "evidence"
    if not evidence_dir.exists():
        print(f"Error: Evidence directory not found: {evidence_dir}")
        sys.exit(1)

    print("Scanning evidence files...")
    mappings = scan_evidence_files(evidence_dir)

    print(f"Found {len(mappings)} sessions with task references")

    # Get existing state
    existing_linkages = get_existing_linkages()
    existing_tasks = get_existing_tasks()
    existing_sessions = get_existing_sessions()

    print(f"Existing tasks in TypeDB: {len(existing_tasks)}")
    print(f"Existing sessions in TypeDB: {len(existing_sessions)}")
    print(f"Tasks with linkages: {len(existing_linkages)}")

    # Calculate sessions to create and linkages needed
    sessions_to_create = set()
    new_linkages = []
    missing_tasks = set()

    for session_id, task_ids in mappings.items():
        # Check if session needs to be created
        if session_id not in existing_sessions:
            sessions_to_create.add(session_id)

        for task_id in task_ids:
            if task_id not in existing_tasks:
                missing_tasks.add(task_id)
                continue

            existing_task_sessions = existing_linkages.get(task_id, set())
            if session_id not in existing_task_sessions:
                new_linkages.append((task_id, session_id))

    print(f"\n{'='*60}")
    print("BACKFILL SUMMARY")
    print('='*60)
    print(f"Sessions to create: {len(sessions_to_create)}")
    print(f"New linkages to create: {len(new_linkages)}")
    print(f"Tasks not in TypeDB (skipped): {len(missing_tasks)}")

    if sessions_to_create:
        print(f"\nSessions to create (first 10):")
        for s in sorted(sessions_to_create)[:10]:
            print(f"  {s}")

    if new_linkages:
        print(f"\nSample new linkages:")
        for task_id, session_id in new_linkages[:10]:
            print(f"  {task_id} → {session_id}")
        if len(new_linkages) > 10:
            print(f"  ... and {len(new_linkages) - 10} more")

    if missing_tasks:
        print(f"\nMissing tasks (first 10):")
        for task_id in list(missing_tasks)[:10]:
            print(f"  {task_id}")

    if args.apply and (sessions_to_create or new_linkages):
        print(f"\n{'='*60}")
        print("APPLYING CHANGES...")
        print('='*60)

        # Step 1: Create missing sessions via REST API
        if sessions_to_create:
            print("\nCreating missing sessions...")
            sessions_created = 0
            for session_id in sorted(sessions_to_create):
                if create_session_via_api(session_id):
                    sessions_created += 1
                    print(f"  ✓ Created session: {session_id}")
                else:
                    print(f"  ✗ Failed to create: {session_id}")
            print(f"Sessions created: {sessions_created}/{len(sessions_to_create)}")

        # Step 2: Create task-session linkages
        if new_linkages:
            print("\nCreating linkages...")
            try:
                from governance.stores import get_typedb_client
                client = get_typedb_client()
                if not client:
                    print("ERROR: TypeDB client not available")
                    sys.exit(1)

                success = 0
                errors = 0

                for task_id, session_id in new_linkages:
                    try:
                        result = client.link_task_to_session(task_id, session_id)
                        if result:
                            success += 1
                            print(f"  ✓ {task_id} → {session_id}")
                        else:
                            errors += 1
                            print(f"  ✗ {task_id} → {session_id} (failed)")
                    except Exception as e:
                        errors += 1
                        print(f"  ✗ {task_id} → {session_id}: {e}")

                print(f"\nLinkages: {success} created, {errors} errors")

            except ImportError as e:
                print(f"ERROR: Could not import governance modules: {e}")
                print("Run inside container for linking step.")
                sys.exit(1)
    elif args.dry_run:
        print("\n[DRY RUN] No changes applied. Use --apply to create linkages.")


if __name__ == "__main__":
    main()
