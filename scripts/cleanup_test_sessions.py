#!/usr/bin/env python3
"""
Cleanup stale test sessions from TypeDB.

Per EPIC-E.3: One-time purge of test-created sessions that pollute
heuristic checks (H-SESSION-005/006).

Patterns cleaned:
  - Sessions with agent_id = "agent-1" (unit test placeholder)
  - Sessions with CHAT- prefix and test indicator patterns
  - Sessions with description containing "test" + CHAT prefix

Usage:
  python3 scripts/cleanup_test_sessions.py [--dry-run]

Created: 2026-02-11
"""

import sys
import logging
import httpx

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8082"

# Patterns that indicate test-artifact sessions
_TEST_PATTERNS = (
    "CHAT-TEST", "CHAT-NO-TOOLS", "CHAT-NO-THOUGHTS",
    "CHAT-CVP", "CHAT-FALLBACK", "CHAT-ORPHAN",
    "CHAT-STORE-", "CHAT-TYPEDB-", "CHAT-RESILIENT",
    "CHAT-DONE", "CHAT-AAA", "CHAT-BBB", "CHAT-CCC",
    "CHAT-HEURISTIC", "CHAT-FULL-LIFECYCLE", "CHAT-REVIEWING",
    "CHAT-HELLO", "CHAT-LINKING", "CHAT-VERIFY",
    "CHAT-TESTING", "CHAT-SUMMARY", "CHAT--STATUS",
    "CHAT-COMPLETE-SESSION", "CHAT-DELETE",
)


def _is_test_session(session: dict) -> bool:
    """Check if session is a test artifact."""
    agent = session.get("agent_id") or ""
    sid = session.get("session_id") or ""
    desc = (session.get("description") or "").lower()

    if agent == "agent-1":
        return True

    if "CHAT-" in sid:
        for pattern in _TEST_PATTERNS:
            if pattern in sid:
                return True
        if "test" in desc:
            return True

    return False


def main():
    dry_run = "--dry-run" in sys.argv

    logger.info("Fetching sessions from %s...", API_BASE)
    try:
        resp = httpx.get(f"{API_BASE}/api/sessions?limit=200", timeout=15.0)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Failed to fetch sessions: %s", e)
        sys.exit(1)

    data = resp.json()
    sessions = data.get("items", data) if isinstance(data, dict) else data

    test_sessions = [s for s in sessions if _is_test_session(s)]
    logger.info("Found %d total sessions, %d are test artifacts",
                len(sessions), len(test_sessions))

    if not test_sessions:
        logger.info("No test sessions to clean up.")
        return

    deleted = 0
    failed = 0
    for s in test_sessions:
        sid = s.get("session_id", "?")
        agent = s.get("agent_id", "?")
        status = s.get("status", "?")
        logger.info("  %s [%s] agent=%s %s",
                     "DRY-RUN" if dry_run else "DELETE",
                     status, agent, sid)

        if not dry_run:
            try:
                r = httpx.delete(f"{API_BASE}/api/sessions/{sid}", timeout=10.0)
                if r.status_code in (200, 204):
                    deleted += 1
                else:
                    logger.warning("    Failed: HTTP %d", r.status_code)
                    failed += 1
            except Exception as e:
                logger.warning("    Failed: %s", e)
                failed += 1

    if dry_run:
        logger.info("\nDry run complete. Would delete %d sessions.", len(test_sessions))
    else:
        logger.info("\nDeleted %d sessions (%d failed).", deleted, failed)


if __name__ == "__main__":
    main()
