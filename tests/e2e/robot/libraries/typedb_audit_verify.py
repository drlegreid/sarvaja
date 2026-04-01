"""
TypeDB Audit Trail Direct Verification Library
================================================
Per SRVJ-FEAT-AUDIT-TRAIL-01 P5: E2E assertions MUST query TypeDB directly
for audit-entry entities, bypassing the JSON audit store.

Extends the typedb_verify.py pattern for audit-specific assertions.

Usage in Robot:
    Library    ../libraries/typedb_audit_verify.py
    ${result}=    Query Audit Entry In TypeDB    AUDIT-3FA8B1C0
    Should Not Be Empty    ${result}
"""

import os

from robot.api import logger
from robot.api.deco import keyword


def _get_driver():
    """Connect to TypeDB using the same credentials as the app."""
    from typedb.driver import Credentials, DriverOptions, TypeDB

    host = os.getenv("TYPEDB_HOST", "localhost")
    port = os.getenv("TYPEDB_PORT", "1729")
    username = os.getenv("TYPEDB_USERNAME", "admin")
    password = os.getenv("TYPEDB_PASSWORD", "password")

    credentials = Credentials(username, password)
    options = DriverOptions(is_tls_enabled=False)
    return TypeDB.driver(f"{host}:{port}", credentials, options)


def _read_tx(driver, query):
    """Execute a read query and return list of result rows."""
    from typedb.driver import TransactionType

    database = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")
    with driver.transaction(database, TransactionType.READ) as tx:
        rows = list(tx.query(query).resolve() or [])
        return rows


def _concept_to_value(concept):
    """Convert TypeDB concept to Python value."""
    if concept is None:
        return None
    if hasattr(concept, "get_value"):
        try:
            return concept.get_value()
        except Exception:
            pass
    if hasattr(concept, "value"):
        return concept.value
    return str(concept)


@keyword("Query Audit Entry In TypeDB")
def query_audit_entry_in_typedb(audit_entry_id: str) -> dict:
    """Query TypeDB directly for an audit-entry by ID.

    Returns dict of attributes or empty dict if not found.
    """
    audit_id_escaped = audit_entry_id.replace("\\", "\\\\").replace('"', '\\"')
    driver = _get_driver()
    try:
        query = (
            f'match $a isa audit-entry, has audit-entry-id "{audit_id_escaped}"; '
            f"select $a;"
        )
        rows = _read_tx(driver, query)
        if not rows:
            logger.info(f"Audit entry {audit_entry_id} NOT found in TypeDB")
            return {}

        # Fetch attributes
        attr_names = [
            "audit-entry-id",
            "audit-correlation-id",
            "audit-actor-id",
            "audit-action-type",
            "audit-entity-type",
            "audit-entity-id",
            "audit-session-id",
            "audit-old-value",
            "audit-new-value",
            "audit-metadata",
        ]
        result = {}
        for attr in attr_names:
            try:
                q = (
                    f'match $a isa audit-entry, has audit-entry-id '
                    f'"{audit_id_escaped}", has {attr} $v; select $v;'
                )
                attr_rows = _read_tx(driver, q)
                if attr_rows:
                    result[attr] = _concept_to_value(attr_rows[0].get("v"))
            except Exception:
                pass
        logger.info(
            f"Audit entry {audit_entry_id} found in TypeDB "
            f"with {len(result)} attributes"
        )
        return result
    finally:
        driver.close()


@keyword("Query Audit Entries For Entity In TypeDB")
def query_audit_entries_for_entity_in_typedb(
    entity_id: str, limit: int = 50
) -> list:
    """Query TypeDB for all audit entries linked to an entity_id.

    Uses attribute-based query (audit-entity-id), not relation traversal.
    Returns list of dicts.
    """
    entity_id_escaped = entity_id.replace("\\", "\\\\").replace('"', '\\"')
    driver = _get_driver()
    try:
        query = (
            f'match $a isa audit-entry, has audit-entity-id "{entity_id_escaped}", '
            f"has audit-entry-id $id, has audit-action-type $act, "
            f"has audit-actor-id $actor; "
            f"select $id, $act, $actor;"
        )
        rows = _read_tx(driver, query)
        results = []
        for row in rows[:limit]:
            results.append(
                {
                    "audit-entry-id": _concept_to_value(row.get("id")),
                    "audit-action-type": _concept_to_value(row.get("act")),
                    "audit-actor-id": _concept_to_value(row.get("actor")),
                }
            )
        logger.info(
            f"Found {len(results)} audit entries for entity {entity_id} in TypeDB"
        )
        return results
    finally:
        driver.close()


