"""
Governance Stores - Audit Trail Module.

Per RD-DEBUG-AUDIT: Audit trail for debugging agent decisions, rule applications,
and task state changes.

Uses in-memory store with file persistence (avoids Python 3.13 TypeDB issue).
"""

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Audit store location (persisted between restarts)
AUDIT_STORE_PATH = Path(__file__).parent.parent.parent / "data" / "audit_trail.json"


@dataclass
class AuditEntry:
    """Single audit trail entry."""
    audit_id: str
    correlation_id: str
    timestamp: str
    actor_id: str  # Agent or user ID
    action_type: str  # CREATE, UPDATE, DELETE, CLAIM, COMPLETE, VERIFY
    entity_type: str  # task, session, rule, gap
    entity_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    applied_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# In-memory audit store
_audit_store: List[Dict[str, Any]] = []

# BUG-353-AUD-001: Hard cap on in-memory audit entries to prevent unbounded growth
_MAX_AUDIT_ENTRIES = 50_000


def _load_audit_store():
    """Load audit entries from file."""
    global _audit_store
    if AUDIT_STORE_PATH.exists():
        try:
            # BUG-201-AUDIT-002: Specify encoding for cross-platform safety
            with open(AUDIT_STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # BUG-STORE-004: Validate JSON structure
            if isinstance(data, list):
                _audit_store = [e for e in data if isinstance(e, dict)]
            else:
                logger.warning("Audit store JSON is not a list, resetting")
                _audit_store = []
            logger.info(f"Loaded {len(_audit_store)} audit entries")
        except Exception as e:
            logger.warning(f"Failed to load audit store: {e}")
            _audit_store = []


def _save_audit_store():
    """Save audit entries to file.

    BUG-201-AUDIT-001: Uses atomic write (temp file + rename) to prevent
    data loss if process is killed mid-write.
    """
    # BUG-329-AUD-001: Initialize tmp before try to prevent UnboundLocalError
    # if mkdir raises (e.g. permission denied) before tmp assignment
    tmp = None
    try:
        AUDIT_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = AUDIT_STORE_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_audit_store, f, indent=2)
        tmp.replace(AUDIT_STORE_PATH)
    except Exception as e:
        # BUG-291-AUD-001: Clean up orphaned .tmp file on save failure
        if tmp is not None:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
        logger.warning(f"Failed to save audit store: {e}")


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return f"CORR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def record_audit(
    action_type: str,
    entity_type: str,
    entity_id: str,
    actor_id: str = "system",
    correlation_id: str = None,
    old_value: str = None,
    new_value: str = None,
    applied_rules: List[str] = None,
    metadata: Dict[str, Any] = None
) -> AuditEntry:
    """
    Record an audit trail entry.

    Per RD-DEBUG-AUDIT: All task state changes should be logged with correlation_id.

    Args:
        action_type: Action performed (CREATE, UPDATE, DELETE, CLAIM, COMPLETE, VERIFY)
        entity_type: Entity type (task, session, rule, gap)
        entity_id: Entity identifier
        actor_id: Agent or user ID performing the action
        correlation_id: Cross-request trace ID (auto-generated if not provided)
        old_value: Previous value (for UPDATE actions)
        new_value: New value (for UPDATE actions)
        applied_rules: List of rule IDs that influenced this decision
        metadata: Additional context

    Returns:
        AuditEntry that was recorded
    """
    entry = AuditEntry(
        audit_id=f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
        correlation_id=correlation_id or generate_correlation_id(),
        timestamp=datetime.now().isoformat(),
        actor_id=actor_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        applied_rules=applied_rules or [],
        metadata=metadata or {}
    )

    _audit_store.append(entry.to_dict())

    # Persist (with 7-day retention)
    _apply_retention()
    _save_audit_store()

    logger.debug(f"Recorded audit: {entry.audit_id} [{entry.action_type}] {entry.entity_type}:{entry.entity_id}")
    return entry


def _apply_retention(days: int = 7):
    """Apply retention policy - keep only entries from last N days."""
    global _audit_store
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    original_count = len(_audit_store)
    # BUG-329-AUD-002: Use slice assignment instead of name rebinding to prevent
    # race condition where concurrent append() is lost during retention
    _audit_store[:] = [
        e for e in _audit_store
        if e.get("timestamp", "")[:10] >= cutoff
    ]
    # BUG-353-AUD-001: Hard cap independent of date-based retention
    if len(_audit_store) > _MAX_AUDIT_ENTRIES:
        _audit_store[:] = _audit_store[-_MAX_AUDIT_ENTRIES:]
    removed = original_count - len(_audit_store)
    if removed > 0:
        logger.info(f"Retention policy removed {removed} old audit entries")


def query_audit_trail(
    entity_id: str = None,
    entity_type: str = None,
    correlation_id: str = None,
    action_type: str = None,
    actor_id: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Query audit trail entries.

    Per RD-DEBUG-AUDIT Phase 4: Audit trail queryable by entity_id.
    Per GAP-AUDIT-RANGE-001: date_from/date_to for timestamp filtering.

    Args:
        entity_id: Filter by entity ID
        entity_type: Filter by entity type (task, session, rule, gap)
        correlation_id: Filter by correlation ID
        action_type: Filter by action type
        actor_id: Filter by actor ID
        date_from: Include entries on or after this date (YYYY-MM-DD)
        date_to: Include entries on or before this date (YYYY-MM-DD)
        limit: Maximum entries to return
        offset: Skip first N entries

    Returns:
        List of matching audit entries (most recent first)
    """
    # BUG-226-AUDIT-003: Validate offset/limit to prevent negative slice behavior
    # BUG-340-AUD-001: Cap limit to prevent unbounded query responses (DoS vector)
    _MAX_QUERY_LIMIT = 1000
    limit = max(1, min(limit, _MAX_QUERY_LIMIT))
    offset = max(0, offset)

    result = _audit_store.copy()

    # Apply filters
    if entity_id:
        result = [e for e in result if e.get("entity_id") == entity_id]
    if entity_type:
        result = [e for e in result if e.get("entity_type") == entity_type]
    if correlation_id:
        result = [e for e in result if e.get("correlation_id") == correlation_id]
    if action_type:
        result = [e for e in result if e.get("action_type") == action_type]
    if actor_id:
        result = [e for e in result if e.get("actor_id") == actor_id]
    if date_from:
        result = [e for e in result if e.get("timestamp", "") >= date_from]
    if date_to:
        # Add end-of-day to include the full date_to day
        # BUG-AUDIT-MICROSECOND-001: Include microseconds to avoid off-by-one
        date_to_end = date_to + "T23:59:59.999999" if "T" not in date_to else date_to
        result = [e for e in result if e.get("timestamp", "") <= date_to_end]

    # Sort by timestamp descending (most recent first)
    result.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    # Apply pagination
    return result[offset:offset + limit]


def get_audit_summary() -> Dict[str, Any]:
    """Get audit trail summary statistics."""
    total = len(_audit_store)
    by_action = {}
    by_entity = {}
    by_actor = {}

    for e in _audit_store:
        action = e.get("action_type", "UNKNOWN")
        entity = e.get("entity_type", "UNKNOWN")
        actor = e.get("actor_id", "UNKNOWN")

        by_action[action] = by_action.get(action, 0) + 1
        by_entity[entity] = by_entity.get(entity, 0) + 1
        by_actor[actor] = by_actor.get(actor, 0) + 1

    return {
        "total_entries": total,
        "by_action_type": by_action,
        "by_entity_type": by_entity,
        "by_actor": by_actor,
        "retention_days": 7
    }


# Load audit store on module import
_load_audit_store()
