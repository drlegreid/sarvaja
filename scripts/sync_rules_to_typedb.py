#!/usr/bin/env python3
"""
Sync Semantic Taxonomy Rules to TypeDB.

Per GAP-DATA-SYNC-001: TypeDB data vs semantic taxonomy sync.

Parses docs/rules/leaf/*.md files and inserts missing rules into TypeDB.

Usage:
    python scripts/sync_rules_to_typedb.py [--dry-run]
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_leaf_rule(file_path: Path) -> Optional[Dict]:
    """Parse a leaf rule markdown file and extract metadata."""
    content = file_path.read_text()

    # Extract semantic ID from filename
    semantic_id = file_path.stem  # e.g., "SESSION-EVID-01-v1"

    # Extract metadata from frontmatter-style headers
    rule = {
        "semantic_id": semantic_id,
        "legacy_id": None,
        "name": None,
        "category": None,
        "priority": None,
        "status": "ACTIVE",
        "directive": None,
        "rule_type": None,
    }

    # Parse title: # SEMANTIC-ID: Name
    title_match = re.search(r'^#\s+[\w-]+:\s+(.+)$', content, re.MULTILINE)
    if title_match:
        rule["name"] = title_match.group(1).strip()

    # Parse category from **Category:** `xxx`
    cat_match = re.search(r'\*\*Category:\*\*\s*`(\w+)`', content)
    if cat_match:
        rule["category"] = cat_match.group(1)

    # Parse priority from **Priority:** xxx
    pri_match = re.search(r'\*\*Priority:\*\*\s*(\w+)', content)
    if pri_match:
        rule["priority"] = pri_match.group(1).upper()

    # Parse status from **Status:** xxx
    status_match = re.search(r'\*\*Status:\*\*\s*(\w+)', content)
    if status_match:
        rule["status"] = status_match.group(1).upper()

    # Parse type from **Type:** xxx
    type_match = re.search(r'\*\*Type:\*\*\s*(\w+)', content)
    if type_match:
        rule["rule_type"] = type_match.group(1).upper()

    # Parse legacy ID from > **Legacy ID:** RULE-xxx
    legacy_match = re.search(r'\*\*Legacy ID:\*\*\s*(RULE-\d+)', content)
    if legacy_match:
        rule["legacy_id"] = legacy_match.group(1)

    # Parse directive from ## Directive section
    directive_match = re.search(r'## Directive\s*\n+(.+?)(?=\n#|\n---|\Z)', content, re.DOTALL)
    if directive_match:
        directive = directive_match.group(1).strip()
        # Clean up markdown, take first paragraph
        directive = re.sub(r'\n+', ' ', directive)
        directive = re.sub(r'\s+', ' ', directive)
        # Truncate if too long
        if len(directive) > 500:
            directive = directive[:497] + "..."
        rule["directive"] = directive

    # Validate required fields
    if not rule["name"] or not rule["category"] or not rule["priority"]:
        print(f"  Warning: Missing required fields in {file_path.name}")
        return None

    # Use semantic ID as rule_id when no legacy ID exists
    # Per GAP-RULE-QUALITY-001: Don't prefix RULE- to avoid duplicates
    if not rule["legacy_id"]:
        rule["legacy_id"] = semantic_id  # Use bare semantic ID

    return rule


def get_existing_rules(driver, database: str) -> set:
    """Get set of existing rule IDs from TypeDB 3.x."""
    from typedb.driver import TransactionType

    existing = set()

    with driver.transaction(database, TransactionType.READ) as tx:
        query = "match $r isa rule-entity, has rule-id $id;"
        result = tx.query(query).resolve()

        # TypeDB 3.x: iterate over result rows
        for row in result:
            # Get the rule-id attribute value
            id_attr = row.get("id")
            if id_attr:
                # TypeDB 3.x: use as_string() for string attributes
                if hasattr(id_attr, 'as_string'):
                    existing.add(id_attr.as_string())
                elif hasattr(id_attr, 'value'):
                    existing.add(id_attr.value)
                elif hasattr(id_attr, 'get_value'):
                    existing.add(id_attr.get_value())

    return existing


def insert_rule(driver, database: str, rule: Dict) -> bool:
    """Insert a rule into TypeDB."""
    from typedb.driver import TransactionType

    # Escape quotes in directive
    directive = rule["directive"].replace('"', '\\"') if rule["directive"] else ""
    name = rule["name"].replace('"', '\\"') if rule["name"] else ""

    # Build insert query
    parts = [
        f'has rule-id "{rule["legacy_id"]}"',
        f'has rule-name "{name}"',
        f'has category "{rule["category"]}"',
        f'has priority "{rule["priority"]}"',
        f'has status "{rule["status"]}"',
        f'has directive "{directive}"',
    ]

    if rule["semantic_id"]:
        parts.append(f'has semantic-id "{rule["semantic_id"]}"')

    if rule["rule_type"]:
        parts.append(f'has rule-type "{rule["rule_type"]}"')

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
        print(f"  Error inserting {rule['legacy_id']}: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sync rules from docs to TypeDB")
    parser.add_argument("--dry-run", action="store_true", help="Print queries without executing")
    parser.add_argument("--host", default=os.getenv("TYPEDB_HOST", "localhost"), help="TypeDB host")
    parser.add_argument("--port", type=int, default=int(os.getenv("TYPEDB_PORT", "1729")), help="TypeDB port")
    parser.add_argument("--database", default=os.getenv("TYPEDB_DATABASE", "sim-ai-governance"), help="Database name")
    args = parser.parse_args()

    print("=" * 60)
    print("Sync Semantic Rules to TypeDB")
    print("=" * 60)

    # Find leaf rule files
    leaf_dir = PROJECT_ROOT / "docs" / "rules" / "leaf"
    if not leaf_dir.exists():
        print(f"Error: Leaf directory not found: {leaf_dir}")
        return 1

    rule_files = sorted(leaf_dir.glob("*.md"))
    print(f"Found {len(rule_files)} rule files in {leaf_dir}")

    # Parse all rules
    rules = []
    for file_path in rule_files:
        rule = parse_leaf_rule(file_path)
        if rule:
            rules.append(rule)

    print(f"Parsed {len(rules)} valid rules")

    if args.dry_run:
        print("\n[DRY RUN] Would insert these rules:")
        for rule in rules:
            print(f"  {rule['legacy_id']} ({rule['semantic_id']}): {rule['name']}")
        return 0

    # Connect to TypeDB
    try:
        from typedb.driver import TypeDB, Credentials, DriverOptions

        address = f"{args.host}:{args.port}"
        username = os.getenv("TYPEDB_USERNAME", "admin")
        password = os.getenv("TYPEDB_PASSWORD", "password")

        credentials = Credentials(username, password)
        options = DriverOptions(is_tls_enabled=False)

        print(f"\nConnecting to TypeDB at {address}...")
        driver = TypeDB.driver(address, credentials, options)
    except ImportError:
        print("Error: typedb-driver not installed")
        return 1
    except Exception as e:
        print(f"Error connecting to TypeDB: {e}")
        return 1

    # Get existing rules
    print("Fetching existing rules...")
    existing = get_existing_rules(driver, args.database)
    print(f"  Found {len(existing)} existing rules in TypeDB")

    # Insert missing rules
    inserted = 0
    skipped = 0
    failed = 0

    print("\nInserting missing rules...")
    for rule in rules:
        rule_id = rule["legacy_id"]

        if rule_id in existing:
            skipped += 1
            continue

        print(f"  Inserting: {rule_id} ({rule['semantic_id']})")
        if insert_rule(driver, args.database, rule):
            inserted += 1
        else:
            failed += 1

    driver.close()

    print("\n" + "=" * 60)
    print("Sync Complete")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped (exists): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Total rules in TypeDB: {len(existing) + inserted}")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
