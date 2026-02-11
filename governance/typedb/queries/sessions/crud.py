"""
TypeDB Session CRUD Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/sessions.py
Per DOC-SIZE-01-v1: Mutations in crud_mutations.py.

Created: 2026-01-04
"""

import logging
from datetime import datetime
from typing import Optional

from ...entities import Session

# Re-export mutations for backward compatibility
from .crud_mutations import SessionMutationOperations  # noqa: F401

logger = logging.getLogger(__name__)


class SessionCRUDOperations(SessionMutationOperations):
    """
    Session CRUD operations for TypeDB.

    Requires a client with _execute_query, _driver, database, and get_session attributes.
    Uses mixin pattern for TypeDBClient composition.

    insert_session + end_session defined here.
    update_session + delete_session inherited from SessionMutationOperations.
    """

    def insert_session(
        self,
        session_id: str,
        name: str = None,
        description: str = None,
        file_path: str = None,
        agent_id: str = None,
        cc_session_uuid: str = None,
        cc_project_slug: str = None,
        cc_git_branch: str = None,
        cc_tool_count: int = None,
        cc_thinking_chars: int = None,
        cc_compaction_count: int = None,
    ) -> Optional[Session]:
        """
        Insert a new session into TypeDB.

        Per GAP-ARCH-002: Session creation in TypeDB.
        Per SESSION-CC-01-v1: CC session metadata.
        """
        from typedb.driver import TransactionType

        existing = self.get_session(session_id)
        if existing:
            logger.info(f"Session {session_id} already exists, skipping insert")
            return None

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                    insert_parts = [f'has session-id "{session_id}"']

                    if name:
                        name_escaped = name.replace('"', '\\"')
                        insert_parts.append(f'has session-name "{name_escaped}"')
                    if description:
                        desc_escaped = description.replace('"', '\\"')
                        insert_parts.append(f'has session-description "{desc_escaped}"')
                    if file_path:
                        path_escaped = file_path.replace('"', '\\"')
                        insert_parts.append(f'has session-file-path "{path_escaped}"')
                    if agent_id:
                        agent_escaped = agent_id.replace('"', '\\"')
                        insert_parts.append(f'has agent-id "{agent_escaped}"')

                    # CC session metadata (SESSION-CC-01-v1)
                    if cc_session_uuid:
                        insert_parts.append(f'has cc-session-uuid "{cc_session_uuid}"')
                    if cc_project_slug:
                        slug_esc = cc_project_slug.replace('"', '\\"')
                        insert_parts.append(f'has cc-project-slug "{slug_esc}"')
                    if cc_git_branch:
                        branch_esc = cc_git_branch.replace('"', '\\"')
                        insert_parts.append(f'has cc-git-branch "{branch_esc}"')
                    if cc_tool_count is not None:
                        insert_parts.append(f'has cc-tool-count {cc_tool_count}')
                    if cc_thinking_chars is not None:
                        insert_parts.append(f'has cc-thinking-chars {cc_thinking_chars}')
                    if cc_compaction_count is not None:
                        insert_parts.append(f'has cc-compaction-count {cc_compaction_count}')

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
            logger.error(f"Failed to insert session {session_id}: {e}")
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
            logger.error(f"Failed to end session {session_id}: {e}")
            return None
