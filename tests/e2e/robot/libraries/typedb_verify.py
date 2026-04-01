"""
TypeDB Direct Verification Library
====================================
Per SRVJ-BUG-TYPEDB-WRITE-01: E2E assertions MUST query TypeDB directly,
bypassing the service layer. API-level persistence_status is the service's
*claim* — this library verifies the *reality*.

Usage in Robot:
    Library    ../libraries/typedb_verify.py
    ${result}=    Query Task In TypeDB    SRVJ-TEST-001
    Should Not Be Empty    ${result}
    Should Be Equal    ${result}[task-layer]    api
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


def _extract_attrs(tx, task_var):
    """Fetch all string/datetime attributes for a task entity via TypeDB."""
    attr_names = [
        "task-id", "task-name", "task-status", "phase", "task-priority",
        "task-type", "task-summary", "task-body", "task-layer",
        "task-concern", "task-method", "agent-id", "task-resolution",
        "resolution-notes", "task-evidence", "gap-reference",
    ]
    result = {}
    for attr in attr_names:
        try:
            q = (
                f'match $t isa task, has task-id "{task_var}", '
                f'has {attr} $a; select $a;'
            )
            rows = list(tx.query(q).resolve())
            if rows:
                val = rows[0].get("a")
                result[attr] = val.as_string() if hasattr(val, "as_string") else str(val)
        except Exception:
            pass  # attribute not set on this task
    return result


@keyword("Query Task In TypeDB")
def query_task_in_typedb(task_id: str) -> dict:
    """Query TypeDB directly for a task by ID. Returns dict of attributes or empty dict."""
    database = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")
    driver = _get_driver()
    try:
        from typedb.driver import TransactionType

        with driver.transaction(database, TransactionType.READ) as tx:
            # Check task exists
            check = list(tx.query(
                f'match $t isa task, has task-id "{task_id}";'
            ).resolve())
            if not check:
                logger.info(f"Task {task_id} NOT found in TypeDB")
                return {}
            logger.info(f"Task {task_id} found in TypeDB — extracting attributes")
            return _extract_attrs(tx, task_id)
    finally:
        driver.close()


@keyword("Task Should Exist In TypeDB")
def task_should_exist_in_typedb(task_id: str) -> dict:
    """Assert task exists in TypeDB. Returns attributes dict. Fails if not found."""
    result = query_task_in_typedb(task_id)
    if not result:
        raise AssertionError(
            f"Task {task_id} NOT found in TypeDB — write did not persist"
        )
    logger.info(f"VERIFIED: Task {task_id} exists in TypeDB with {len(result)} attributes")
    return result


@keyword("Task Should Not Exist In TypeDB")
def task_should_not_exist_in_typedb(task_id: str):
    """Assert task does NOT exist in TypeDB (e.g. after delete)."""
    result = query_task_in_typedb(task_id)
    if result:
        raise AssertionError(
            f"Task {task_id} unexpectedly found in TypeDB with attrs: {result}"
        )


@keyword("TypeDB Task Attribute Should Be")
def typedb_task_attribute_should_be(task_id: str, attr_name: str, expected: str):
    """Assert a specific TypeDB attribute matches expected value."""
    result = query_task_in_typedb(task_id)
    if not result:
        raise AssertionError(f"Task {task_id} not found in TypeDB")
    actual = result.get(attr_name)
    if actual is None:
        raise AssertionError(
            f"Task {task_id} has no attribute '{attr_name}' in TypeDB. "
            f"Available: {list(result.keys())}"
        )
    if actual != expected:
        raise AssertionError(
            f"TypeDB attribute '{attr_name}' mismatch for {task_id}: "
            f"expected '{expected}', got '{actual}'"
        )
    logger.info(f"VERIFIED: {task_id}.{attr_name} = '{expected}' in TypeDB")


@keyword("Delete Task From TypeDB")
def delete_task_from_typedb(task_id: str) -> bool:
    """Delete a task directly from TypeDB. For test cleanup."""
    database = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")
    driver = _get_driver()
    try:
        from typedb.driver import TransactionType

        with driver.transaction(database, TransactionType.WRITE) as tx:
            tx.query(f'match $t isa task, has task-id "{task_id}"; delete $t;').resolve()
            tx.commit()
            logger.info(f"Deleted task {task_id} from TypeDB")
            return True
    except Exception as e:
        logger.warn(f"Failed to delete {task_id} from TypeDB: {e}")
        return False
    finally:
        driver.close()
