"""
Governance Stores - Audit Trail Module.

Per RD-DEBUG-AUDIT: Audit trail for debugging agent decisions, rule applications,
and task state changes.

Per SRVJ-FEAT-AUDIT-TRAIL-01 P5: Dual-write (JSON + TypeDB).
  - JSON file: hot cache (7-day retention, 50K cap)
  - TypeDB: source of truth (90-day retention, graph-queryable)
  - Write order: in-memory → JSON → TypeDB (best-effort)
  - Query order: TypeDB-first → JSON fallback → merge + dedup
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
    """Load audit entries from file.

    BUG-P6-REFBIND-001: Uses slice assignment instead of name rebinding
    to preserve list identity for any code holding a reference to _audit_store.
    """
    if AUDIT_STORE_PATH.exists():
        try:
            # BUG-201-AUDIT-002: Specify encoding for cross-platform safety
            with open(AUDIT_STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # BUG-STORE-004: Validate JSON structure
            if isinstance(data, list):
                _audit_store[:] = [e for e in data if isinstance(e, dict)]
            else:
                logger.warning("Audit store JSON is not a list, resetting")
                _audit_store[:] = []
            logger.info(f"Loaded {len(_audit_store)} audit entries")
        except Exception as e:
            # BUG-433-AUD-001: Add exc_info for stack trace preservation
            # BUG-473-AUD-1: Sanitize logger message — exc_info=True already captures full stack
            logger.warning(f"Failed to load audit store: {type(e).__name__}", exc_info=True)
            _audit_store[:] = []


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
        # BUG-433-AUD-002: Add exc_info for stack trace preservation
        # BUG-473-AUD-2: Sanitize logger message — exc_info=True already captures full stack
        logger.warning(f"Failed to save audit store: {type(e).__name__}", exc_info=True)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return f"CORR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def get_typedb_client():
    """Get TypeDB client for audit persistence.

    Delegates to stores.config.get_typedb_client. Returns None on any failure.
    """
    try:
        from governance.stores.config import get_typedb_client as _get_client
        return _get_client()
    except Exception:
        return None


def _persist_audit_to_typedb(entry_dict: Dict[str, Any]) -> None:
    """Persist an audit entry to TypeDB (best-effort, fire-and-forget).

    Per SRVJ-FEAT-AUDIT-TRAIL-01 P5:
    - Level 2 Safety (Isolation): JSON already written before this is called
    - Level 4 Safety (Graceful Degradation): entity created even if relations fail
    - Idempotent: @key on audit-entry-id prevents duplicates

    Steps:
    1. Insert audit-entry entity with all attributes
    2. Attempt task-audit relation if entity_type=task and task exists
    3. Attempt session-audit relation if session_id in metadata
    """
    client = get_typedb_client()
    if not client:
        return

    try:
        from typedb.driver import TransactionType
    except ImportError:
        return

    audit_id = entry_dict.get("audit_id", "")
    entity_type = entry_dict.get("entity_type", "")
    entity_id = entry_dict.get("entity_id", "")
    session_id = entry_dict.get("metadata", {}).get("session_id", "")

    # Escape strings for TypeQL
    def _esc(val: str) -> str:
        return val.replace("\\", "\\\\").replace('"', '\\"') if val else ""

    try:
        with client._driver.transaction(client.database, TransactionType.WRITE) as tx:
            # Step 1: Check if already exists (@key guard at application level too)
            check_q = (
                f'match $a isa audit-entry, has audit-entry-id '
                f'"{_esc(audit_id)}"; select $a;'
            )
            existing = list(tx.query(check_q).resolve() or [])
            if existing:
                tx.commit()
                return  # Idempotent skip

            # Step 2: Insert audit-entry entity
            # Format timestamp as TypeDB datetime (seconds precision, no quotes)
            ts_raw = entry_dict.get("timestamp", "")
            ts_typedb = ts_raw[:19] if ts_raw else datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            # Build insert with only non-None optional attributes
            insert_parts = [
                "insert $a isa audit-entry",
                f'  has audit-entry-id "{_esc(audit_id)}"',
                f'  has audit-correlation-id "{_esc(entry_dict.get("correlation_id", ""))}"',
                f"  has audit-timestamp {ts_typedb}",
                f'  has audit-actor-id "{_esc(entry_dict.get("actor_id", "system"))}"',
                f'  has audit-action-type "{_esc(entry_dict.get("action_type", ""))}"',
                f'  has audit-entity-type "{_esc(entity_type)}"',
                f'  has audit-entity-id "{_esc(entity_id)}"',
            ]
            if session_id:
                insert_parts.append(f'  has audit-session-id "{_esc(session_id)}"')
            if entry_dict.get("old_value"):
                insert_parts.append(f'  has audit-old-value "{_esc(str(entry_dict["old_value"]))}"')
            if entry_dict.get("new_value"):
                insert_parts.append(f'  has audit-new-value "{_esc(str(entry_dict["new_value"]))}"')
            # Metadata as JSON string
            meta_json = json.dumps(entry_dict.get("metadata", {}), ensure_ascii=False)
            insert_parts.append(f'  has audit-metadata "{_esc(meta_json)}"')

            insert_q = ",\n".join(insert_parts) + ";"
            tx.query(insert_q).resolve()

            # Step 3: Attempt task-audit relation (graceful degradation)
            if entity_type == "task" and entity_id:
                try:
                    task_check = (
                        f'match $t isa task, has task-id "{_esc(entity_id)}"; select $t;'
                    )
                    task_exists = list(tx.query(task_check).resolve() or [])
                    if task_exists:
                        rel_q = (
                            f'match $t isa task, has task-id "{_esc(entity_id)}"; '
                            f'$a isa audit-entry, has audit-entry-id "{_esc(audit_id)}"; '
                            f"insert (audited-task: $t, task-audit-entry: $a) isa task-audit;"
                        )
                        tx.query(rel_q).resolve()
                except Exception:
                    logger.debug(f"task-audit relation skipped for {entity_id}")

            # Step 4: Attempt session-audit relation (graceful degradation)
            if session_id:
                try:
                    sess_check = (
                        f'match $s isa work-session, has session-id "{_esc(session_id)}"; '
                        f"select $s;"
                    )
                    sess_exists = list(tx.query(sess_check).resolve() or [])
                    if sess_exists:
                        sess_rel_q = (
                            f'match $s isa work-session, has session-id "{_esc(session_id)}"; '
                            f'$a isa audit-entry, has audit-entry-id "{_esc(audit_id)}"; '
                            f"insert (audit-session: $s, session-audit-entry: $a) isa session-audit;"
                        )
                        tx.query(sess_rel_q).resolve()
                except Exception:
                    logger.debug(f"session-audit relation skipped for {session_id}")

            tx.commit()
            logger.debug(f"TypeDB audit persist OK: {audit_id}")

    except Exception as e:
        # Level 2 Safety: silent failure — JSON already written
        logger.warning(f"TypeDB audit persist failed for {audit_id}: {type(e).__name__}", exc_info=True)


def _query_audit_from_typedb(
    entity_id: str = None,
    entity_type: str = None,
    correlation_id: str = None,
    action_type: str = None,
    actor_id: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = 50,
) -> Optional[List[Dict[str, Any]]]:
    """Query audit entries from TypeDB.

    Per SRVJ-FEAT-AUDIT-TRAIL-01 P5: TypeDB-first query.
    Returns None if TypeDB unavailable (signals fallback to JSON).
    Returns list of dicts on success.
    """
    client = get_typedb_client()
    if not client:
        return None
    if not client.is_connected():
        return None

    def _esc(val: str) -> str:
        return val.replace("\\", "\\\\").replace('"', '\\"') if val else ""

    # Build match clause with filters
    match_parts = ["$a isa audit-entry"]
    select_vars = ["$aid", "$act", "$etype", "$eid", "$actor"]

    if entity_id:
        match_parts.append(f'has audit-entity-id "{_esc(entity_id)}"')
    if entity_type:
        match_parts.append(f'has audit-entity-type "{_esc(entity_type)}"')
    if action_type:
        match_parts.append(f'has audit-action-type "{_esc(action_type)}"')
    if actor_id:
        match_parts.append(f'has audit-actor-id "{_esc(actor_id)}"')
    if correlation_id:
        match_parts.append(f'has audit-correlation-id "{_esc(correlation_id)}"')

    # Always select core fields
    match_parts.extend([
        "has audit-entry-id $aid",
        "has audit-action-type $act",
        "has audit-entity-type $etype",
        "has audit-entity-id $eid",
        "has audit-actor-id $actor",
    ])

    query = (
        f"match {', '.join(match_parts)}; "
        f"select {', '.join(select_vars)}; "
        f"limit {min(limit, 1000)};"
    )

    try:
        results = client.execute_query(query)
        entries = []
        for row in results:
            entry = {
                "audit_id": row.get("aid"),
                "action_type": row.get("act"),
                "entity_type": row.get("etype"),
                "entity_id": row.get("eid"),
                "actor_id": row.get("actor"),
                "timestamp": str(row.get("ts", "")),
                # Remaining fields need individual attribute queries (expensive)
                # For now, return core fields for dedup + display
                "correlation_id": "",
                "old_value": None,
                "new_value": None,
                "applied_rules": [],
                "metadata": {},
            }
            entries.append(entry)
        return entries
    except Exception as e:
        logger.warning(f"TypeDB audit query failed: {type(e).__name__}", exc_info=True)
        return None


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

    entry_dict = entry.to_dict()
    _audit_store.append(entry_dict)

    # Step 2: JSON persist (with 7-day retention)
    _apply_retention()
    _save_audit_store()

    # Step 3: TypeDB persist (best-effort, after JSON is safe)
    # Per SRVJ-FEAT-AUDIT-TRAIL-01 P5 Level 2 Safety:
    # TypeDB failure must never affect the JSON path.
    try:
        _persist_audit_to_typedb(entry_dict)
    except Exception as e:
        logger.warning(f"TypeDB audit dual-write failed: {type(e).__name__}", exc_info=True)

    logger.debug(f"Recorded audit: {entry.audit_id} [{entry.action_type}] {entry.entity_type}:{entry.entity_id}")
    return entry


# Default archive directory (logs/audit/ relative to project root)
AUDIT_ARCHIVE_DIR = Path(__file__).parent.parent.parent / "logs" / "audit"


def _archive_entries(
    entries: List[Dict[str, Any]],
    archive_dir: Path = None,
) -> None:
    """Write audit entries to daily JSONL archive files.

    Per SRVJ-FEAT-AUDIT-TRAIL-01 P4: Cold archive before retention deletes.
    Groups entries by date → one file per day (YYYY-MM-DD.jsonl).
    Appends to existing files. Silent on failure (logs warning).
    """
    if not entries:
        return

    target_dir = archive_dir or AUDIT_ARCHIVE_DIR
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning(f"Cannot create archive dir {target_dir}: {e}")
        return

    # Group by date from timestamp
    by_date: Dict[str, List[Dict]] = {}
    for entry in entries:
        date_key = entry.get("timestamp", "")[:10] or "unknown"
        by_date.setdefault(date_key, []).append(entry)

    for date_key, day_entries in by_date.items():
        filepath = target_dir / f"{date_key}.jsonl"
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                for entry in day_entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning(f"Archive write failed for {filepath}: {e}")


def query_audit_archive(
    entity_id: str = None,
    action_type: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = 100,
    archive_dir: Path = None,
) -> List[Dict[str, Any]]:
    """Query cold archive JSONL files.

    Per SRVJ-FEAT-AUDIT-TRAIL-01 P4: Read archived entries with filters.
    Scans all *.jsonl files in archive directory.
    """
    target_dir = archive_dir or AUDIT_ARCHIVE_DIR
    if not target_dir.exists():
        return []

    results = []
    for filepath in sorted(target_dir.glob("*.jsonl")):
        # Optimization: skip files outside date range based on filename
        file_date = filepath.stem  # e.g. "2026-03-20"
        if date_from and file_date < date_from:
            continue
        if date_to and file_date > date_to:
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(f"Corrupt JSONL line in {filepath}, skipping")
                        continue

                    # Apply filters
                    if entity_id and entry.get("entity_id") != entity_id:
                        continue
                    if action_type and entry.get("action_type") != action_type:
                        continue

                    results.append(entry)
                    if len(results) >= min(limit, 1000):
                        return results
        except OSError as e:
            logger.warning(f"Cannot read archive {filepath}: {e}")

    return results


def _apply_retention(days: int = 7):
    """Apply retention policy - keep only entries from last N days.

    Per SRVJ-FEAT-AUDIT-TRAIL-01 P4: Archive entries BEFORE deleting.
    """
    global _audit_store
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # P4: Identify entries that will be removed by date-based retention
    expired = [
        e for e in _audit_store
        if e.get("timestamp", "")[:10] < cutoff
    ]
    # Archive expired entries before deletion (silent on failure)
    if expired:
        _archive_entries(expired)

    original_count = len(_audit_store)
    # BUG-329-AUD-002: Use slice assignment instead of name rebinding to prevent
    # race condition where concurrent append() is lost during retention
    _audit_store[:] = [
        e for e in _audit_store
        if e.get("timestamp", "")[:10] >= cutoff
    ]
    # BUG-353-AUD-001: Hard cap independent of date-based retention
    if len(_audit_store) > _MAX_AUDIT_ENTRIES:
        # Archive overflow entries too
        overflow = _audit_store[:-_MAX_AUDIT_ENTRIES]
        if overflow:
            _archive_entries(overflow)
        _audit_store[:] = _audit_store[-_MAX_AUDIT_ENTRIES:]
    removed = original_count - len(_audit_store)
    if removed > 0:
        logger.info(f"Retention policy removed {removed} old audit entries (archived)")


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

    # Per SRVJ-FEAT-AUDIT-TRAIL-01 P5 Level 3 Safety (Query Fallback):
    # Try TypeDB first → fall back to JSON → merge + dedup by audit_id
    typedb_results = None
    try:
        typedb_results = _query_audit_from_typedb(
            entity_id=entity_id,
            entity_type=entity_type,
            correlation_id=correlation_id,
            action_type=action_type,
            actor_id=actor_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit + offset,  # Fetch enough for pagination
        )
    except Exception:
        typedb_results = None

    # JSON in-memory query (always available)
    json_result = _audit_store.copy()
    if entity_id:
        json_result = [e for e in json_result if e.get("entity_id") == entity_id]
    if entity_type:
        json_result = [e for e in json_result if e.get("entity_type") == entity_type]
    if correlation_id:
        json_result = [e for e in json_result if e.get("correlation_id") == correlation_id]
    if action_type:
        json_result = [e for e in json_result if e.get("action_type") == action_type]
    if actor_id:
        json_result = [e for e in json_result if e.get("actor_id") == actor_id]
    if date_from:
        json_result = [e for e in json_result if e.get("timestamp", "") >= date_from]
    if date_to:
        # BUG-AUDIT-MICROSECOND-001: Include microseconds to avoid off-by-one
        date_to_end = date_to + "T23:59:59.999999" if "T" not in date_to else date_to
        json_result = [e for e in json_result if e.get("timestamp", "") <= date_to_end]

    # Merge + dedup: JSON entries have full metadata (preferred when available),
    # TypeDB fills gaps (entries purged from JSON by 7-day retention).
    if typedb_results is not None and typedb_results:
        seen_ids = set()
        merged = []
        # JSON entries first (richer data — full metadata, old/new values)
        for entry in json_result:
            aid = entry.get("audit_id")
            if aid and aid not in seen_ids:
                seen_ids.add(aid)
                merged.append(entry)
        # TypeDB entries that aren't in JSON (survived retention purge)
        for entry in typedb_results:
            aid = entry.get("audit_id")
            if aid and aid not in seen_ids:
                seen_ids.add(aid)
                merged.append(entry)
        result = merged
    else:
        # TypeDB unavailable or returned nothing — use JSON only
        result = json_result

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
