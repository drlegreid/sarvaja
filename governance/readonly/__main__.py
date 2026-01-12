"""
Read-Only CLI Entry Point
Created: 2024-12-25 (P7.5)
Modularized: 2026-01-02 (RULE-032)

Usage:
    python -m governance.readonly query -c collection -q "search text"
    python -m governance.readonly list
    python -m governance.readonly status
"""
import argparse
import json

from governance.readonly import create_readonly_client


def main():
    """CLI for read-only wrapper."""
    parser = argparse.ArgumentParser(description="ChromaDB Read-Only Wrapper")
    parser.add_argument("command", choices=["query", "get", "list", "status"])
    parser.add_argument("--collection", "-c", help="Collection name")
    parser.add_argument("--query", "-q", help="Query text")
    parser.add_argument("--ids", nargs="+", help="Document IDs")
    args = parser.parse_args()

    client = create_readonly_client()

    if args.command == "query" and args.collection and args.query:
        result = client.query(args.collection, args.query)
        print(json.dumps(result, indent=2))

    elif args.command == "get" and args.collection and args.ids:
        result = client.get(args.collection, args.ids)
        print(json.dumps(result, indent=2))

    elif args.command == "list":
        result = client.list_collections()
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        result = client.get_deprecation_status()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
