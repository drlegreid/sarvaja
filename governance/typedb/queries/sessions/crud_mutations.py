"""
TypeDB Session Mutation Operations (update + delete).

Per DOC-SIZE-01-v1: Extracted from crud.py.
"""

import logging
from datetime import datetime
from typing import Optional

from ...entities import Session

logger = logging.getLogger(__name__)


class SessionMutationOperations:
    """
    Session update/delete operations for TypeDB.

    Requires a client with get_session, _driver, database attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def update_session(
        self,
        session_id: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        tasks_completed: Optional[int] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Optional[Session]:
        """
        Update a session's attributes in TypeDB.

        Per GAP-UI-034: Session CRUD operations.

        Uses delete-then-insert pattern for each optional attribute.
        """
        from typedb.driver import TransactionType

        # Check session exists first
        existing = self.get_session(session_id)
        if not existing:
            return None

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                    # Update started-at
                    if start_time is not None:
                        ts = start_time[:19]  # YYYY-MM-DDTHH:MM:SS
                        delete_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}",
                                    has started-at $sa;
                            delete
                                has $sa of $s;
                        """
                        try:
                            tx.query(delete_query).resolve()
                        except Exception:
                            pass
                        insert_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}";
                            insert
                                $s has started-at {ts};
                        """
                        tx.query(insert_query).resolve()

                    # Update completed-at (end_time)
                    if end_time is not None:
                        ts = end_time[:19]
                        delete_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}",
                                    has completed-at $ca;
                            delete
                                has $ca of $s;
                        """
                        try:
                            tx.query(delete_query).resolve()
                        except Exception:
                            pass
                        insert_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}";
                            insert
                                $s has completed-at {ts};
                        """
                        tx.query(insert_query).resolve()

                    # Update description
                    if description is not None:
                        # Delete old description (TypeDB 3.x: has $var of $entity)
                        delete_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}",
                                    has session-description $desc;
                            delete
                                has $desc of $s;
                        """
                        try:
                            tx.query(delete_query).resolve()
                        except Exception:
                            pass  # May not have existing description

                        # Insert new description
                        desc_escaped = description.replace('"', '\\"')
                        insert_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}";
                            insert
                                $s has session-description "{desc_escaped}";
                        """
                        tx.query(insert_query).resolve()

                    # Update agent_id
                    if agent_id is not None:
                        # Delete old agent_id (TypeDB 3.x: has $var of $entity)
                        delete_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}",
                                    has agent-id $aid;
                            delete
                                has $aid of $s;
                        """
                        try:
                            tx.query(delete_query).resolve()
                        except Exception:
                            pass

                        # Insert new agent_id
                        agent_escaped = agent_id.replace('"', '\\"')
                        insert_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}";
                            insert
                                $s has agent-id "{agent_escaped}";
                        """
                        tx.query(insert_query).resolve()

                    # Update status (complete session if COMPLETED)
                    # Skip if end_time already set completed-at above
                    if status == "COMPLETED" and end_time is None:
                        now = datetime.now()
                        timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                        # Delete existing completed-at first
                        del_q = f"""
                            match
                                $s isa work-session, has session-id "{session_id}",
                                    has completed-at $ca;
                            delete
                                has $ca of $s;
                        """
                        try:
                            tx.query(del_q).resolve()
                        except Exception:
                            pass
                        insert_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}";
                            insert
                                $s has completed-at {timestamp_str};
                        """
                        try:
                            tx.query(insert_query).resolve()
                        except Exception:
                            pass  # May already have completed-at

                    tx.commit()

            return self.get_session(session_id)
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from TypeDB.

        Per GAP-UI-034: Session CRUD operations.
        Per TypeDB 3.x: delete syntax is just `delete $var;`

        Returns:
            True if deleted successfully, False otherwise
        """
        from typedb.driver import TransactionType

        # Check session exists first
        existing = self.get_session(session_id)
        if not existing:
            return False

        try:
            # Delete relations in separate transactions to avoid
            # TypeDB 3.x variable type conflict ($r reused across types)
            relation_queries = [
                f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                        $r (evidence-session: $s) isa has-evidence;
                    delete $r;
                """,
                f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                        $r (applying-session: $s) isa session-applied-rule;
                    delete $r;
                """,
                f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                        $r (deciding-session: $s) isa session-decision;
                    delete $r;
                """,
                f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                        $r (hosting-session: $s) isa completed-in;
                    delete $r;
                """,
            ]

            for query in relation_queries:
                try:
                    with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                        tx.query(query).resolve()
                        tx.commit()
                except Exception:
                    pass  # Relation may not exist

            # Delete the session entity itself
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                delete_query = f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                    delete $s;
                """
                tx.query(delete_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
