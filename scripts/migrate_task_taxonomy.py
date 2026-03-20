#!/usr/bin/env python3
"""
Migrate TypeDB schema: Task taxonomy + workspace entities (EPIC-GOV-TASKS-V2).

Adds task-priority/task-type attributes and workspace entity with relations.
Idempotent — safe to re-run (skips already-applied changes).

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
    # ── Task taxonomy (BUG-TASK-TAXONOMY-001) ──
    ("Add task-priority attribute", "define attribute task-priority, value string;"),
    ("Add task-type attribute", "define attribute task-type, value string;"),
    ("task owns task-priority", "define task owns task-priority;"),
    ("task owns task-type", "define task owns task-type;"),
    # ── Project extended attributes (EPIC-GOV-TASKS-V2) ──
    ("Add project-type attribute", "define attribute project-type, value string;"),
    ("Add project-description attribute", "define attribute project-description, value string;"),
    ("Add project-created-at attribute", "define attribute project-created-at, value datetime;"),
    ("project owns project-type", "define project owns project-type;"),
    ("project owns project-description", "define project owns project-description;"),
    ("project owns project-created-at", "define project owns project-created-at;"),
    # ── Workspace entity + attributes (EPIC-GOV-TASKS-V2) ──
    ("Add workspace-id attribute", "define attribute workspace-id, value string;"),
    ("Add workspace-name attribute", "define attribute workspace-name, value string;"),
    ("Add workspace-type attribute", "define attribute workspace-type, value string;"),
    ("Add workspace-description attribute", "define attribute workspace-description, value string;"),
    ("Add workspace-status attribute", "define attribute workspace-status, value string;"),
    ("Add workspace-created-at attribute", "define attribute workspace-created-at, value datetime;"),
    ("Add workspace entity", (
        "define entity workspace,"
        " owns workspace-id,"
        " owns workspace-name,"
        " owns workspace-type,"
        " owns workspace-description,"
        " owns workspace-status,"
        " owns workspace-created-at;"
    )),
    # ── Workspace relations (EPIC-GOV-TASKS-V2) ──
    ("Add project-has-workspace relation", (
        "define relation project-has-workspace,"
        " relates owning-project,"
        " relates workspace-member;"
    )),
    ("project plays project-has-workspace", "define project plays project-has-workspace:owning-project;"),
    ("workspace plays project-has-workspace", "define workspace plays project-has-workspace:workspace-member;"),
    ("workspace plays workspace-has-agent", "define workspace plays workspace-has-agent:agent-workspace;"),
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
