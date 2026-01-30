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

    from typedb.driver import TransactionType

    try:
        with client._driver.transaction(client.database, TransactionType.WRITE) as tx:
                # Delete old status (TypeDB 3.x: has $var of $entity)
                delete_query = f"""
                    match
                        $t isa task, has task-id "{task_id}", has task-status $s;
                        $s == "{current.status}";
                    delete
                        has $s of $t;
                """
                tx.query(delete_query).resolve()

                # Insert new status
                insert_query = f"""
                    match
                        $t isa task, has task-id "{task_id}";
                    insert
                        $t has task-status "{status}";
                """
                tx.query(insert_query).resolve()

                # Update agent_id if provided (per E2E test requirements)
                if agent_id:
                    # First delete old agent-id if exists
                    if current.agent_id:
                        # TypeDB 3.x: has $var of $entity
                        delete_agent_query = f"""
                            match
                                $t isa task, has task-id "{task_id}", has agent-id $a;
                                $a == "{current.agent_id}";
                            delete
                                has $a of $t;
                        """
                        tx.query(delete_agent_query).resolve()

                    # Insert new agent-id
                    insert_agent_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has agent-id "{agent_id}";
                    """
                    tx.query(insert_agent_query).resolve()

                # Update evidence if provided (per E2E test requirements)
                if evidence:
                    evidence_escaped = evidence.replace('"', '\\"')
                    # First delete old evidence if exists (TypeDB 3.x: has $var of $entity)
                    if current.evidence:
                        delete_evidence_query = f"""
                            match
                                $t isa task, has task-id "{task_id}", has task-evidence $e;
                            delete
                                has $e of $t;
                        """
                        tx.query(delete_evidence_query).resolve()

                    # Insert new evidence
                    insert_evidence_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-evidence "{evidence_escaped}";
                    """
                    tx.query(insert_evidence_query).resolve()

                # Update resolution if provided (GAP-UI-046)
                if resolution:
                    # First delete old resolution if exists
                    current_resolution = getattr(current, 'resolution', None)
                    if current_resolution:
                        # TypeDB 3.x: has $var of $entity
                        delete_res_query = f"""
                            match
                                $t isa task, has task-id "{task_id}", has task-resolution $r;
                                $r == "{current_resolution}";
                            delete
                                has $r of $t;
                        """
                        try:
                            tx.query(delete_res_query).resolve()
                        except Exception:
                            pass  # Might not exist

                    # Insert new resolution
                    insert_res_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-resolution "{resolution}";
                    """
                    tx.query(insert_res_query).resolve()

                # Auto-reset resolution to NONE when reopening (GAP-UI-046)
                if status in ["OPEN", "IN_PROGRESS"] and not resolution:
                    current_resolution = getattr(current, 'resolution', None)
                    if current_resolution and current_resolution != "NONE":
                        # TypeDB 3.x: has $var of $entity
                        delete_res_query = f"""
                            match
                                $t isa task, has task-id "{task_id}", has task-resolution $r;
                            delete
                                has $r of $t;
                        """
                        try:
                            tx.query(delete_res_query).resolve()
                        except Exception:
                            pass
                        insert_res_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has task-resolution "NONE";
                        """
                        tx.query(insert_res_query).resolve()

                # Set claimed_at when status is IN_PROGRESS (GAP-UI-035)
                if status == "IN_PROGRESS" and not current.claimed_at:
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                    insert_claimed_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-claimed-at {timestamp_str};
                    """
                    tx.query(insert_claimed_query).resolve()

                # Set completed_at when status is DONE/CLOSED (per E2E test requirements, GAP-UI-046)
                if status in ["DONE", "CLOSED"] and not current.completed_at:
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                    insert_completed_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-completed-at {timestamp_str};
                    """
                    tx.query(insert_completed_query).resolve()

                tx.commit()

        return client.get_task(task_id)
    except Exception as e:
        logger.error(f"Failed to update task {task_id}: {e}")
        return None
