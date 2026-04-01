#!/usr/bin/env python3
"""Bulk migrate existing audit_trail.json entries to TypeDB.

Per SRVJ-FEAT-AUDIT-TRAIL-01 P5: Idempotent migration script.
Safe to re-run — @key on audit-entry-id prevents duplicates.

Usage:
    .venv/bin/python3 scripts/migrate_audit_to_typedb.py
    .venv/bin/python3 scripts/migrate_audit_to_typedb.py --dry-run
    .venv/bin/python3 scripts/migrate_audit_to_typedb.py --batch-size 50
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

AUDIT_FILE = PROJECT_ROOT / "data" / "audit_trail.json"


def _esc(val: str) -> str:
    """Escape string for TypeQL."""
    return val.replace("\\", "\\\\").replace('"', '\\"') if val else ""


def migrate(dry_run: bool = False, batch_size: int = 100):
    """Migrate audit_trail.json entries to TypeDB."""
    if not AUDIT_FILE.exists():
        logger.error(f"Audit file not found: {AUDIT_FILE}")
        return

    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    if not isinstance(entries, list):
        logger.error("Audit file is not a JSON array")
        return

    logger.info(f"Found {len(entries)} entries in {AUDIT_FILE}")

    if dry_run:
        logger.info("DRY RUN — no writes will be performed")
        # Count unique IDs
        ids = set(e.get("audit_id") for e in entries if e.get("audit_id"))
        logger.info(f"Unique audit IDs: {len(ids)}")
        return

    from typedb.driver import TypeDB, Credentials, DriverOptions, TransactionType

    host = os.getenv("TYPEDB_HOST", "localhost")
    port = os.getenv("TYPEDB_PORT", "1729")
    database = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")
    credentials = Credentials(
        os.getenv("TYPEDB_USERNAME", "admin"),
        os.getenv("TYPEDB_PASSWORD", "password"),
    )
    options = DriverOptions(is_tls_enabled=False)
    driver = TypeDB.driver(f"{host}:{port}", credentials, options)

    migrated = 0
    skipped = 0
    failed = 0

    for i in range(0, len(entries), batch_size):
        batch = entries[i : i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1} ({i}–{i + len(batch) - 1})")

        for entry in batch:
            audit_id = entry.get("audit_id", "")
            if not audit_id:
                skipped += 1
                continue

            try:
                with driver.transaction(database, TransactionType.WRITE) as tx:
                    # Check existence (idempotent)
                    check_q = (
                        f'match $a isa audit-entry, has audit-entry-id '
                        f'"{_esc(audit_id)}"; select $a;'
                    )
                    existing = list(tx.query(check_q).resolve() or [])
                    if existing:
                        skipped += 1
                        tx.commit()
                        continue

                    # Build insert
                    ts_raw = entry.get("timestamp", "")
                    ts_typedb = ts_raw[:19] if ts_raw else "2026-01-01T00:00:00"

                    parts = [
                        "insert $a isa audit-entry",
                        f'  has audit-entry-id "{_esc(audit_id)}"',
                        f'  has audit-correlation-id "{_esc(entry.get("correlation_id", ""))}"',
                        f"  has audit-timestamp {ts_typedb}",
                        f'  has audit-actor-id "{_esc(entry.get("actor_id", "system"))}"',
                        f'  has audit-action-type "{_esc(entry.get("action_type", ""))}"',
                        f'  has audit-entity-type "{_esc(entry.get("entity_type", ""))}"',
                        f'  has audit-entity-id "{_esc(entry.get("entity_id", ""))}"',
                    ]
                    session_id = (entry.get("metadata") or {}).get("session_id", "")
                    if session_id:
                        parts.append(f'  has audit-session-id "{_esc(session_id)}"')
                    if entry.get("old_value"):
                        parts.append(f'  has audit-old-value "{_esc(str(entry["old_value"]))}"')
                    if entry.get("new_value"):
                        parts.append(f'  has audit-new-value "{_esc(str(entry["new_value"]))}"')
                    meta = json.dumps(entry.get("metadata", {}), ensure_ascii=False)
                    parts.append(f'  has audit-metadata "{_esc(meta)}"')

                    insert_q = ",\n".join(parts) + ";"
                    tx.query(insert_q).resolve()

                    # Attempt task-audit relation
                    entity_type = entry.get("entity_type", "")
                    entity_id = entry.get("entity_id", "")
                    if entity_type == "task" and entity_id:
                        try:
                            task_check = (
                                f'match $t isa task, has task-id '
                                f'"{_esc(entity_id)}"; select $t;'
                            )
                            if list(tx.query(task_check).resolve() or []):
                                rel_q = (
                                    f'match $t isa task, has task-id "{_esc(entity_id)}"; '
                                    f'$a isa audit-entry, has audit-entry-id "{_esc(audit_id)}"; '
                                    f"insert (audited-task: $t, task-audit-entry: $a) isa task-audit;"
                                )
                                tx.query(rel_q).resolve()
                        except Exception:
                            pass  # Graceful degradation

                    tx.commit()
                    migrated += 1

            except Exception as e:
                failed += 1
                if failed <= 5:
                    logger.warning(f"Failed to migrate {audit_id}: {type(e).__name__}: {e}")
                elif failed == 6:
                    logger.warning("Suppressing further failure messages...")

        logger.info(f"Progress: migrated={migrated} skipped={skipped} failed={failed}")

    driver.close()
    logger.info(
        f"Migration complete: {migrated} migrated, {skipped} skipped, {failed} failed "
        f"(total: {len(entries)})"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate audit entries to TypeDB")
    parser.add_argument("--dry-run", action="store_true", help="Count entries without writing")
    parser.add_argument("--batch-size", type=int, default=100, help="Entries per batch")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run, batch_size=args.batch_size)
