#!/usr/bin/env python3
"""
Repair backfilled session data quality issues.

Per GAP-GOVSESS-TIMESTAMP-001: Fix identical artificial timestamps
Per GAP-GOVSESS-AGENT-001: Assign missing agent_ids
Per GAP-GOVSESS-DURATION-001: Cap unrealistic durations

Usage:
  python3 scripts/repair_backfill_sessions.py [--dry-run]

Created: 2026-02-11
"""

import sys
import logging
import httpx

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8082"


def main():
    dry_run = "--dry-run" in sys.argv

    # Import repair functions
    sys.path.insert(0, ".")
    from governance.services.session_repair import (
        build_repair_plan, is_backfilled_session,
    )

    logger.info("Fetching sessions from %s...", API_BASE)
    try:
        resp = httpx.get(f"{API_BASE}/api/sessions?limit=500", timeout=15.0)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Failed to fetch sessions: %s", e)
        sys.exit(1)

    data = resp.json()
    sessions = data.get("items", data) if isinstance(data, dict) else data

    # Build repair plan
    plan = build_repair_plan(sessions)
    logger.info(
        "Found %d sessions, %d need repair",
        len(sessions), len(plan)
    )

    if not plan:
        logger.info("No sessions need repair.")
        return

    repaired = 0
    failed = 0
    for item in plan:
        sid = item["session_id"]
        fixes = item["fixes"]
        fix_types = ", ".join(fixes.keys())
        logger.info(
            "  %s %s: %s",
            "DRY-RUN" if dry_run else "REPAIR", sid, fix_types
        )

        if not dry_run:
            try:
                update = {}
                if "agent_id" in fixes:
                    update["agent_id"] = fixes["agent_id"]
                if "timestamp" in fixes:
                    update["start_time"] = fixes["timestamp"]["start"]
                    update["end_time"] = fixes["timestamp"]["end"]
                if "duration" in fixes:
                    update["end_time"] = fixes["duration"]["end_time"]

                r = httpx.put(
                    f"{API_BASE}/api/sessions/{sid}",
                    json=update,
                    timeout=10.0,
                )
                if r.status_code == 200:
                    repaired += 1
                else:
                    logger.warning("    Failed: HTTP %d", r.status_code)
                    failed += 1
            except Exception as e:
                logger.warning("    Failed: %s", e)
                failed += 1

    if dry_run:
        logger.info("\nDry run complete. Would repair %d sessions.", len(plan))
    else:
        logger.info("\nRepaired %d sessions (%d failed).", repaired, failed)


if __name__ == "__main__":
    main()
