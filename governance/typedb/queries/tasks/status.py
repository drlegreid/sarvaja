"""
TypeDB Task Status Operations.

Per DOC-SIZE-01-v1: Files under 300 lines.
Extracted from: governance/typedb/queries/tasks/crud.py

Created: 2026-01-14
"""

import logging
from datetime import datetime
from typing import Optional

from ...entities import Task

logger = logging.getLogger(__name__)


def update_task_status(
    client,
    task_id: str,
    status: str,
    agent_id: str = None,
    evidence: str = None,
    resolution: str = None
) -> Optional[Task]:
    """
    Update a task's status (and optionally assign agent, evidence, resolution).

    Per TODO-6: Agent task claiming uses this method.
    Per GAP-UI-046: Status/resolution lifecycle.

    Args:
        client: TypeDB client with _driver, database, get_task attributes
        task_id: Task ID to update
        status: New status (OPEN, IN_PROGRESS, CLOSED per GAP-UI-046)
        agent_id: Optional agent ID to assign
        evidence: Optional completion evidence/notes
        resolution: Optional resolution (NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED)

    Returns:
        Updated Task object or None if not found
    """
    current = client.get_task(task_id)
    if not current:
        return None

    # BUG-297-STS-001: Validate status and resolution against allowlists
    _VALID_STATUSES = {"OPEN", "IN_PROGRESS", "DONE", "CLOSED", "TODO"}
    if status not in _VALID_STATUSES:
        logger.error(f"update_task_status: invalid status {status!r}")
        return None
    _VALID_RESOLUTIONS = {"NONE", "DEFERRED", "IMPLEMENTED", "VALIDATED", "CERTIFIED"}
    if resolution and resolution not in _VALID_RESOLUTIONS:
        logger.error(f"update_task_status: invalid resolution {resolution!r}")
        return None

    from typedb.driver import TransactionType

    # BUG-TYPEQL-ESCAPE-TASK-003: Escape task_id for TypeQL safety
    tid = task_id.replace('\\', '\\\\').replace('"', '\\"')

    try:
        with client._driver.transaction(client.database, TransactionType.WRITE) as tx:
                # BUG-STATUS-ESCAPE-001: Escape all user-provided fields
                status_escaped = status.replace('\\', '\\\\').replace('"', '\\"')

                # BUG-297-STS-002: Only delete old status if it exists; None/empty causes
                # empty-string match that deletes nothing, then insert adds a second attribute
                if current.status:
                    current_status_escaped = current.status.replace('\\', '\\\\').replace('"', '\\"')
                    # Delete old status (TypeDB 3.x: has $var of $entity)
                    delete_query = f"""
                        match
                            $t isa task, has task-id "{tid}", has task-status $s;
                            $s == "{current_status_escaped}";
                        delete
                            has $s of $t;
                    """
                    tx.query(delete_query).resolve()

                # Insert new status
                insert_query = f"""
                    match
                        $t isa task, has task-id "{tid}";
                    insert
                        $t has task-status "{status_escaped}";
                """
                tx.query(insert_query).resolve()

                # Update agent_id if provided (per E2E test requirements)
                if agent_id:
                    agent_id_escaped = agent_id.replace('\\', '\\\\').replace('"', '\\"')
                    # First delete old agent-id if exists
                    if current.agent_id:
                        current_agent_escaped = current.agent_id.replace('\\', '\\\\').replace('"', '\\"')
                        # TypeDB 3.x: has $var of $entity
                        delete_agent_query = f"""
                            match
                                $t isa task, has task-id "{tid}", has agent-id $a;
                                $a == "{current_agent_escaped}";
                            delete
                                has $a of $t;
                        """
                        tx.query(delete_agent_query).resolve()

                    # Insert new agent-id
                    insert_agent_query = f"""
                        match
                            $t isa task, has task-id "{tid}";
                        insert
                            $t has agent-id "{agent_id_escaped}";
                    """
                    tx.query(insert_agent_query).resolve()

                # Update evidence if provided (per E2E test requirements)
                if evidence:
                    evidence_escaped = evidence.replace('\\', '\\\\').replace('"', '\\"')
                    # First delete old evidence if exists (TypeDB 3.x: has $var of $entity)
                    # BUG-341-STATUS-001: Pin evidence value in delete (consistent with
                    # status/agent/resolution delete patterns — prevents deleting ALL evidence)
                    if current.evidence:
                        current_evidence_escaped = current.evidence.replace('\\', '\\\\').replace('"', '\\"')
                        delete_evidence_query = f"""
                            match
                                $t isa task, has task-id "{tid}", has task-evidence $e;
                                $e == "{current_evidence_escaped}";
                            delete
                                has $e of $t;
                        """
                        tx.query(delete_evidence_query).resolve()

                    # Insert new evidence
                    insert_evidence_query = f"""
                        match
                            $t isa task, has task-id "{tid}";
                        insert
                            $t has task-evidence "{evidence_escaped}";
                    """
                    tx.query(insert_evidence_query).resolve()

                # Update resolution if provided (GAP-UI-046)
                if resolution:
                    resolution_escaped = resolution.replace('\\', '\\\\').replace('"', '\\"')
                    # First delete old resolution if exists
                    current_resolution = getattr(current, 'resolution', None)
                    if current_resolution:
                        current_res_escaped = current_resolution.replace('\\', '\\\\').replace('"', '\\"')
                        # TypeDB 3.x: has $var of $entity
                        delete_res_query = f"""
                            match
                                $t isa task, has task-id "{tid}", has task-resolution $r;
                                $r == "{current_res_escaped}";
                            delete
                                has $r of $t;
                        """
                        try:
                            tx.query(delete_res_query).resolve()
                        except Exception as e:
                            # BUG-360-STS-001: Log instead of silently swallowing — connection
                            # errors are actionable even if "not found" is expected
                            logger.debug(f"Resolution delete for {task_id} (expected if absent): {e}")

                    # Insert new resolution
                    insert_res_query = f"""
                        match
                            $t isa task, has task-id "{tid}";
                        insert
                            $t has task-resolution "{resolution_escaped}";
                    """
                    tx.query(insert_res_query).resolve()

                # Auto-reset resolution to NONE when reopening (GAP-UI-046)
                if status in ["OPEN", "IN_PROGRESS"] and not resolution:
                    current_resolution = getattr(current, 'resolution', None)
                    if current_resolution and current_resolution != "NONE":
                        # BUG-375-STS-001: Pin resolution value in delete (consistent with
                        # status/agent/evidence delete patterns — prevents race condition)
                        current_res_reset_escaped = current_resolution.replace('\\', '\\\\').replace('"', '\\"')
                        delete_res_query = f"""
                            match
                                $t isa task, has task-id "{tid}", has task-resolution $r;
                                $r == "{current_res_reset_escaped}";
                            delete
                                has $r of $t;
                        """
                        try:
                            tx.query(delete_res_query).resolve()
                        except Exception as e:
                            # BUG-360-STS-001: Log instead of silently swallowing
                            logger.debug(f"Resolution reset delete for {task_id} (expected if absent): {e}")
                        insert_res_query = f"""
                            match
                                $t isa task, has task-id "{tid}";
                            insert
                                $t has task-resolution "NONE";
                        """
                        tx.query(insert_res_query).resolve()

                # Set claimed_at when status is IN_PROGRESS (GAP-UI-035)
                if status == "IN_PROGRESS" and not current.claimed_at:
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                    # TypeDB datetime: no quotes (value datetime in schema)
                    insert_claimed_query = f"""
                        match
                            $t isa task, has task-id "{tid}";
                        insert
                            $t has task-claimed-at {timestamp_str};
                    """
                    tx.query(insert_claimed_query).resolve()

                # Set completed_at when status is DONE/CLOSED (per E2E test requirements, GAP-UI-046)
                if status in ["DONE", "CLOSED"] and not current.completed_at:
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                    # TypeDB datetime: no quotes (value datetime in schema)
                    insert_completed_query = f"""
                        match
                            $t isa task, has task-id "{tid}";
                        insert
                            $t has task-completed-at {timestamp_str};
                    """
                    tx.query(insert_completed_query).resolve()

                tx.commit()

        return client.get_task(task_id)
    except Exception as e:
        # BUG-397-STS-001: Add exc_info for stack trace preservation
        logger.error(f"Failed to update task {task_id}: {e}", exc_info=True)
        return None
