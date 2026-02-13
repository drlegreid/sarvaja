#!/usr/bin/env python3
"""
Migrate TypeDB schema: Add CC session attributes (SESSION-CC-01-v1).

Adds cc-session-uuid, cc-project-slug, cc-git-branch, cc-tool-count,
cc-thinking-chars, cc-compaction-count to work-session entity.

Usage: python3 scripts/migrate_cc_attributes.py
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

# Each migration step: (description, TypeQL define statement)
# TypeDB 3.x syntax: "define attribute NAME, value TYPE;" (not "NAME sub attribute")
MIGRATIONS = [
    ("Add cc-session-uuid attribute", "define attribute cc-session-uuid, value string;"),
    ("Add cc-project-slug attribute", "define attribute cc-project-slug, value string;"),
    ("Add cc-git-branch attribute", "define attribute cc-git-branch, value string;"),
    ("Add cc-tool-count attribute", "define attribute cc-tool-count, value integer;"),
    ("Add cc-thinking-chars attribute", "define attribute cc-thinking-chars, value integer;"),
    ("Add cc-compaction-count attribute", "define attribute cc-compaction-count, value integer;"),
    ("work-session owns cc-session-uuid", "define work-session owns cc-session-uuid;"),
    ("work-session owns cc-project-slug", "define work-session owns cc-project-slug;"),
    ("work-session owns cc-git-branch", "define work-session owns cc-git-branch;"),
    ("work-session owns cc-tool-count", "define work-session owns cc-tool-count;"),
    ("work-session owns cc-thinking-chars", "define work-session owns cc-thinking-chars;"),
    ("work-session owns cc-compaction-count", "define work-session owns cc-compaction-count;"),
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
            print(f"  OK: {desc}")
            applied += 1
        except Exception as e:
            err_str = str(e)
            if "already exists" in err_str or "already defined" in err_str or "already owns" in err_str:
                print(f"  SKIP: {desc} (already exists)")
                skipped += 1
            else:
                print(f"  FAIL: {desc} — {err_str[:120]}")
                failed += 1

    print(f"\nMigration complete: {applied} applied, {skipped} skipped, {failed} failed")
    driver.close()


if __name__ == "__main__":
    main()
