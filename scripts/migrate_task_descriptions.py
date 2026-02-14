#!/usr/bin/env python3
"""One-time migration: move long task descriptions to body field.

Tasks with descriptions > 200 chars and empty body will have their
description moved to body and truncated.

Usage:
    python3 scripts/migrate_task_descriptions.py              # dry run
    python3 scripts/migrate_task_descriptions.py --apply      # apply changes
"""

import argparse
import sys

import httpx

API_BASE = "http://localhost:8082"


def main():
    parser = argparse.ArgumentParser(description="Migrate long task descriptions to body")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry run)")
    parser.add_argument("--api", default=API_BASE, help="API base URL")
    args = parser.parse_args()

    print(f"{'APPLY' if args.apply else 'DRY RUN'} mode | API: {args.api}")

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(f"{args.api}/api/tasks", params={"limit": 200, "offset": 0})
        if resp.status_code != 200:
            print(f"ERROR: Failed to fetch tasks: {resp.status_code}")
            sys.exit(1)

        data = resp.json()
        tasks = data.get("items", data) if isinstance(data, dict) else data

        affected = []
        for task in tasks:
            desc = task.get("description", "")
            body = task.get("body") or ""
            if len(desc) > 200 and not body.strip():
                affected.append(task)

        print(f"Found {len(affected)} tasks with description > 200 chars and no body\n")

        for task in affected:
            tid = task.get("task_id", task.get("id", "?"))
            desc = task["description"]
            print(f"  {tid}: {len(desc)} chars -> truncate to 200, move full text to body")

            if args.apply:
                update = {
                    "description": desc[:197] + "...",
                    "body": desc,
                }
                put_resp = client.put(f"{args.api}/api/tasks/{tid}", json=update)
                if put_resp.status_code == 200:
                    print(f"    UPDATED")
                else:
                    print(f"    FAILED: {put_resp.status_code}")

        if not args.apply and affected:
            print(f"\nRe-run with --apply to apply changes")


if __name__ == "__main__":
    main()
