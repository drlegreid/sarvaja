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

    @mcp.tool()
    def session_tool_call(
        tool_name: str,
        arguments: str = "{}",
        result_summary: Optional[str] = None,
        duration_ms: int = 0,
        success: bool = True,
        topic: Optional[str] = None,
        correlation_id: Optional[str] = None,
        applied_rules: Optional[str] = None
    ) -> str:
        """
        Record a tool call in the current session.

        Per Task 2.3: Track tool calls with arguments for session evidence.
        Per RD-DEBUG-AUDIT: Cross-agent correlation and rule linkage.
        Enables debugging and replay of agent actions.

        Args:
            tool_name: MCP tool name (e.g., "governance_get_rule", "Bash")
            arguments: Tool arguments as JSON string
            result_summary: Summary of tool result (truncated for large results)
            duration_ms: Execution time in milliseconds
            success: Whether the tool call succeeded
            topic: Session topic (uses last session if not provided)
            correlation_id: Cross-agent trace ID for request correlation
            applied_rules: Comma-separated rule IDs applied during this call

        Returns:
            JSON object with tool call confirmation
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return json.dumps({"error": "SessionCollector not available"})

        # Get or create session
        sessions = list_active_sessions()
        if not sessions and not topic:
            return json.dumps({"error": "No active session. Call session_start first."})

        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

        # Parse arguments JSON
        try:
            args_dict = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            args_dict = {"raw": arguments}

        # Parse applied_rules from comma-separated string
        rules_list = [r.strip() for r in applied_rules.split(",")] if applied_rules else []

        collector.capture_tool_call(
            tool_name=tool_name,
            arguments=args_dict,
            result=result_summary,
            duration_ms=duration_ms,
            success=success,
            correlation_id=correlation_id,
            applied_rules=rules_list
        )

        return json.dumps({
            "tool_name": tool_name,
            "session_id": collector.session_id,
            "duration_ms": duration_ms,
            "success": success,
            "correlation_id": correlation_id,
            "applied_rules": rules_list,
            "message": f"Tool call {tool_name} recorded"
        }, indent=2)

    @mcp.tool()
    def session_thought(
        thought: str,
        thought_type: str = "reasoning",
        related_tools: Optional[str] = None,
        confidence: float = 0.0,
        topic: Optional[str] = None
    ) -> str:
        """
        Record a thought/reasoning step in the current session.

        Per Task 2.3: Track thoughts with holographic detailisation.
        Enables understanding of agent reasoning chains.

        Args:
            thought: The thought/reasoning text
            thought_type: Type of thought (reasoning, planning, reflection, hypothesis)
            related_tools: Comma-separated list of related tool names
            confidence: Confidence score (0.0-1.0)
            topic: Session topic (uses last session if not provided)

        Returns:
            JSON object with thought confirmation
        """
        if not SESSION_COLLECTOR_AVAILABLE:
            return json.dumps({"error": "SessionCollector not available"})

        # Get or create session
        sessions = list_active_sessions()
        if not sessions and not topic:
            return json.dumps({"error": "No active session. Call session_start first."})

        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

        # Parse related tools
        tools_list = [t.strip() for t in related_tools.split(",")] if related_tools else []

        collector.capture_thought(
            thought=thought,
            thought_type=thought_type,
            related_tools=tools_list,
            confidence=confidence if confidence > 0 else None
        )

        return json.dumps({
            "thought_type": thought_type,
            "session_id": collector.session_id,
            "related_tools": tools_list,
            "message": f"Thought ({thought_type}) recorded"
        }, indent=2)
