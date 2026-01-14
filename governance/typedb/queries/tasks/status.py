"""
TypeDB Task Status Operations.

Per DOC-SIZE-01-v1: Files under 300 lines.
Extracted from: governance/typedb/queries/tasks/crud.py

Created: 2026-01-14
"""

from datetime import datetime
from typing import Optional

from ...entities import Task


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
        client: TypeDB client with _client, database, get_task attributes
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

    from typedb.driver import SessionType, TransactionType

    try:
        with client._client.session(client.database, SessionType.DATA) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                # Delete old status
                delete_query = f"""
                    match
                        $t isa task, has task-id "{task_id}";
                        $a isa task-status; $a "{current.status}";
                        $t has $a;
                    delete
                        $t has $a;
                """
                tx.query.delete(delete_query)

                # Insert new status
                insert_query = f"""
                    match
                        $t isa task, has task-id "{task_id}";
                    insert
                        $t has task-status "{status}";
                """
                tx.query.insert(insert_query)

                # Update agent_id if provided (per E2E test requirements)
                if agent_id:
                    # First delete old agent-id if exists
                    if current.agent_id:
                        delete_agent_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                                $a isa agent-id; $a "{current.agent_id}";
                                $t has $a;
                            delete
                                $t has $a;
                        """
                        tx.query.delete(delete_agent_query)

                    # Insert new agent-id
                    insert_agent_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has agent-id "{agent_id}";
                    """
                    tx.query.insert(insert_agent_query)

                # Update evidence if provided (per E2E test requirements)
                if evidence:
                    evidence_escaped = evidence.replace('"', '\\"')
                    # First delete old evidence if exists
                    if current.evidence:
                        delete_evidence_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                                $e isa task-evidence; $t has $e;
                            delete
                                $t has $e;
                        """
                        tx.query.delete(delete_evidence_query)

                    # Insert new evidence
                    insert_evidence_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-evidence "{evidence_escaped}";
                    """
                    tx.query.insert(insert_evidence_query)

                # Update resolution if provided (GAP-UI-046)
                if resolution:
                    # First delete old resolution if exists
                    current_resolution = getattr(current, 'resolution', None)
                    if current_resolution:
                        delete_res_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                                $r isa task-resolution; $r "{current_resolution}";
                                $t has $r;
                            delete
                                $t has $r;
                        """
                        try:
                            tx.query.delete(delete_res_query)
                        except Exception:
                            pass  # Might not exist

                    # Insert new resolution
                    insert_res_query = f"""
                        match
                            $t isa task, has task-id "{task_id}";
                        insert
                            $t has task-resolution "{resolution}";
                    """
                    tx.query.insert(insert_res_query)

                # Auto-reset resolution to NONE when reopening (GAP-UI-046)
                if status in ["OPEN", "IN_PROGRESS"] and not resolution:
                    current_resolution = getattr(current, 'resolution', None)
                    if current_resolution and current_resolution != "NONE":
                        delete_res_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                                $r isa task-resolution; $t has $r;
                            delete
                                $t has $r;
                        """
                        try:
                            tx.query.delete(delete_res_query)
                        except Exception:
                            pass
                        insert_res_query = f"""
                            match
                                $t isa task, has task-id "{task_id}";
                            insert
                                $t has task-resolution "NONE";
                        """
                        tx.query.insert(insert_res_query)

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
                    tx.query.insert(insert_claimed_query)

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
                    tx.query.insert(insert_completed_query)

                tx.commit()

        return client.get_task(task_id)
    except Exception as e:
        print(f"Failed to update task {task_id}: {e}")
        return None
