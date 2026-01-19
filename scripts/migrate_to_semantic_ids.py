#!/usr/bin/env python3
"""
Migrate TypeDB rules to semantic IDs only.

Per GAP-RULE-QUALITY-001 Option C: Single ID system using semantic IDs.

This script:
1. For RULE-XXX with semantic_id → creates new rule with semantic_id as rule-id
2. For RULE-{semantic} → strips prefix, creates bare semantic ID rule
3. Deletes old legacy entries after migration

Usage:
    python3 scripts/migrate_to_semantic_ids.py [--dry-run]
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_all_rules(driver, database: str) -> list:
    """Get all rules with their attributes from TypeDB 3.x."""
    from typedb.driver import TransactionType

    rules = []
    with driver.transaction(database, TransactionType.READ) as tx:
        query = """
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status $status,
                has directive $dir;
            fetch
                $r: rule-id, rule-name, category, priority, status, directive,
                    semantic-id, rule-type;
        """
        # Use simpler query for TypeDB 3.x
        query = "match $r isa rule-entity, has rule-id $id;"
        result = tx.query(query).resolve()

        for row in result:
            id_attr = row.get("id")
            if id_attr:
                rule_id = id_attr.as_string() if hasattr(id_attr, 'as_string') else str(id_attr)
                rules.append(rule_id)

    return rules


def get_rule_details(driver, database: str, rule_id: str) -> dict:
    """Get full details for a single rule."""
    from typedb.driver import TransactionType

    with driver.transaction(database, TransactionType.READ) as tx:
        query = f'match $r isa rule-entity, has rule-id "{rule_id}";'
        result = tx.query(query).resolve()

        for row in result:
            rule = row.get("r")
            if rule:
                # Extract all attributes
                details = {"rule_id": rule_id}

                # Get attributes via get_has
                try:
                    attrs = list(rule.get_has(tx))
                    for attr in attrs:
                        attr_type = attr.get_type().get_label()
                        if hasattr(attr, 'as_string'):
                            details[attr_type] = attr.as_string()
                        elif hasattr(attr, 'as_boolean'):
                            details[attr_type] = attr.as_boolean()
                        else:
                            details[attr_type] = str(attr)
                except Exception as e:
                    print(f"  Warning: Could not get attributes for {rule_id}: {e}")

                return details
    return None


def determine_target_id(rule_id: str, semantic_id: str) -> str:
    """Determine what the new semantic-only ID should be."""
    # Already a bare semantic ID (no RULE- prefix)
    if not rule_id.startswith("RULE-"):
        return rule_id

    # Has RULE-XXX format with semantic_id attribute
    if semantic_id and rule_id.startswith("RULE-") and rule_id[5:].isdigit():
        return semantic_id

    # Has RULE-{semantic} format - strip prefix
    if rule_id.startswith("RULE-") and not rule_id[5:].isdigit():
        return rule_id[5:]  # Strip "RULE-" prefix

    # Fallback
    return semantic_id if semantic_id else rule_id


def insert_rule_with_id(driver, database: str, new_id: str, details: dict) -> bool:
    """Insert a rule with the new semantic ID."""
    from typedb.driver import TransactionType

    # Escape quotes
    def escape(s):
        return s.replace('"', '\\"') if s else ""

    parts = [
        f'has rule-id "{new_id}"',
    ]

    if details.get("rule-name"):
        parts.append(f'has rule-name "{escape(details["rule-name"])}"')
    if details.get("category"):
        parts.append(f'has category "{details["category"]}"')
    if details.get("priority"):
        parts.append(f'has priority "{details["priority"]}"')
    if details.get("status"):
        parts.append(f'has status "{details["status"]}"')
    if details.get("directive"):
        parts.append(f'has directive "{escape(details["directive"])}"')
    if details.get("rule-type"):
        parts.append(f'has rule-type "{details["rule-type"]}"')
    # Store original legacy ID for reference
    if details.get("rule-id") and details["rule-id"].startswith("RULE-"):
        parts.append(f'has semantic-id "{new_id}"')  # semantic-id = new ID

    insert_query = f"""
        insert $r isa rule-entity,
            {", ".join(parts)};
    """

    try:
        with driver.transaction(database, TransactionType.WRITE) as tx:
            tx.query(insert_query).resolve()
            tx.commit()
        return True
    except Exception as e:
        print(f"  Error inserting {new_id}: {e}")
        return False


def delete_rule(driver, database: str, rule_id: str) -> bool:
    """Delete a rule by ID."""
    from typedb.driver import TransactionType

    try:
        with driver.transaction(database, TransactionType.WRITE) as tx:
            query = f'match $r isa rule-entity, has rule-id "{rule_id}"; delete $r;'
            tx.query(query).resolve()
            tx.commit()
        return True
    except Exception as e:
        print(f"  Error deleting {rule_id}: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Migrate rules to semantic IDs")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    parser.add_argument("--host", default=os.getenv("TYPEDB_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("TYPEDB_PORT", "1729")))
    parser.add_argument("--database", default=os.getenv("TYPEDB_DATABASE", "sim-ai-governance"))
    args = parser.parse_args()

    print("=" * 60)
    print("Migrate Rules to Semantic IDs Only")
    print("=" * 60)

    # Connect to TypeDB
    try:
        from typedb.driver import TypeDB, Credentials, DriverOptions

        address = f"{args.host}:{args.port}"
        credentials = Credentials(
            os.getenv("TYPEDB_USERNAME", "admin"),
            os.getenv("TYPEDB_PASSWORD", "password")
        )
        options = DriverOptions(is_tls_enabled=False)

        print(f"\nConnecting to TypeDB at {address}...")
        driver = TypeDB.driver(address, credentials, options)
    except Exception as e:
        print(f"Error connecting: {e}")
        return 1

    # Get all rule IDs
    print("Fetching all rules...")
    rule_ids = get_all_rules(driver, args.database)
    print(f"  Found {len(rule_ids)} rules")

    # Analyze and plan migration
    migrations = []  # (old_id, new_id, details)
    already_semantic = []
    needs_migration = []

    for rule_id in rule_ids:
        details = get_rule_details(driver, args.database, rule_id)
        if not details:
            print(f"  Warning: Could not get details for {rule_id}")
            continue

        semantic_id = details.get("semantic-id")
        target_id = determine_target_id(rule_id, semantic_id)

        if target_id == rule_id:
            already_semantic.append(rule_id)
        else:
            needs_migration.append((rule_id, target_id, details))

    print(f"\n--- Migration Plan ---")
    print(f"Already semantic (no change): {len(already_semantic)}")
    print(f"Needs migration: {len(needs_migration)}")

    if needs_migration:
        print("\nMigrations planned:")
        for old_id, new_id, _ in sorted(needs_migration):
            print(f"  {old_id} → {new_id}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        driver.close()
        return 0

    # Execute migrations
    print("\n--- Executing Migration ---")
    migrated = 0
    failed = 0

    for old_id, new_id, details in needs_migration:
        # Check if target already exists
        if new_id in rule_ids:
            print(f"  SKIP {old_id} → {new_id} (target exists)")
            # Just delete the old one
            if delete_rule(driver, args.database, old_id):
                print(f"  DELETED {old_id} (duplicate)")
                migrated += 1
            continue

        # Insert new rule with semantic ID
        print(f"  INSERT {new_id}...")
        if insert_rule_with_id(driver, args.database, new_id, details):
            # Delete old rule
            if delete_rule(driver, args.database, old_id):
                print(f"  MIGRATED {old_id} → {new_id}")
                migrated += 1
            else:
                print(f"  WARNING: Inserted {new_id} but failed to delete {old_id}")
                failed += 1
        else:
            failed += 1

    driver.close()

    print("\n" + "=" * 60)
    print("Migration Complete")
    print(f"  Migrated: {migrated}")
    print(f"  Failed: {failed}")
    print(f"  Already semantic: {len(already_semantic)}")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
