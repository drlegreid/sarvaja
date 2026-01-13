#!/usr/bin/env python3
"""
Migrate TypeDB rules to include semantic-id attribute.

Per META-TAXON-01-v1: Rule Taxonomy & Management.
Per GAP-MCP-008: Semantic ID support.

This script:
1. Connects to TypeDB
2. Updates the schema to add semantic-id attribute (if not exists)
3. Adds semantic-id to all existing rules

Usage:
    python scripts/migrate_semantic_ids.py [--dry-run]

Created: 2026-01-13
"""

import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from governance.rule_linker import LEGACY_TO_SEMANTIC


def get_typedb_client():
    """Get TypeDB client."""
    from governance.client import TypeDBClient
    client = TypeDBClient()
    if not client.connect():
        print("ERROR: Failed to connect to TypeDB")
        sys.exit(1)
    return client


def check_schema_has_semantic_id(client) -> bool:
    """Check if semantic-id attribute exists in schema."""
    try:
        query = """
        match
            $a type semantic-id;
        get $a;
        """
        results = client.execute_query(query)
        return len(results) > 0
    except Exception:
        return False


def migrate_schema(client, dry_run: bool = False) -> bool:
    """Add semantic-id attribute to schema if not exists."""
    if check_schema_has_semantic_id(client):
        print("Schema already has semantic-id attribute")
        return True

    print("Adding semantic-id attribute to schema...")

    if dry_run:
        print("  [DRY RUN] Would add: semantic-id sub attribute, value string;")
        print("  [DRY RUN] Would add: rule-entity owns semantic-id;")
        return True

    # Schema updates need to be done via schema session
    # This is typically done by re-loading the schema file
    print("  NOTE: Schema update requires re-loading schema.tql")
    print("  Run: python -c \"from governance.client import TypeDBClient; c = TypeDBClient(); c.connect(); c.load_schema()\"")
    return False


def add_semantic_ids(client, dry_run: bool = False) -> dict:
    """Add semantic-id to all rules."""
    stats = {
        "total": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "missing_mapping": []
    }

    # Get all rules
    try:
        query = """
        match
            $r isa rule-entity, has rule-id $id;
        get $r, $id;
        """
        results = client.execute_query(query)
        stats["total"] = len(results)
        print(f"Found {stats['total']} rules in TypeDB")
    except Exception as e:
        print(f"ERROR: Failed to query rules: {e}")
        return stats

    for result in results:
        rule_id = result.get("id")
        if not rule_id:
            continue

        semantic_id = LEGACY_TO_SEMANTIC.get(rule_id)

        if not semantic_id:
            stats["missing_mapping"].append(rule_id)
            stats["skipped"] += 1
            continue

        # Check if rule already has semantic-id
        try:
            check_query = f"""
            match
                $r isa rule-entity, has rule-id "{rule_id}", has semantic-id $sid;
            get $sid;
            """
            existing = client.execute_query(check_query)
            if existing:
                print(f"  {rule_id} -> already has semantic-id")
                stats["skipped"] += 1
                continue
        except Exception:
            # semantic-id attribute might not exist yet
            pass

        if dry_run:
            print(f"  [DRY RUN] Would add: {rule_id} -> {semantic_id}")
            stats["updated"] += 1
            continue

        # Add semantic-id to rule
        try:
            update_query = f"""
            match
                $r isa rule-entity, has rule-id "{rule_id}";
            insert
                $r has semantic-id "{semantic_id}";
            """
            client.execute_query(update_query, write=True)
            print(f"  {rule_id} -> {semantic_id}")
            stats["updated"] += 1
        except Exception as e:
            print(f"  ERROR: {rule_id} -> {e}")
            stats["errors"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Migrate TypeDB rules to include semantic-id")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    print("=" * 60)
    print("TypeDB Semantic ID Migration")
    print("Per META-TAXON-01-v1: Rule Taxonomy & Management")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]\n")

    # Connect to TypeDB
    print("\n1. Connecting to TypeDB...")
    client = get_typedb_client()
    print("   Connected!")

    # Check/migrate schema
    print("\n2. Checking schema...")
    migrate_schema(client, args.dry_run)

    # Add semantic IDs
    print("\n3. Adding semantic IDs to rules...")
    stats = add_semantic_ids(client, args.dry_run)

    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"  Total rules:    {stats['total']}")
    print(f"  Updated:        {stats['updated']}")
    print(f"  Skipped:        {stats['skipped']}")
    print(f"  Errors:         {stats['errors']}")

    if stats["missing_mapping"]:
        print(f"\n  Rules without semantic ID mapping:")
        for rid in stats["missing_mapping"]:
            print(f"    - {rid}")

    # Cleanup
    client.close()

    if args.dry_run:
        print("\n[DRY RUN COMPLETE - Run without --dry-run to apply changes]")
    else:
        print("\n[MIGRATION COMPLETE]")


if __name__ == "__main__":
    main()
