#!/usr/bin/env python3
"""
Migrate TypeDB data: EPIC-TASK-TAXONOMY-V2 Session 4.

Performs three migrations:
1. Normalize deprecated task types: gap→bug, specification→spec, epic→feature
2. Normalize CLOSED status → DONE
3. Verify counts pre/post migration

Idempotent — safe to re-run (only updates tasks that still have old values).

Usage:
    python3 scripts/migrate_task_taxonomy_v2.py [--dry-run]
"""
import os
import sys
import argparse

try:
    from typedb.driver import TypeDB, Credentials, DriverOptions, TransactionType
except ImportError:
    print("ERROR: typedb-driver not installed. Run: pip install typedb-driver")
    sys.exit(1)

TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE = "sim-ai-governance"

# Type aliases: old → canonical
TYPE_ALIASES = {
    "gap": "bug",
    "specification": "spec",
    "epic": "feature",
    "story": "feature",
}

# Status aliases: old → canonical
STATUS_ALIASES = {
    "CLOSED": "DONE",
}


def get_driver():
    """Create TypeDB driver connection."""
    address = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
    return TypeDB.cloud_driver(
        address,
        Credentials("admin", "password", tls_enabled=False),
        DriverOptions(),
    )


def count_tasks_by_type(tx):
    """Count tasks grouped by task-type."""
    results = {}
    query = """
        match
            $t isa task, has task-type $tt;
        fetch {
            "task_type": $tt
        };
    """
    for row in tx.query().fetch(query):
        tt = row.get("task_type", {}).get("value", "unknown")
        results[tt] = results.get(tt, 0) + 1
    return results


def count_tasks_by_status(tx):
    """Count tasks grouped by task-status."""
    results = {}
    query = """
        match
            $t isa task, has task-status $ts;
        fetch {
            "task_status": $ts
        };
    """
    for row in tx.query().fetch(query):
        ts = row.get("task_status", {}).get("value", "unknown")
        results[ts] = results.get(ts, 0) + 1
    return results


def migrate_task_types(tx, dry_run=False):
    """Migrate deprecated task types to canonical types."""
    migrated = 0
    for old_type, new_type in TYPE_ALIASES.items():
        # Find tasks with old type
        query = f"""
            match
                $t isa task, has task-type "{old_type}";
            fetch {{
                "task_id": $t
            }};
        """
        count = sum(1 for _ in tx.query().fetch(query))
        if count > 0:
            print(f"  {old_type} → {new_type}: {count} tasks")
            if not dry_run:
                # Delete old attribute value and insert new one
                update_query = f"""
                    match
                        $t isa task, has task-type $old;
                        $old == "{old_type}";
                    delete
                        $t has $old;
                    insert
                        $t has task-type "{new_type}";
                """
                tx.query().update(update_query)
                migrated += count
    return migrated


def migrate_closed_status(tx, dry_run=False):
    """Migrate CLOSED status to DONE."""
    query = """
        match
            $t isa task, has task-status "CLOSED";
        fetch {
            "task_id": $t
        };
    """
    count = sum(1 for _ in tx.query().fetch(query))
    if count > 0:
        print(f"  CLOSED → DONE: {count} tasks")
        if not dry_run:
            update_query = """
                match
                    $t isa task, has task-status $old;
                    $old == "CLOSED";
                delete
                    $t has $old;
                insert
                    $t has task-status "DONE";
            """
            tx.query().update(update_query)
    return count


def main():
    parser = argparse.ArgumentParser(description="Migrate task taxonomy v2")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()

    print(f"=== EPIC-TASK-TAXONOMY-V2 Migration ===")
    print(f"Host: {TYPEDB_HOST}:{TYPEDB_PORT} | DB: {DATABASE}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    driver = get_driver()

    try:
        # Pre-migration counts
        print("--- Pre-Migration Counts ---")
        with driver.session(DATABASE) as session:
            with session.transaction(TransactionType.READ) as tx:
                type_counts = count_tasks_by_type(tx)
                status_counts = count_tasks_by_status(tx)
                print(f"  Types:    {type_counts}")
                print(f"  Statuses: {status_counts}")
                print()

        # Run migrations
        print("--- Migrating Task Types ---")
        with driver.session(DATABASE) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                type_migrated = migrate_task_types(tx, args.dry_run)
                if not args.dry_run and type_migrated > 0:
                    tx.commit()
                    print(f"  Committed {type_migrated} type changes")
                elif type_migrated == 0:
                    print("  No deprecated types found")

        print("--- Migrating CLOSED → DONE ---")
        with driver.session(DATABASE) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                status_migrated = migrate_closed_status(tx, args.dry_run)
                if not args.dry_run and status_migrated > 0:
                    tx.commit()
                    print(f"  Committed {status_migrated} status changes")
                elif status_migrated == 0:
                    print("  No CLOSED tasks found")

        # Post-migration counts
        if not args.dry_run:
            print()
            print("--- Post-Migration Counts ---")
            with driver.session(DATABASE) as session:
                with session.transaction(TransactionType.READ) as tx:
                    type_counts = count_tasks_by_type(tx)
                    status_counts = count_tasks_by_status(tx)
                    print(f"  Types:    {type_counts}")
                    print(f"  Statuses: {status_counts}")

        print()
        total = type_migrated + status_migrated
        if args.dry_run:
            print(f"DRY RUN complete: {total} tasks would be migrated")
        else:
            print(f"Migration complete: {total} tasks migrated")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
