#!/usr/bin/env python3
"""
Backfill Traceability Data.

Per PLAN-UI-OVERHAUL-001 Task 2.5: Backfill task<>rule<>session mappings.
Uses REST API to link tasks to sessions and rules based on existing data.

Usage:
    .venv/bin/python3 scripts/backfill_traceability.py [--dry-run]
"""

import argparse
import logging
import sys

import httpx

API_BASE = "http://localhost:8082"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_all_tasks(client: httpx.Client) -> list:
    """Fetch all tasks from API."""
    tasks = []
    offset = 0
    while True:
        resp = client.get(f"{API_BASE}/api/tasks", params={"limit": 100, "offset": offset})
        if resp.status_code != 200:
            logger.error(f"Failed to fetch tasks: {resp.status_code}")
            break
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        tasks.extend(items)
        pagination = data.get("pagination", {})
        if not pagination.get("has_more"):
            break
        offset += 100
    return tasks


def get_all_sessions(client: httpx.Client) -> list:
    """Fetch all sessions from API."""
    sessions = []
    offset = 0
    while True:
        resp = client.get(f"{API_BASE}/api/sessions", params={"limit": 100, "offset": offset})
        if resp.status_code != 200:
            logger.error(f"Failed to fetch sessions: {resp.status_code}")
            break
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        sessions.extend(items)
        pagination = data.get("pagination", {})
        if not pagination.get("has_more"):
            break
        offset += 100
    return sessions


def link_task_to_session(client: httpx.Client, task_id: str, session_id: str,
                         dry_run: bool = False) -> bool:
    """Link a task to a session via API."""
    if dry_run:
        logger.info(f"  [DRY-RUN] Would link task {task_id} -> session {session_id}")
        return True
    try:
        resp = client.post(
            f"{API_BASE}/api/tasks/{task_id}/link-session",
            json={"session_id": session_id}
        )
        if resp.status_code in (200, 201):
            return True
        logger.warning(f"  Link task->session failed: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        logger.warning(f"  Link task->session error: {e}")
    return False


def link_task_to_rule(client: httpx.Client, task_id: str, rule_id: str,
                      dry_run: bool = False) -> bool:
    """Link a task to a rule via API."""
    if dry_run:
        logger.info(f"  [DRY-RUN] Would link task {task_id} -> rule {rule_id}")
        return True
    try:
        resp = client.post(
            f"{API_BASE}/api/tasks/{task_id}/link-rule",
            json={"rule_id": rule_id}
        )
        if resp.status_code in (200, 201):
            return True
        logger.warning(f"  Link task->rule failed: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        logger.warning(f"  Link task->rule error: {e}")
    return False


def backfill_task_session_links(client: httpx.Client, tasks: list,
                                sessions: list, dry_run: bool) -> dict:
    """Backfill task-to-session links from linked_sessions field."""
    stats = {"checked": 0, "linked": 0, "skipped": 0, "failed": 0}
    session_ids = {s.get("session_id", s.get("id")) for s in sessions}

    for task in tasks:
        task_id = task.get("task_id", task.get("id"))
        linked = task.get("linked_sessions", [])
        if not linked:
            stats["skipped"] += 1
            continue

        for session_id in linked:
            stats["checked"] += 1
            if session_id not in session_ids:
                stats["skipped"] += 1
                continue
            if link_task_to_session(client, task_id, session_id, dry_run):
                stats["linked"] += 1
            else:
                stats["failed"] += 1

    return stats


def backfill_task_rule_links(client: httpx.Client, tasks: list,
                             dry_run: bool) -> dict:
    """Backfill task-to-rule links from linked_rules field."""
    stats = {"checked": 0, "linked": 0, "skipped": 0, "failed": 0}

    for task in tasks:
        task_id = task.get("task_id", task.get("id"))
        linked = task.get("linked_rules", [])
        if not linked:
            stats["skipped"] += 1
            continue

        for rule_id in linked:
            stats["checked"] += 1
            if link_task_to_rule(client, task_id, rule_id, dry_run):
                stats["linked"] += 1
            else:
                stats["failed"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Backfill traceability data")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making changes")
    args = parser.parse_args()

    logger.info("=== Backfill Traceability Data ===")
    if args.dry_run:
        logger.info("DRY RUN MODE - no changes will be made")

    with httpx.Client(timeout=30.0) as client:
        # Check API is reachable
        try:
            resp = client.get(f"{API_BASE}/health")
            if resp.status_code != 200:
                logger.error(f"API not healthy: {resp.status_code}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Cannot reach API at {API_BASE}: {e}")
            sys.exit(1)

        # Fetch all data
        logger.info("Fetching tasks...")
        tasks = get_all_tasks(client)
        logger.info(f"  Found {len(tasks)} tasks")

        logger.info("Fetching sessions...")
        sessions = get_all_sessions(client)
        logger.info(f"  Found {len(sessions)} sessions")

        # Backfill task->session links
        logger.info("\n--- Backfilling task-session links ---")
        ts_stats = backfill_task_session_links(client, tasks, sessions, args.dry_run)
        logger.info(f"  Checked: {ts_stats['checked']}, "
                     f"Linked: {ts_stats['linked']}, "
                     f"Skipped: {ts_stats['skipped']}, "
                     f"Failed: {ts_stats['failed']}")

        # Backfill task->rule links
        logger.info("\n--- Backfilling task-rule links ---")
        tr_stats = backfill_task_rule_links(client, tasks, args.dry_run)
        logger.info(f"  Checked: {tr_stats['checked']}, "
                     f"Linked: {tr_stats['linked']}, "
                     f"Skipped: {tr_stats['skipped']}, "
                     f"Failed: {tr_stats['failed']}")

        logger.info("\n=== Backfill Complete ===")
        total_linked = ts_stats["linked"] + tr_stats["linked"]
        logger.info(f"Total new links created: {total_linked}")


if __name__ == "__main__":
    main()
