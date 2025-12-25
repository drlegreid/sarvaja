"""
Session Evidence Collector - P4.2 Cross-Workspace Integration

Collects and routes session evidence to appropriate stores:
- Decisions → TypeDB (typed relations, inference)
- Tasks → TypeDB (task graph, dependencies)
- Summaries → ChromaDB (semantic search)
- Session Logs → Markdown (human-readable archive)

Created: 2024-12-24 (Phase 4.2)
Per: RULE-001 (Session Evidence), RULE-006 (Decision Logging)
Design: docs/STRATEGIC-SESSION-FLOW.md
"""

import os
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Import TypeDB client for evidence indexing
try:
    from governance.client import TypeDBClient, Decision
    TYPEDB_AVAILABLE = True
except ImportError:
    TYPEDB_AVAILABLE = False
    # Stub for when TypeDB not available
    @dataclass
    class Decision:
        id: str
        name: str
        context: str
        rationale: str
        status: str
        decision_date: Optional[datetime] = None


@dataclass
class SessionEvent:
    """Single event in a session."""
    timestamp: str
    event_type: str  # prompt, response, decision, task, error
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Task entity for session tracking."""
    id: str
    name: str
    description: str
    status: str  # pending, in_progress, completed, blocked
    priority: str = "MEDIUM"
    created_date: Optional[str] = None


class SessionCollector:
    """
    Collects and routes session evidence to appropriate stores.

    Usage:
        collector = SessionCollector("STRATEGIC-VISION")
        collector.capture_prompt("What is our architecture?")
        collector.capture_decision(Decision(...))
        log_path = collector.generate_session_log()
    """

    def __init__(
        self,
        topic: str,
        session_type: str = "general",
        evidence_dir: str = None
    ):
        """
        Initialize session collector.

        Args:
            topic: Session topic (e.g., "STRATEGIC-VISION", "RD-HASKELL-MCP")
            session_type: Type of session (general, strategic, research, debug)
            evidence_dir: Directory for evidence files (default: ./evidence)
        """
        self.session_id = f"SESSION-{date.today()}-{topic.upper()}"
        self.topic = topic
        self.session_type = session_type
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

        # Evidence collections
        self.events: List[SessionEvent] = []
        self.decisions: List[Decision] = []
        self.tasks: List[Task] = []

        # Configure paths
        self.evidence_dir = Path(evidence_dir or "./evidence")
        self.docs_dir = Path("./docs")

        # TypeDB configuration
        self.typedb_host = os.getenv("TYPEDB_HOST", "localhost")
        self.typedb_port = int(os.getenv("TYPEDB_PORT", "1729"))
        self.typedb_database = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")

    def capture_prompt(self, prompt: str, metadata: Dict[str, Any] = None) -> None:
        """
        Capture user prompt.

        Args:
            prompt: User prompt text
            metadata: Additional metadata
        """
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="prompt",
            content=prompt,
            metadata={
                "session_id": self.session_id,
                **(metadata or {})
            }
        ))

    def capture_response(self, response: str, metadata: Dict[str, Any] = None) -> None:
        """
        Capture assistant response.

        Args:
            response: Assistant response text
            metadata: Additional metadata
        """
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="response",
            content=response,
            metadata={
                "session_id": self.session_id,
                **(metadata or {})
            }
        ))

    def capture_decision(
        self,
        decision_id: str,
        name: str,
        context: str,
        rationale: str,
        status: str = "active"
    ) -> Decision:
        """
        Capture strategic decision.

        Args:
            decision_id: Decision ID (e.g., "DECISION-007")
            name: Decision title
            context: Context/problem statement
            rationale: Reasoning for the decision
            status: Decision status

        Returns:
            Created Decision object
        """
        decision = Decision(
            id=decision_id,
            name=name,
            context=context,
            rationale=rationale,
            status=status,
            decision_date=datetime.now()
        )
        self.decisions.append(decision)

        # Record as event
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="decision",
            content=f"{decision_id}: {name}",
            metadata={
                "decision_id": decision_id,
                "rationale": rationale
            }
        ))

        # Auto-index to TypeDB if available
        if TYPEDB_AVAILABLE:
            self._index_decision_to_typedb(decision)

        return decision

    def capture_task(
        self,
        task_id: str,
        name: str,
        description: str,
        status: str = "pending",
        priority: str = "MEDIUM"
    ) -> Task:
        """
        Capture task for tracking.

        Args:
            task_id: Task ID (e.g., "P4.2", "RD-001")
            name: Task name
            description: Task description
            status: Task status
            priority: Task priority

        Returns:
            Created Task object
        """
        task = Task(
            id=task_id,
            name=name,
            description=description,
            status=status,
            priority=priority,
            created_date=date.today().isoformat()
        )
        self.tasks.append(task)

        # Record as event
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="task",
            content=f"{task_id}: {name}",
            metadata={
                "task_id": task_id,
                "status": status,
                "priority": priority
            }
        ))

        return task

    def capture_error(self, error: str, context: str = None) -> None:
        """
        Capture error event.

        Args:
            error: Error message
            context: Error context
        """
        self.events.append(SessionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="error",
            content=error,
            metadata={
                "session_id": self.session_id,
                "context": context
            }
        ))

    def generate_session_log(self, output_dir: Path = None) -> str:
        """
        Generate markdown session log.

        Args:
            output_dir: Output directory (default: evidence/)

        Returns:
            Path to generated log file
        """
        self.end_time = datetime.now()
        output_dir = output_dir or self.evidence_dir

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{self.session_id}.md"
        filepath = output_dir / filename

        # Build markdown content
        content = self._render_session_markdown()

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return str(filepath)

    def _render_session_markdown(self) -> str:
        """Render session as markdown document."""
        duration = (self.end_time or datetime.now()) - self.start_time

        lines = [
            f"# Session Evidence Log: {self.topic}",
            "",
            f"**Session ID:** {self.session_id}",
            f"**Type:** {self.session_type}",
            f"**Started:** {self.start_time.isoformat()}",
            f"**Ended:** {(self.end_time or datetime.now()).isoformat()}",
            f"**Duration:** {duration}",
            "",
            "---",
            "",
        ]

        # Decisions section
        if self.decisions:
            lines.extend([
                "## Decisions",
                "",
                "| ID | Name | Status |",
                "|-----|------|--------|",
            ])
            for d in self.decisions:
                lines.append(f"| {d.id} | {d.name} | {d.status} |")
            lines.extend(["", "### Decision Details", ""])
            for d in self.decisions:
                lines.extend([
                    f"#### {d.id}: {d.name}",
                    "",
                    f"**Context:** {d.context}",
                    "",
                    f"**Rationale:** {d.rationale}",
                    "",
                ])

        # Tasks section
        if self.tasks:
            lines.extend([
                "## Tasks",
                "",
                "| ID | Name | Status | Priority |",
                "|----|------|--------|----------|",
            ])
            for t in self.tasks:
                lines.append(f"| {t.id} | {t.name} | {t.status} | {t.priority} |")
            lines.append("")

        # Events timeline
        lines.extend([
            "## Event Timeline",
            "",
        ])
        for event in self.events:
            icon = {
                "prompt": "💬",
                "response": "🤖",
                "decision": "⚖️",
                "task": "📋",
                "error": "❌"
            }.get(event.event_type, "📌")
            lines.append(f"- {icon} **{event.event_type.upper()}** ({event.timestamp}): {event.content[:100]}...")

        lines.extend([
            "",
            "---",
            "",
            f"*Generated per RULE-001: Session Evidence Logging*",
        ])

        return "\n".join(lines)

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

        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "session_type": self.session_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "events_count": len(self.events),
            "decisions_count": len(self.decisions),
            "tasks_count": len(self.tasks),
            "decisions": [asdict(d) for d in self.decisions],
            "tasks": [asdict(t) for t in self.tasks],
        }

    def to_json(self) -> str:
        """Convert session to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)


# Global session registry for active sessions
_active_sessions: Dict[str, SessionCollector] = {}


def get_or_create_session(topic: str, session_type: str = "general") -> SessionCollector:
    """
    Get existing session or create new one.

    Args:
        topic: Session topic
        session_type: Type of session

    Returns:
        SessionCollector instance
    """
    session_id = f"SESSION-{date.today()}-{topic.upper()}"

    if session_id not in _active_sessions:
        _active_sessions[session_id] = SessionCollector(topic, session_type)

    return _active_sessions[session_id]


def end_session(topic: str) -> Optional[str]:
    """
    End session and generate log.

    Args:
        topic: Session topic

    Returns:
        Path to generated log file, or None if session not found
    """
    session_id = f"SESSION-{date.today()}-{topic.upper()}"

    if session_id in _active_sessions:
        collector = _active_sessions.pop(session_id)
        log_path = collector.generate_session_log()
        collector.sync_to_chromadb()
        return log_path

    return None


def list_active_sessions() -> List[str]:
    """List all active session IDs."""
    return list(_active_sessions.keys())
