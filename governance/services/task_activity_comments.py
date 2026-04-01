"""Auto-generated activity comments from audit events.

Per SRVJ-FEAT-AUDIT-TRAIL-01 P7: Human-readable system comments
auto-generated when task mutations occur (status change, link, evidence, etc.).

SRP: This module owns the text generation + orchestration.
  - format_activity_text() — pure function, audit event -> comment text
  - maybe_add_activity_comment() — orchestrator, calls add_comment if applicable

CRITICAL: This module imports add_comment from task_comments.py.
  add_comment calls record_audit("COMMENT").
  This module is NEVER called from record_audit or add_comment.
  The loop cannot form by architecture.
  Belt-and-suspenders: COMMENT/CREATE actions return None.
"""

import logging
from typing import Any, Dict, Optional

from governance.services.task_comments import add_comment

logger = logging.getLogger(__name__)

# Author for all auto-generated comments — distinguishes from user comments
SYSTEM_AUDIT_AUTHOR = "system-audit"

# Max snippet length for evidence/field values in comment text
_MAX_SNIPPET = 120

# Action types that should NOT generate auto-comments
_SKIP_ACTIONS = frozenset({"COMMENT", "CREATE"})


def _truncate(text: str, max_len: int = _MAX_SNIPPET) -> str:
    """Truncate text with ellipsis if too long."""
    if not text:
        return ""
    text = str(text)
    return text[:max_len] + "..." if len(text) > max_len else text


def _format_attribution(actor_id: str, source: str) -> str:
    """Format 'by {actor} ({source})' suffix."""
    parts = []
    if actor_id:
        parts.append(f"by {actor_id}")
    if source:
        parts.append(f"({source})")
    return " ".join(parts)


def _format_status_change(field_changes: Dict, actor_id: str, source: str) -> str:
    """Format status change: 'Status changed from X to Y by actor (source)'."""
    sc = field_changes.get("status", {})
    old = sc.get("from", "?")
    new = sc.get("to", "?")
    attr = _format_attribution(actor_id, source)
    return f"Status changed from {old} to {new} {attr}".strip()


def _format_field_changes(field_changes: Dict, actor_id: str, source: str) -> str:
    """Format non-status field changes.

    Evidence gets special treatment with snippet.
    Other fields: 'field FROM -> TO'.
    """
    lines = []
    for field, change in field_changes.items():
        if field == "status":
            continue  # Handled separately
        old = change.get("from")
        new = change.get("to")
        if field == "evidence":
            snippet = _truncate(new) if new else ""
            lines.append(f"Evidence updated: {snippet}" if snippet else "Evidence cleared")
        else:
            if old is None:
                lines.append(f"{field} set to {_truncate(str(new))}")
            else:
                lines.append(f"{field} {_truncate(str(old))} \u2192 {_truncate(str(new))}")

    attr = _format_attribution(actor_id, source)
    if not lines:
        return f"Task updated {attr}".strip()

    if len(lines) == 1:
        return f"{lines[0]} {attr}".strip()

    body = "; ".join(lines)
    return f"Updated {attr}: {body}".strip()


def _format_link(metadata: Dict, actor_id: str, source: str) -> str:
    """Format LINK action: '{Type} {id} linked by actor (source)'."""
    linked = metadata.get("linked_entity", {})
    etype = linked.get("type", "entity")
    eid = linked.get("id", "unknown")
    action = linked.get("action", "link")
    verb = "linked" if action == "link" else "linked"

    type_label = etype.capitalize()
    attr = _format_attribution(actor_id, source)
    return f"{type_label} {eid} {verb} {attr}".strip()


def _format_unlink(metadata: Dict, actor_id: str, source: str) -> str:
    """Format UNLINK action: '{Type} {id} unlinked by actor (source)'."""
    linked = metadata.get("linked_entity", {})
    etype = linked.get("type", "entity")
    eid = linked.get("id", "unknown")
    type_label = etype.capitalize()
    attr = _format_attribution(actor_id, source)
    return f"{type_label} {eid} unlinked {attr}".strip()


def format_activity_text(
    action_type: str,
    actor_id: str = "system",
    source: str = "rest",
    old_value: str = None,
    new_value: str = None,
    metadata: Dict[str, Any] = None,
) -> Optional[str]:
    """Generate human-readable comment text from an audit event.

    Returns None if no comment should be generated (COMMENT, CREATE actions).

    Args:
        action_type: UPDATE, DELETE, LINK, UNLINK, COMMENT, CREATE
        actor_id: Who performed the action
        source: Where it came from (rest, mcp, etc.)
        old_value: Previous value (for status changes)
        new_value: New value (for status changes)
        metadata: Audit metadata (field_changes, linked_entity, etc.)

    Returns:
        Comment text string, or None to skip.
    """
    if action_type in _SKIP_ACTIONS:
        return None

    metadata = metadata or {}
    field_changes = metadata.get("field_changes", {})

    if action_type == "UPDATE":
        parts = []
        # Status change gets its own line
        if "status" in field_changes:
            parts.append(_format_status_change(field_changes, actor_id, source))
        # Other field changes
        non_status = {k: v for k, v in field_changes.items() if k != "status"}
        if non_status:
            parts.append(_format_field_changes(non_status, actor_id, source))
        elif not parts:
            # No field_changes at all — generic update
            attr = _format_attribution(actor_id, source)
            parts.append(f"Task updated {attr}".strip())
        return "; ".join(parts) if parts else f"Task updated {_format_attribution(actor_id, source)}".strip()

    if action_type == "DELETE":
        attr = _format_attribution(actor_id, source)
        return f"Task deleted {attr}".strip()

    if action_type == "LINK":
        if metadata.get("linked_entity"):
            return _format_link(metadata, actor_id, source)
        attr = _format_attribution(actor_id, source)
        return f"Entity linked {attr}".strip()

    if action_type == "UNLINK":
        if metadata.get("linked_entity"):
            return _format_unlink(metadata, actor_id, source)
        attr = _format_attribution(actor_id, source)
        return f"Entity unlinked {attr}".strip()

    # Unknown action type — generic fallback
    attr = _format_attribution(actor_id, source)
    return f"{action_type} {attr}".strip()


def maybe_add_activity_comment(
    task_id: str,
    action_type: str,
    actor_id: str = "system",
    source: str = "rest",
    old_value: str = None,
    new_value: str = None,
    metadata: Dict[str, Any] = None,
) -> Optional[Dict[str, Any]]:
    """Auto-generate a system comment for a task mutation if applicable.

    Returns the created comment dict, or None if skipped/failed.

    This function is called from tasks_mutations.py and tasks_mutations_linking.py
    AFTER record_audit(). It is NEVER called from record_audit() or add_comment().
    """
    text = format_activity_text(
        action_type=action_type,
        actor_id=actor_id,
        source=source,
        old_value=old_value,
        new_value=new_value,
        metadata=metadata,
    )
    if text is None:
        return None

    try:
        return add_comment(task_id, body=text, author=SYSTEM_AUDIT_AUTHOR)
    except Exception as e:
        logger.warning(
            "Auto-comment failed for %s [%s]: %s",
            task_id, action_type, type(e).__name__,
        )
        return None
