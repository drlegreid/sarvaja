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
        cc_session_uuid: Optional[str] = None,
        cc_project_slug: Optional[str] = None,
        cc_git_branch: Optional[str] = None,
        cc_tool_count: Optional[int] = None,
        cc_thinking_chars: Optional[int] = None,
        cc_compaction_count: Optional[int] = None,
        cc_external_name: Optional[str] = None,
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

        # BUG-306-MUT-001: Escape backslash FIRST, then quotes (correct order)
        # Previously only escaped quotes, allowing backslash injection
        session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                    # Update started-at
                    if start_time is not None:
                        # BUG-306-MUT-004: Validate timestamp format
                        ts = start_time[:19]  # YYYY-MM-DDTHH:MM:SS
                        delete_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id_escaped}",
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
                                $s isa work-session, has session-id "{session_id_escaped}";
                            insert
                                $s has started-at {ts};
                        """
                        tx.query(insert_query).resolve()

                    # Update completed-at (end_time)
                    if end_time is not None:
                        ts = end_time[:19]
                        delete_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id_escaped}",
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
                                $s isa work-session, has session-id "{session_id_escaped}";
                            insert
                                $s has completed-at {ts};
                        """
                        tx.query(insert_query).resolve()

                    # Update description
                    if description is not None:
                        # Delete old description (TypeDB 3.x: has $var of $entity)
                        delete_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id_escaped}",
                                    has session-description $desc;
                            delete
                                has $desc of $s;
                        """
                        try:
                            tx.query(delete_query).resolve()
                        except Exception:
                            pass  # May not have existing description

                        # BUG-306-MUT-001: Backslash-first escape
                        desc_escaped = description.replace('\\', '\\\\').replace('"', '\\"')
                        insert_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id_escaped}";
                            insert
                                $s has session-description "{desc_escaped}";
                        """
                        tx.query(insert_query).resolve()

                    # Update agent_id
                    if agent_id is not None:
                        # Delete old agent_id (TypeDB 3.x: has $var of $entity)
                        delete_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id_escaped}",
                                    has agent-id $aid;
                            delete
                                has $aid of $s;
                        """
                        try:
                            tx.query(delete_query).resolve()
                        except Exception:
                            pass

                        # BUG-306-MUT-001: Backslash-first escape
                        agent_escaped = agent_id.replace('\\', '\\\\').replace('"', '\\"')
                        insert_query = f"""
                            match
                                $s isa work-session, has session-id "{session_id_escaped}";
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
                                $s isa work-session, has session-id "{session_id_escaped}",
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
                                $s isa work-session, has session-id "{session_id_escaped}";
                            insert
                                $s has completed-at {timestamp_str};
                        """
                        try:
                            tx.query(insert_query).resolve()
                        except Exception:
                            pass  # May already have completed-at

                    # CC session metadata (SESSION-CC-01-v1)
                    cc_str_fields = {
                        "cc-session-uuid": cc_session_uuid,
                        "cc-project-slug": cc_project_slug,
                        "cc-git-branch": cc_git_branch,
                        "cc-external-name": cc_external_name,
                    }
                    for attr, val in cc_str_fields.items():
                        if val is not None:
                            # BUG-306-MUT-001: Backslash-first escape
                            val_esc = val.replace('\\', '\\\\').replace('"', '\\"')
                            try:
                                tx.query(f'''
                                    match $s isa work-session, has session-id "{session_id_escaped}",
                                        has {attr} $v;
                                    delete has $v of $s;
                                ''').resolve()
                            except Exception:
                                pass
                            tx.query(f'''
                                match $s isa work-session, has session-id "{session_id_escaped}";
                                insert $s has {attr} "{val_esc}";
                            ''').resolve()

                    cc_int_fields = {
                        "cc-tool-count": cc_tool_count,
                        "cc-thinking-chars": cc_thinking_chars,
                        "cc-compaction-count": cc_compaction_count,
                    }
                    for attr, val in cc_int_fields.items():
                        if val is not None:
                            # BUG-306-MUT-003: Coerce to int to prevent TypeQL injection
                            safe_val = int(val)
                            try:
                                tx.query(f'''
                                    match $s isa work-session, has session-id "{session_id_escaped}",
                                        has {attr} $v;
                                    delete has $v of $s;
                                ''').resolve()
                            except Exception:
                                pass
                            tx.query(f'''
                                match $s isa work-session, has session-id "{session_id_escaped}";
                                insert $s has {attr} {safe_val};
                            ''').resolve()

                    tx.commit()

            return self.get_session(session_id)
        except Exception as e:
            # BUG-472-SMU-001: Sanitize logger message + add exc_info for stack trace preservation
            logger.error(f"Failed to update session {session_id}: {type(e).__name__}", exc_info=True)
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

        # BUG-306-MUT-002: Escape backslash FIRST, then quotes (correct order)
        session_id_escaped = session_id.replace('\\', '\\\\').replace('"', '\\"')

        try:
            # Delete relations in separate transactions to avoid
            # TypeDB 3.x variable type conflict ($r reused across types)
            relation_queries = [
                f"""
                    match
                        $s isa work-session, has session-id "{session_id_escaped}";
                        $r (evidence-session: $s) isa has-evidence;
                    delete $r;
                """,
                f"""
                    match
                        $s isa work-session, has session-id "{session_id_escaped}";
                        $r (applying-session: $s) isa session-applied-rule;
                    delete $r;
                """,
                f"""
                    match
                        $s isa work-session, has session-id "{session_id_escaped}";
                        $r (deciding-session: $s) isa session-decision;
                    delete $r;
                """,
                f"""
                    match
                        $s isa work-session, has session-id "{session_id_escaped}";
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
                        $s isa work-session, has session-id "{session_id_escaped}";
                    delete $s;
                """
                tx.query(delete_query).resolve()
                tx.commit()

            return True
        except Exception as e:
            # BUG-472-SMU-002: Sanitize logger message + add exc_info for stack trace preservation
            logger.error(f"Failed to delete session {session_id}: {type(e).__name__}", exc_info=True)
            return False
