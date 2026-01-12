"""
Session Core MCP Tools
======================
Core session evidence collection operations.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines

Extracted from sessions.py per modularization plan.
Created: 2026-01-03
"""

import json
from typing import Optional

# Import session collector (with fallback)
try:
    from governance.session_collector import (
        SessionCollector,
        get_or_create_session,
        end_session,
        list_active_sessions
    )
    SESSION_COLLECTOR_AVAILABLE = True
except ImportError:
    SESSION_COLLECTOR_AVAILABLE = False

# Check TypeDB availability
try:
    from governance.client import TypeDBClient
    TYPEDB_AVAILABLE = True
except ImportError:
    TYPEDB_AVAILABLE = False


def register_session_core_tools(mcp) -> None:
    """Register core session MCP tools."""

    @mcp.tool()
    def session_start(topic: str, session_type: str = "general") -> str:
        """
        Start a new session with evidence collection.

        Args:
            topic: Session topic (e.g., "STRATEGIC-VISION", "RD-HASKELL-MCP")
            session_type: Type of session (general, strategic, research, debug)

        Returns:
            JSON object with session ID and status
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return json.dumps({"error": "SessionCollector not available"})

        collector = get_or_create_session(topic, session_type)

        return json.dumps({
            "session_id": collector.session_id,
            "topic": topic,
            "session_type": session_type,
            "started_at": collector.start_time.isoformat(),
            "message": f"Session started: {collector.session_id}"
        }, indent=2)

    @mcp.tool()
    def session_decision(
        decision_id: str,
        name: str,
        context: str,
        rationale: str,
        topic: Optional[str] = None
    ) -> str:
        """
        Record a strategic decision in the current session.

        Args:
            decision_id: Decision ID (e.g., "DECISION-007")
            name: Decision title
            context: Context/problem statement
            rationale: Reasoning for the decision
            topic: Session topic (uses last session if not provided)

        Returns:
            JSON object with decision confirmation
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return json.dumps({"error": "SessionCollector not available"})

        # Get or create session
        sessions = list_active_sessions()
        if not sessions and not topic:
            return json.dumps({"error": "No active session. Call session_start first."})

        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

        decision = collector.capture_decision(
            decision_id=decision_id,
            name=name,
            context=context,
            rationale=rationale
        )

        return json.dumps({
            "decision_id": decision_id,
            "session_id": collector.session_id,
            "name": name,
            "indexed_to_typedb": TYPEDB_AVAILABLE,
            "message": f"Decision {decision_id} recorded and indexed"
        }, indent=2)

    @mcp.tool()
    def session_task(
        task_id: str,
        name: str,
        description: str,
        status: str = "pending",
        priority: str = "MEDIUM",
        topic: Optional[str] = None
    ) -> str:
        """
        Record a task in the current session.

        Args:
            task_id: Task ID (e.g., "P4.2", "RD-001")
            name: Task name
            description: Task description
            status: Task status (pending, in_progress, completed, blocked)
            priority: Task priority (LOW, MEDIUM, HIGH, CRITICAL)
            topic: Session topic (uses last session if not provided)

        Returns:
            JSON object with task confirmation
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return json.dumps({"error": "SessionCollector not available"})

        # Get or create session
        sessions = list_active_sessions()
        if not sessions and not topic:
            return json.dumps({"error": "No active session. Call session_start first."})

        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

        task = collector.capture_task(
            task_id=task_id,
            name=name,
            description=description,
            status=status,
            priority=priority
        )

        return json.dumps({
            "task_id": task_id,
            "session_id": collector.session_id,
            "name": name,
            "status": status,
            "message": f"Task {task_id} recorded"
        }, indent=2)

    @mcp.tool()
    def session_end(topic: str) -> str:
        """
        End session and generate evidence artifacts.

        Args:
            topic: Session topic to end

        Returns:
            JSON object with log path and sync status
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return json.dumps({"error": "SessionCollector not available"})

        log_path = end_session(topic)

        if log_path:
            return json.dumps({
                "topic": topic,
                "log_path": log_path,
                "synced_to_chromadb": True,
                "message": f"Session ended. Log: {log_path}"
            }, indent=2)
        else:
            return json.dumps({
                "error": f"Session for topic '{topic}' not found"
            })

    @mcp.tool()
    def session_list() -> str:
        """
        List all active sessions.

        Returns:
            JSON array of active session IDs
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return json.dumps({"error": "SessionCollector not available"})

        sessions = list_active_sessions()

        return json.dumps({
            "active_sessions": sessions,
            "count": len(sessions)
        }, indent=2)
