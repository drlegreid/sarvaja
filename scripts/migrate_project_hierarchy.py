#!/usr/bin/env python3
"""
Migrate TypeDB schema: Add project hierarchy (GOV-PROJECT-01-v1).

Adds project, plan, epic entities and their relations to TypeDB.
TypeDB 3.x syntax used throughout.

Usage: python3 scripts/migrate_project_hierarchy.py
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

# TypeDB 3.x syntax: "define entity NAME, ..." / "define attribute NAME, value TYPE;"
MIGRATIONS = [
    # Attributes
    ("Add project-id attr", "define attribute project-id, value string;"),
    ("Add project-name attr", "define attribute project-name, value string;"),
    ("Add project-path attr", "define attribute project-path, value string;"),
    ("Add plan-id attr", "define attribute plan-id, value string;"),
    ("Add plan-name attr", "define attribute plan-name, value string;"),
    ("Add epic-id attr", "define attribute epic-id, value string;"),
    ("Add epic-name attr", "define attribute epic-name, value string;"),
    # Relations (define before entities that play roles)
    ("Add project-contains-plan relation",
     "define relation project-contains-plan, relates parent-project, relates child-plan;"),
    ("Add plan-contains-epic relation",
     "define relation plan-contains-epic, relates parent-plan, relates child-epic;"),
    ("Add epic-contains-task relation",
     "define relation epic-contains-task, relates parent-epic, relates epic-task;"),
    ("Add project-has-session relation",
     "define relation project-has-session, relates session-project, relates project-session;"),
    # Entities
    ("Add project entity",
     "define entity project, owns project-id, owns project-name, owns project-path, "
     "plays project-contains-plan:parent-project, plays project-has-session:session-project;"),
    ("Add plan entity",
     "define entity plan, owns plan-id, owns plan-name, owns session-description, "
     "plays project-contains-plan:child-plan, plays plan-contains-epic:parent-plan;"),
    ("Add epic entity",
     "define entity epic, owns epic-id, owns epic-name, owns session-description, "
     "plays plan-contains-epic:child-epic, plays epic-contains-task:parent-epic;"),
    # Extend existing entities with new roles
    ("task plays epic-task",
     "define task plays epic-contains-task:epic-task;"),
    ("work-session plays project-session",
     "define work-session plays project-has-session:project-session;"),
]


def run_migration(driver, desc, query):
    """Execute a single migration step."""
    try:
        with driver.transaction(DATABASE, TransactionType.SCHEMA) as tx:
            tx.query(query).resolve()
            tx.commit()
        return "OK", None
    except Exception as e:
        err_str = str(e)
        if any(x in err_str for x in ["already exists", "already defined", "already owns", "already plays"]):
            return "SKIP", None
        return "FAIL", err_str[:120]


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
        status, err = run_migration(driver, desc, query)
        if status == "OK":
            print(f"  OK: {desc}")
            applied += 1
        elif status == "SKIP":
            print(f"  SKIP: {desc} (already exists)")
            skipped += 1
        else:
            print(f"  FAIL: {desc} — {err}")
            failed += 1

    print(f"\nMigration complete: {applied} applied, {skipped} skipped, {failed} failed")
    driver.close()


if __name__ == "__main__":
    main()
