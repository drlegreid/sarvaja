"""
Session Sync Operations (TypeDB and ChromaDB).

Per RULE-032: Modularized from session_collector.py (591 lines).
Contains: TypeDB and ChromaDB synchronization methods.
"""

import logging
import os
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

from .models import Decision, Task, TYPEDB_AVAILABLE

if TYPE_CHECKING:
    pass


class SessionSyncMixin:
    """
    Mixin class providing sync methods for SessionCollector.

    Requires the following attributes on the parent class:
    - session_id: str
    - topic: str
    - session_type: str
    - start_time: datetime
    - decisions: List[Decision]
    - tasks: List[Task]
    - events: List[SessionEvent]
    - typedb_host: str
    - typedb_port: int
    - typedb_database: str
    """

    def sync_to_chromadb(self) -> bool:
        """
        Sync session summary to ChromaDB for semantic search.

        Returns:
            True if sync successful
        """
        try:
            import chromadb

            host = os.getenv("CHROMADB_HOST", "localhost")
            port = int(os.getenv("CHROMADB_PORT", "8001"))

            client = chromadb.HttpClient(host=host, port=port)
            collection = client.get_or_create_collection("sim_ai_sessions")

            # Create session summary
            summary = self._generate_summary()

            # Upsert to ChromaDB
            collection.upsert(
                ids=[self.session_id],
                documents=[summary],
                metadatas=[{
                    "session_type": self.session_type,
                    "topic": self.topic,
                    "start_time": self.start_time.isoformat(),
                    "decisions_count": len(self.decisions),
                    "tasks_count": len(self.tasks),
                    "events_count": len(self.events)
                }]
            )

            return True

        except Exception as e:
            self.capture_error(f"ChromaDB sync failed: {e}")
            return False

    def _generate_summary(self) -> str:
        """Generate text summary for semantic indexing."""
        parts = [
            f"Session: {self.session_id}",
            f"Topic: {self.topic}",
            f"Type: {self.session_type}",
        ]

        if self.decisions:
            parts.append("Decisions: " + ", ".join(d.name for d in self.decisions))

        if self.tasks:
            parts.append("Tasks: " + ", ".join(t.name for t in self.tasks))

        # Include key event content
        key_events = [e for e in self.events if e.event_type in ("decision", "task")]
        if key_events:
            parts.append("Key events: " + "; ".join(e.content for e in key_events[:5]))

        return " | ".join(parts)

    def _index_decision_to_typedb(self, decision: Decision) -> bool:
        """Index decision to TypeDB."""
        if not TYPEDB_AVAILABLE:
            return False

        try:
            from governance.client import TypeDBClient

            client = TypeDBClient(
                host=self.typedb_host,
                port=self.typedb_port,
                database=self.typedb_database
            )

            if not client.connect():
                return False

            # Insert decision via TypeQL
            query = f'''
                insert $d isa decision,
                    has decision-id "{decision.id}",
                    has decision-name "{decision.name}",
                    has context "{decision.context}",
                    has rationale "{decision.rationale}",
                    has decision-status "{decision.status}";
            '''

            client.execute_query(query)
            client.close()
            return True

        except Exception as e:
            logger.debug(f"Failed to index decision to TypeDB: {e}")
            return False

    def _index_task_to_typedb(self, task: Task) -> bool:
        """
        Index task to TypeDB with session linkage.

        Per GAP-DATA-002: Tasks linked to sessions via completed-in relation.
        Creates work-session if not exists, then links task.
        """
        if not TYPEDB_AVAILABLE:
            return False

        try:
            from governance.client import TypeDBClient

            client = TypeDBClient(
                host=self.typedb_host,
                port=self.typedb_port,
                database=self.typedb_database
            )

            if not client.connect():
                return False

            # First ensure work-session exists
            session_query = f'''
                match $s isa work-session, has session-id "{self.session_id}";
                select $s;
            '''
            existing_session = client.execute_query(session_query)

            if not existing_session:
                # Create work-session
                create_session_query = f'''
                    insert $s isa work-session,
                        has session-id "{self.session_id}",
                        has session-name "{self.topic}",
                        has session-description "Session for {self.session_type}";
                '''
                client.execute_query(create_session_query)

            # Insert or update task with session link
            task_name_escaped = task.name.replace('"', '\\"')
            task_desc_escaped = task.description.replace('"', '\\"') if task.description else ""

            # Check if task exists
            task_check = f'''
                match $t isa task, has task-id "{task.id}";
                select $t;
            '''
            existing_task = client.execute_query(task_check)

            if not existing_task:
                # Insert new task
                insert_task_query = f'''
                    insert $t isa task,
                        has task-id "{task.id}",
                        has task-name "{task_name_escaped}",
                        has task-status "{task.status}",
                        has phase "SESSION";
                '''
                client.execute_query(insert_task_query)

            # Create completed-in relation (session-task link)
            link_query = f'''
                match
                    $t isa task, has task-id "{task.id}";
                    $s isa work-session, has session-id "{self.session_id}";
                insert
                    (completed-task: $t, hosting-session: $s) isa completed-in;
            '''
            client.execute_query(link_query)

            client.close()
            return True

        except Exception as e:
            logger.debug(f"Failed to index task to TypeDB: {e}")
            return False
