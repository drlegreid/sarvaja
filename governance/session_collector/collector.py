"""
Session Collector Main Class.

Per RULE-032: Modularized from session_collector.py (591 lines).
Contains: SessionCollector class with all mixins composed.
"""

import os
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path

from .models import SessionEvent, Task, Decision, SessionIntent, SessionOutcome
from .capture import SessionCaptureMixin
from .sync import SessionSyncMixin
from .render import SessionRenderMixin


class SessionCollector(SessionCaptureMixin, SessionSyncMixin, SessionRenderMixin):
    """
    Collects and routes session evidence to appropriate stores.

    Usage:
        collector = SessionCollector("STRATEGIC-VISION")
        collector.capture_prompt("What is our architecture?")
        collector.capture_decision(Decision(...))
        log_path = collector.generate_session_log()

    Per RULE-001: Session Evidence Logging
    Per RULE-006: Decision Logging
    """

    def __init__(
        self,
        topic: str,
        session_type: str = "general",
        evidence_dir: str = None,
        agent_id: str = None,
    ):
        """
        Initialize session collector.

        Args:
            topic: Session topic (e.g., "STRATEGIC-VISION", "RD-HASKELL-MCP")
            session_type: Type of session (general, strategic, research, debug)
            evidence_dir: Directory for evidence files (default: ./evidence)
            agent_id: Agent that owns this session (A.4: session-agent linking)
        """
        self.session_id = f"SESSION-{date.today()}-{topic.upper()}"
        self.topic = topic
        self.session_type = session_type
        self.agent_id = agent_id
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

        # Evidence collections
        self.events: List[SessionEvent] = []
        self.decisions: List[Decision] = []
        self.tasks: List[Task] = []

        # Intent tracking (RD-INTENT)
        self.intent: Optional[SessionIntent] = None
        self.outcome: Optional[SessionOutcome] = None

        # Configure paths
        self.evidence_dir = Path(evidence_dir or "./evidence")
        self.docs_dir = Path("./docs")

        # TypeDB configuration
        self.typedb_host = os.getenv("TYPEDB_HOST", "localhost")
        self.typedb_port = int(os.getenv("TYPEDB_PORT", "1729"))
        self.typedb_database = os.getenv("TYPEDB_DATABASE", "sim-ai-governance")
