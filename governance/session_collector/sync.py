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
            metadata = {
                "session_type": self.session_type,
                "topic": self.topic,
                "start_time": self.start_time.isoformat(),
                "decisions_count": len(self.decisions),
                "tasks_count": len(self.tasks),
                "events_count": len(self.events),
            }
            # A.4: Include agent_id for session-agent linking
            if getattr(self, "agent_id", None):
                metadata["agent_id"] = self.agent_id

            collection.upsert(
                ids=[self.session_id],
                documents=[summary],
                metadatas=[metadata],
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

        client = None  # BUG-267-SYNC-001: Track for finally block (matches _index_task_to_typedb)
        try:
            from governance.client import TypeDBClient

            client = TypeDBClient(
                host=self.typedb_host,
                port=self.typedb_port,
                database=self.typedb_database
            )

            if not client.connect():
                return False

            # BUG-TYPEDB-INJECTION-003 + BUG-233-SYN-001: Escape backslash THEN quotes
            # BUG-293-SYN-001: Guard against None fields from TypeDB Decision class
            def _esc(val) -> str:
                if val is None:
                    return ""
                return str(val).replace('\\', '\\\\').replace('"', '\\"')
            id_escaped = _esc(decision.id)
            name_escaped = _esc(decision.name)
            context_escaped = _esc(decision.context)
            rationale_escaped = _esc(decision.rationale)
            status_escaped = _esc(decision.status)

            # Insert decision via TypeQL
            query = f'''
                insert $d isa decision,
                    has decision-id "{id_escaped}",
                    has decision-name "{name_escaped}",
                    has context "{context_escaped}",
                    has rationale "{rationale_escaped}",
                    has decision-status "{status_escaped}";
            '''

            client.execute_query(query)
            return True

        except Exception as e:
            logger.debug(f"Failed to index decision to TypeDB: {e}")
            return False
        finally:
            # BUG-233-SYN-002: Always close client, even on exception
            # BUG-267-SYNC-001: Check client is not None before close
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass

    def _index_task_to_typedb(self, task: Task) -> bool:
        """
        Index task to TypeDB with session linkage.

        Per GAP-DATA-002: Tasks linked to sessions via completed-in relation.
        Creates work-session if not exists, then links task.
        """
        if not TYPEDB_AVAILABLE:
            return False

        client = None  # BUG-248-SYN-002: Track for finally block
        try:
            from governance.client import TypeDBClient

            client = TypeDBClient(
                host=self.typedb_host,
                port=self.typedb_port,
                database=self.typedb_database
            )

            if not client.connect():
                return False

            # BUG-248-SYN-003: Consistent _esc() helper (matches _index_decision_to_typedb)
            # BUG-293-SYN-001: Guard against None fields from TypeDB Task class
            def _esc(val) -> str:
                if val is None:
                    return ""
                return str(val).replace('\\', '\\\\').replace('"', '\\"')

            # First ensure work-session exists
            session_id_escaped = _esc(self.session_id)
            session_query = f'''
                match $s isa work-session, has session-id "{session_id_escaped}";
                select $s;
            '''
            existing_session = client.execute_query(session_query)

            if not existing_session:
                # Create work-session with agent_id (A.4: session-agent linking)
                agent_part = ""
                if getattr(self, "agent_id", None):
                    # BUG-248-SYN-004: Use _esc for agent_id
                    agent_escaped = _esc(self.agent_id)
                    agent_part = f',\n                        has agent-id "{agent_escaped}"'
                topic_escaped = _esc(self.topic)
                type_escaped = _esc(self.session_type)
                create_session_query = f'''
                    insert $s isa work-session,
                        has session-id "{session_id_escaped}",
                        has session-name "{topic_escaped}",
                        has session-description "Session for {type_escaped}"{agent_part};
                '''
                client.execute_query(create_session_query)

            # Insert or update task with session link
            task_name_escaped = _esc(task.name)
            task_id_escaped = _esc(task.id)
            task_check = f'''
                match $t isa task, has task-id "{task_id_escaped}";
                select $t;
            '''
            existing_task = client.execute_query(task_check)

            if not existing_task:
                # Insert new task
                task_status_escaped = _esc(task.status) if task.status else "pending"
                insert_task_query = f'''
                    insert $t isa task,
                        has task-id "{task_id_escaped}",
                        has task-name "{task_name_escaped}",
                        has task-status "{task_status_escaped}",
                        has phase "SESSION";
                '''
                client.execute_query(insert_task_query)

            # BUG-293-SYN-002: Check for existing relation before inserting to prevent duplicates
            relation_check = f'''
                match
                    $t isa task, has task-id "{task_id_escaped}";
                    $s isa work-session, has session-id "{session_id_escaped}";
                    $r (completed-task: $t, hosting-session: $s) isa completed-in;
                select $r;
            '''
            existing_rel = client.execute_query(relation_check)
            if not existing_rel:
                link_query = f'''
                    match
                        $t isa task, has task-id "{task_id_escaped}";
                        $s isa work-session, has session-id "{session_id_escaped}";
                    insert
                        (completed-task: $t, hosting-session: $s) isa completed-in;
                '''
                client.execute_query(link_query)

            return True

        except Exception as e:
            logger.debug(f"Failed to index task to TypeDB: {e}")
            return False
        finally:
            # BUG-248-SYN-002: Always close client to prevent connection leak
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
