"""Dashboard action logging for trame UI interactions.

Logs user actions (page views, CRUD triggers, filter changes) as
structured JSON to the `governance.dashboard` logger. This complements
L1 access logs (HTTP-level) with L3 UI-level context.

Usage in controllers:
    from governance.middleware.dashboard_log import log_action
    log_action("sessions", "select", session_id="SESSION-...")

Created: 2026-02-11
"""
import json
import logging
import time

logger = logging.getLogger("governance.dashboard")


def log_action(view: str, action: str, **details):
    """Emit a structured dashboard action event.

    Args:
        view: Dashboard view name (sessions, tasks, rules, agents).
        action: User action (select, create, delete, filter, page).
        **details: Arbitrary key-value pairs to include.
    """
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "view": view,
        "action": action,
        **details,
    }
    # BUG-LOG-001: Use default=str to handle non-serializable values (UUID, datetime, etc.)
    logger.info(json.dumps(entry, separators=(",", ":"), default=str))
