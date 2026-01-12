"""
Migration CLI Entry Point
Created: 2024-12-25 (P7.4)
Modularized: 2026-01-02 (RULE-032)

Usage:
    python -m governance.migration scan
    python -m governance.migration migrate --dry-run
    python -m governance.migration migrate --execute
"""
import argparse
import json

from governance.migration import create_chroma_migration


def main():
    """CLI for ChromaDB migration."""
    parser = argparse.ArgumentParser(description="ChromaDB Migration Tool")
    parser.add_argument("command", choices=["scan", "migrate", "status"])
    parser.add_argument("--collection", "-c", help="Specific collection to migrate")
    parser.add_argument("--dry-run", "-n", action="store_true", default=True)
    parser.add_argument("--execute", "-x", action="store_true", help="Actually execute migration")
    args = parser.parse_args()

    dry_run = not args.execute
    migrator = create_chroma_migration(dry_run=dry_run)

    if args.command == "scan":
        result = migrator.scan_chroma()
        print(json.dumps(result, indent=2))

    elif args.command == "migrate":
        if args.collection:
            result = migrator.migrate_collection(args.collection)
        else:
            result = migrator.migrate_all()
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        result = migrator.get_migration_status()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
