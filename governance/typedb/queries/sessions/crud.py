"""
TypeDB Session CRUD Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/sessions.py

Created: 2026-01-04
"""

from datetime import datetime
from typing import Optional

from ...entities import Session


class SessionCRUDOperations:
    """
    Session CRUD operations for TypeDB.

    Requires a client with _execute_query, _driver, database, and get_session attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def insert_session(
        self,
        session_id: str,
        name: str = None,
        description: str = None,
        file_path: str = None,
        agent_id: str = None
    ) -> Optional[Session]:
        """
        Insert a new session into TypeDB.

        Per GAP-ARCH-002: Session creation in TypeDB.

        Note: Checks for existing session first to prevent duplicates.
        """
        from typedb.driver import TransactionType

        # Check if session already exists
        existing = self.get_session(session_id)
        if existing:
            # Session already exists, return None to indicate conflict
            print(f"Session {session_id} already exists, skipping insert")
            return None

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                    # Build insert parts
                    insert_parts = [f'has session-id "{session_id}"']

                    if name:
                        insert_parts.append(f'has session-name "{name}"')
                    if description:
                        desc_escaped = description.replace('"', '\\"')
                        insert_parts.append(f'has session-description "{desc_escaped}"')
                    if file_path:
                        insert_parts.append(f'has session-file-path "{file_path}"')
                    if agent_id:
                        insert_parts.append(f'has agent-id "{agent_id}"')

                    # Add started-at timestamp (TypeDB datetime format: YYYY-MM-DDTHH:MM:SS)
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                    insert_parts.append(f'has started-at {timestamp_str}')

                    insert_query = f"""
                        insert $s isa work-session,
                            {", ".join(insert_parts)};
                    """
                    tx.query(insert_query).resolve()
                    tx.commit()

            return self.get_session(session_id)
        except Exception as e:
            print(f"Failed to insert session {session_id}: {e}")
            return None

    def end_session(self, session_id: str) -> Optional[Session]:
        """End a session by setting completed-at timestamp."""
        from typedb.driver import TransactionType

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                    # TypeDB datetime format: YYYY-MM-DDTHH:MM:SS (no microseconds, no trailing T)
                    now = datetime.now()
                    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                    insert_query = f"""
                        match
                            $s isa work-session, has session-id "{session_id}";
                        insert
                            $s has completed-at {timestamp_str};
                    """
                    tx.query(insert_query).resolve()
                    tx.commit()

            return self.get_session(session_id)
        except Exception as e:
            print(f"Failed to end session {session_id}: {e}")
            return None

    def update_session(
        self,
        session_id: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        tasks_completed: Optional[int] = None,
        agent_id: Optional[str] = None
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
                        insert_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id}";
                            insert
                                $s has agent-id "{agent_id}";
                        """
                        tx.query(insert_query).resolve()

                    # Update status (complete session if COMPLETED)
                    if status == "COMPLETED":
                        now = datetime.now()
                        timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
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
            print(f"Failed to update session {session_id}: {e}")
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
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Delete all relations first (has-evidence, session-applied-rule, etc.)
                # Delete has-evidence relations
                del_evidence = f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                        $r (evidence-session: $s) isa has-evidence;
                    delete $r;
                """
                try:
                    tx.query(del_evidence).resolve()
                except Exception:
                    pass

                # Delete session-applied-rule relations
                del_rules = f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                        $r (applying-session: $s) isa session-applied-rule;
                    delete $r;
                """
                try:
                    tx.query(del_rules).resolve()
                except Exception:
                    pass

                # Delete session-decision relations
                del_decisions = f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                        $r (deciding-session: $s) isa session-decision;
                    delete $r;
                """
                try:
                    tx.query(del_decisions).resolve()
                except Exception:
                    pass

                # Delete the session entity itself
                delete_query = f"""
                    match
                        $s isa work-session, has session-id "{session_id}";
                    delete $s;
                """
                tx.query(delete_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            print(f"Failed to delete session {session_id}: {e}")
            return False