@keyword("Query Audit Entries By Actor In TypeDB")
def query_audit_entries_by_actor_in_typedb(
    actor_id: str, entity_type: str = "task", limit: int = 50
) -> list:
    """Query TypeDB for all audit entries by a specific actor.

    Enables: 'all tasks changed by agent X' graph query.
    Returns list of dicts with entity_id and action_type.
    """
    actor_escaped = actor_id.replace("\\", "\\\\").replace('"', '\\"')
    type_escaped = entity_type.replace("\\", "\\\\").replace('"', '\\"')
    driver = _get_driver()
    try:
        query = (
            f'match $a isa audit-entry, has audit-actor-id "{actor_escaped}", '
            f'has audit-entity-type "{type_escaped}", '
            f"has audit-entity-id $eid, has audit-action-type $act; "
            f"select $eid, $act;"
        )
        rows = _read_tx(driver, query)
        results = []
        for row in rows[:limit]:
            results.append(
                {
                    "audit-entity-id": _concept_to_value(row.get("eid")),
                    "audit-action-type": _concept_to_value(row.get("act")),
                }
            )
        # Deduplicate entity IDs for summary
        unique_entities = list(set(r["audit-entity-id"] for r in results))
        logger.info(
            f"Found {len(results)} audit entries by actor {actor_id} "
            f"across {len(unique_entities)} entities in TypeDB"
        )
        return results
    finally:
        driver.close()


@keyword("Query Task Audit Via Relation In TypeDB")
def query_task_audit_via_relation_in_typedb(
    task_id: str, limit: int = 50
) -> list:
    """Query TypeDB for audit entries via task-audit relation (graph traversal).

    This proves the relation was created, not just the entity.
    """
    task_id_escaped = task_id.replace("\\", "\\\\").replace('"', '\\"')
    driver = _get_driver()
    try:
        query = (
            f'match $t isa task, has task-id "{task_id_escaped}"; '
            f"(audited-task: $t, task-audit-entry: $a) isa task-audit; "
            f"$a has audit-entry-id $id, has audit-action-type $act; "
            f"select $id, $act;"
        )
        rows = _read_tx(driver, query)
        results = []
        for row in rows[:limit]:
            results.append(
                {
                    "audit-entry-id": _concept_to_value(row.get("id")),
                    "audit-action-type": _concept_to_value(row.get("act")),
                }
            )
        logger.info(
            f"Found {len(results)} audit entries via task-audit relation "
            f"for task {task_id} in TypeDB"
        )
        return results
    finally:
        driver.close()


@keyword("Audit Entry Should Exist In TypeDB")
def audit_entry_should_exist_in_typedb(audit_entry_id: str) -> dict:
    """Assert audit entry exists in TypeDB. Fails if not found."""
    result = query_audit_entry_in_typedb(audit_entry_id)
    if not result:
        raise AssertionError(
            f"Audit entry {audit_entry_id} NOT found in TypeDB "
            f"-- dual-write did not persist"
        )
    logger.info(f"VERIFIED: Audit entry {audit_entry_id} exists in TypeDB")
    return result


@keyword("Audit Entry Should Not Exist In TypeDB")
def audit_entry_should_not_exist_in_typedb(audit_entry_id: str):
    """Assert audit entry does NOT exist in TypeDB."""
    result = query_audit_entry_in_typedb(audit_entry_id)
    if result:
        raise AssertionError(
            f"Audit entry {audit_entry_id} unexpectedly found in TypeDB"
        )


@keyword("TypeDB Should Have Audit Entries For Entity")
def typedb_should_have_audit_entries_for_entity(
    entity_id: str, min_count: int = 1
):
    """Assert TypeDB has at least min_count audit entries for entity."""
    entries = query_audit_entries_for_entity_in_typedb(entity_id)
    if len(entries) < int(min_count):
        raise AssertionError(
            f"Expected >= {min_count} TypeDB audit entries for {entity_id}, "
            f"got {len(entries)}"
        )
    logger.info(
        f"VERIFIED: {len(entries)} audit entries for {entity_id} in TypeDB"
    )
    return entries


@keyword("Delete Audit Entries From TypeDB")
def delete_audit_entries_from_typedb(entity_id: str) -> int:
    """Delete all audit entries for an entity from TypeDB. For test cleanup."""
    from typedb.driver import TransactionType

    entity_id_escaped = entity_id.replace("\\", "\\\\").replace('"', '\\"')
    database = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")
    driver = _get_driver()
    try:
        # Count first
        count_q = (
            f'match $a isa audit-entry, has audit-entity-id '
            f'"{entity_id_escaped}"; select $a;'
        )
        rows = _read_tx(driver, count_q)
        count = len(rows)

        if count > 0:
            with driver.transaction(database, TransactionType.WRITE) as tx:
                delete_q = (
                    f'match $a isa audit-entry, has audit-entity-id '
                    f'"{entity_id_escaped}"; delete $a;'
                )
                tx.query(delete_q).resolve()
                tx.commit()
            logger.info(
                f"Deleted {count} audit entries for {entity_id} from TypeDB"
            )
        return count
    except Exception as e:
        logger.warn(f"Failed to delete audit entries for {entity_id}: {e}")
        return 0
    finally:
        driver.close()
