"""Business event logging (L2) for governance state changes.

Emits structured JSON events for session, task, rule, and agent
lifecycle transitions. Consumed by the same logger hierarchy so
container logs capture both access (L1) and event (L2) streams.

Usage:
    from governance.middleware.event_log import log_event
    log_event("session", "create", session_id="SESSION-...", agent_id="code-agent")

Created: 2026-02-11
"""
import json
import logging
import time

logger = logging.getLogger("governance.events")


def log_event(entity: str, action: str, **details):
    """Emit a structured business event.

    Args:
        entity: Entity type (session, task, rule, agent).
        action: Lifecycle action (create, update, delete, start, end).
        **details: Arbitrary key-value pairs to include.
    """
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "entity": entity or "unknown",
        "action": action or "unknown",
        **details,
    }
    # BUG-MCP-002: Use default=str to prevent crash on non-serializable values
    try:
        logger.info(json.dumps(entry, separators=(",", ":"), default=str))
    except Exception:
        logger.warning(f"Failed to serialize event: entity={entity} action={action}")
