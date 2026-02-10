#!/usr/bin/env python3
"""
Cleanup TEST-* entities from TypeDB.

Removes residual test data (TEST-* rules, TEST-SESSION-* sessions, TEST-* tasks)
left behind by interrupted E2E or Robot Framework test runs.

Usage:
    .venv/bin/python3 scripts/cleanup_test_data.py
    .venv/bin/python3 scripts/cleanup_test_data.py --dry-run
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

import httpx

API_URL = "http://localhost:8082"
PROJECT_ROOT = Path(__file__).parent.parent


def cleanup_evidence_archives(dry_run: bool = False, max_age_days: int = 7) -> int:
    """Remove TEST-* evidence archive files older than max_age_days."""
    archive_dir = PROJECT_ROOT / "evidence" / "archive" / "rules"
    if not archive_dir.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=max_age_days)
    cleaned = 0
    for f in archive_dir.glob("TEST-*.json"):
        if f.stat().st_mtime < cutoff.timestamp():
            if dry_run:
                print(f"  [DRY] Would delete archive {f.name}")
            else:
                f.unlink()
            cleaned += 1
    print(f"Found {cleaned} TEST-* archive files older than {max_age_days} days")
    return cleaned


def cleanup(dry_run: bool = False) -> dict:
    """Remove all TEST-* entities from the system."""
    cleaned = {"tasks": 0, "rules": 0, "sessions": 0, "archives": 0}

    # Clean evidence archives first (no API needed)
    cleaned["archives"] = cleanup_evidence_archives(dry_run)

    with httpx.Client(base_url=API_URL, timeout=30.0) as client:
        # Check API is up
        try:
            resp = client.get("/api/health")
            if resp.status_code != 200:
                print(f"API not healthy: {resp.status_code}")
                return cleaned
            health = resp.json()
            typedb_ok = health.get("typedb_connected", False)
            print(f"API healthy, TypeDB: {'connected' if typedb_ok else 'disconnected'}")
        except Exception as e:
            print(f"Cannot reach API at {API_URL}: {e}")
            return cleaned

        # Tasks
        try:
            resp = client.get("/api/tasks?limit=1000")
            if resp.status_code == 200:
                data = resp.json()
                tasks = data.get("items", data) if isinstance(data, dict) else data
                test_tasks = [t for t in tasks if t.get("task_id", "").startswith("TEST-")]
                print(f"Found {len(test_tasks)} TEST-* tasks")
                for task in test_tasks:
                    tid = task["task_id"]
                    if dry_run:
                        print(f"  [DRY] Would delete task {tid}")
                    else:
                        if client.delete(f"/api/tasks/{tid}").status_code == 204:
                            cleaned["tasks"] += 1
        except Exception as e:
            print(f"Task cleanup error: {e}")

        # Sessions (TEST-* prefixed)
        try:
            resp = client.get("/api/sessions?limit=200")
            if resp.status_code == 200:
                data = resp.json()
                sessions = data.get("items", data) if isinstance(data, dict) else data
                test_sessions = [s for s in sessions
                                 if s.get("session_id", "").startswith(("TEST-SESSION-", "TEST-"))]
                print(f"Found {len(test_sessions)} TEST-* sessions")
                for s in test_sessions:
                    sid = s["session_id"]
                    if dry_run:
                        print(f"  [DRY] Would cleanup session {sid}")
                    else:
                        if s.get("status") == "ACTIVE":
                            client.put(f"/api/sessions/{sid}/end")
                        client.delete(f"/api/sessions/{sid}")
                        cleaned["sessions"] += 1
        except Exception as e:
            print(f"Session cleanup error: {e}")

        # CHAT test-artifact sessions (E.3: test data pollution fix)
        _CHAT_TEST_PATTERNS = (
            "CHAT-TEST", "CHAT-NO-TOOLS", "CHAT-NO-THOUGHTS",
            "CHAT-CVP", "CHAT-FALLBACK", "CHAT-ORPHAN",
            "CHAT-STORE-", "CHAT-TYPEDB-", "CHAT-RESILIENT",
            "CHAT-DONE", "CHAT-AAA", "CHAT-BBB", "CHAT-CCC",
        )
        try:
            resp = client.get("/api/sessions?limit=500")
            if resp.status_code == 200:
                data = resp.json()
                sessions = data.get("items", data) if isinstance(data, dict) else data
                chat_test = []
                for s in sessions:
                    sid = s.get("session_id", "")
                    agent = s.get("agent_id", "")
                    if "CHAT-" not in sid:
                        continue
                    if agent == "agent-1" or any(p in sid for p in _CHAT_TEST_PATTERNS):
                        chat_test.append(s)
                print(f"Found {len(chat_test)} CHAT test-artifact sessions")
                for s in chat_test:
                    sid = s["session_id"]
                    if dry_run:
                        print(f"  [DRY] Would cleanup CHAT test session {sid}")
                    else:
                        if s.get("status") == "ACTIVE":
                            client.put(f"/api/sessions/{sid}/end")
                        client.delete(f"/api/sessions/{sid}")
                        cleaned["sessions"] += 1
        except Exception as e:
            print(f"CHAT test session cleanup error: {e}")

        # Rules (requires TypeDB)
        if typedb_ok:
            try:
                resp = client.get("/api/rules")
                if resp.status_code == 200:
                    data = resp.json()
                    rules = data.get("items", data) if isinstance(data, dict) else data
                    test_rules = [r for r in rules if r.get("id", "").startswith("TEST-")]
                    print(f"Found {len(test_rules)} TEST-* rules")
                    for rule in test_rules:
                        rid = rule["id"]
                        if dry_run:
                            print(f"  [DRY] Would delete rule {rid}")
                        else:
                            if client.delete(f"/api/rules/{rid}", params={"archive": "false"}).status_code == 204:
                                cleaned["rules"] += 1
            except Exception as e:
                print(f"Rule cleanup error: {e}")

    return cleaned


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup TEST-* entities from TypeDB")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    args = parser.parse_args()

    result = cleanup(dry_run=args.dry_run)
    total = sum(result.values())

    if args.dry_run:
        print(f"\n[DRY RUN] Would clean: {result}")
    else:
        print(f"\nCleaned: {result} (total: {total})")

    sys.exit(0 if total >= 0 else 1)
