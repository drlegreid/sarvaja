#!/usr/bin/env python3
"""
Migrate TypeDB schema: Add task classification attributes (BUG-TASK-TAXONOMY-001).

Adds task-priority and task-type attributes to task entity.

Usage: python3 scripts/migrate_task_taxonomy.py
"""
import os
import sys

try:
    from typedb.driver import TypeDB, Credentials, DriverOptions, TransactionType
except ImportError:
    print("ERROR: typedb-driver not installed")
    sys.exit(1)

TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE = "sim-ai-governance"

MIGRATIONS = [
    ("Add task-priority attribute", "define attribute task-priority, value string;"),
    ("Add task-type attribute", "define attribute task-type, value string;"),
    ("task owns task-priority", "define task owns task-priority;"),
    ("task owns task-type", "define task owns task-type;"),
]


def main():
    address = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
    print(f"Connecting to TypeDB at {address}...")

    username = os.getenv("TYPEDB_USERNAME", "admin")
    password = os.getenv("TYPEDB_PASSWORD", "password")
    credentials = Credentials(username, password)
    options = DriverOptions(is_tls_enabled=False)

    driver = TypeDB.driver(address, credentials, options)

    applied = 0
    skipped = 0
    failed = 0

    for desc, query in MIGRATIONS:
        try:
            with driver.transaction(DATABASE, TransactionType.SCHEMA) as tx:
                tx.query(query).resolve()
                tx.commit()
            print(f"  [OK] {desc}")
            applied += 1
        except Exception as e:
            err = str(e)
            if "already" in err.lower() or "exists" in err.lower():
                print(f"  [SKIP] {desc} (already exists)")
                skipped += 1
            else:
                print(f"  [FAIL] {desc}: {e}")
                failed += 1

    driver.close()
    print(f"\nDone: {applied} applied, {skipped} skipped, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
