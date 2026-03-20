#!/usr/bin/env python3
"""
Migrate TypeDB schema: Add workspace entity + relations (EPIC-GOV-TASKS-V2 Phase 3/4).

Adds workspace entity, attributes, and workspace-has-task/workspace-has-agent relations.
Also extends task/agent/project entities with required plays roles.

Usage: python3 scripts/migrate_workspace_schema.py
       # Or inside container:
       podman exec platform_governance-dashboard-dev_1 python3 /app/scripts/migrate_workspace_schema.py
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
# Order matters: attributes first, then entities, then relations, then plays roles
MIGRATIONS = [
    # 1. Workspace attributes
    ("Add workspace-id attribute", "define attribute workspace-id, value string;"),
    ("Add workspace-name attribute", "define attribute workspace-name, value string;"),
    ("Add workspace-type attribute", "define attribute workspace-type, value string;"),
    ("Add workspace-description attribute", "define attribute workspace-description, value string;"),
    ("Add workspace-status attribute", "define attribute workspace-status, value string;"),
    ("Add workspace-created-at attribute", "define attribute workspace-created-at, value datetime;"),

    # 2. Relations (must be defined before entity plays roles)
    ("Add project-has-workspace relation",
     "define relation project-has-workspace, relates owning-project, relates workspace-member;"),
    ("Add workspace-has-agent relation",
     "define relation workspace-has-agent, relates agent-workspace, relates assigned-agent;"),
    ("Add workspace-has-task relation",
     "define relation workspace-has-task, relates task-workspace, relates assigned-task;"),

    # 3. Workspace entity with owns + plays
    ("Add workspace entity",
     """define entity workspace,
        owns workspace-id,
        owns workspace-name,
        owns workspace-type,
        owns workspace-description,
        owns workspace-status,
        owns workspace-created-at,
        plays project-has-workspace:workspace-member,
        plays workspace-has-agent:agent-workspace,
        plays workspace-has-task:task-workspace;"""),

    # 4. Extend existing entities with new plays roles
    ("task plays workspace-has-task:assigned-task",
     "define task plays workspace-has-task:assigned-task;"),
    ("agent plays workspace-has-agent:assigned-agent",
     "define agent plays workspace-has-agent:assigned-agent;"),
    ("project plays project-has-workspace:owning-project",
     "define project plays project-has-workspace:owning-project;"),
]


def main():
    address = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
    print(f"Connecting to TypeDB at {address}...")

    username = os.getenv("TYPEDB_USERNAME", "admin")
    password = os.getenv("TYPEDB_PASSWORD", "password")
    credentials = Credentials(username, password)
    options = DriverOptions(is_tls_enabled=False)

    driver = TypeDB.driver(address, credentials, options)

    if not driver.databases.contains(DATABASE):
        print(f"ERROR: Database '{DATABASE}' not found")
        driver.close()
        sys.exit(1)

    print(f"Running {len(MIGRATIONS)} migration steps on '{DATABASE}'...")

    success = 0
    skipped = 0
    failed = 0

    for desc, query in MIGRATIONS:
        try:
            with driver.transaction(DATABASE, TransactionType.SCHEMA) as tx:
                tx.query(query).resolve()
                tx.commit()
            print(f"  ✓ {desc}")
            success += 1
        except Exception as e:
            err_str = str(e)
            if "already" in err_str.lower() or "exists" in err_str.lower():
                print(f"  ○ {desc} (already exists)")
                skipped += 1
            else:
                print(f"  ✗ {desc}: {err_str[:200]}")
                failed += 1

    driver.close()
    print(f"\nDone: {success} applied, {skipped} skipped, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
