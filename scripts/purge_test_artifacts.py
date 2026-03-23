#!/usr/bin/env python3
"""Purge test artifacts from TypeDB via API.

SRVJ-CHORE-002: One-time cleanup of E2E-*, RF-*, INTTEST-*, CRUD-* tasks.
Can also be used as pre-CI hook.

Usage:
    python3 scripts/purge_test_artifacts.py             # Dry run (default)
    python3 scripts/purge_test_artifacts.py --execute    # Actually delete
    python3 scripts/purge_test_artifacts.py --prefix E2E-QUAL-  # Custom prefix
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.shared.task_test_factory import purge_test_artifacts, ALL_TEST_PREFIXES


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Purge test artifacts from TypeDB")
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually delete (default is dry run)",
    )
    parser.add_argument(
        "--prefix", action="append", default=None,
        help="Custom prefix to match (can repeat). Default: all test prefixes",
    )
    parser.add_argument(
        "--api-url", default="http://localhost:8082/api",
        help="API base URL (default: http://localhost:8082/api)",
    )
    args = parser.parse_args()

    prefixes = args.prefix or ALL_TEST_PREFIXES

    if not args.execute:
        print("DRY RUN — use --execute to actually delete")
        print(f"Would purge tasks matching: {prefixes}")
        # Still scan to show what would be deleted
        import httpx
        with httpx.Client(base_url=args.api_url, timeout=10.0) as client:
            r = client.get("/tasks", params={"limit": 200})
            if r.status_code != 200:
                print(f"API error: {r.status_code}")
                sys.exit(1)
            items = r.json().get("items", [])
            matches = [
                i["task_id"] for i in items
                if any(i.get("task_id", "").startswith(p) for p in prefixes)
            ]
            print(f"Found {len(matches)} matching tasks:")
            for tid in matches[:20]:
                print(f"  {tid}")
            if len(matches) > 20:
                print(f"  ... and {len(matches) - 20} more")
        sys.exit(0)

    print(f"Purging tasks matching: {prefixes}")
    result = purge_test_artifacts(base_url=args.api_url, prefixes=prefixes)
    print(f"Checked: {result['checked']}")
    print(f"Deleted: {result['deleted']}")
    print(f"Failed:  {result['failed']}")
    if result["errors"]:
        print("Errors:")
        for err in result["errors"][:10]:
            print(f"  - {err}")
    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
