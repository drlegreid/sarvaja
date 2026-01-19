"""Session Core MCP Tools. Per RULE-012: DSP Semantic Code Structure."""
from typing import Optional

from governance.mcp_tools.common import format_mcp_result

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
        """Start a new session with evidence collection."""
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        collector = get_or_create_session(topic, session_type)

        return format_mcp_result({
            "session_id": collector.session_id,
            "topic": topic,
            "session_type": session_type,
            "started_at": collector.start_time.isoformat(),
            "message": f"Session started: {collector.session_id}"
        })

    @mcp.tool()
    def session_decision(decision_id: str, name: str, context: str, rationale: str,
                         topic: Optional[str] = None) -> str:
        """Record a strategic decision in the current session."""
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        # Get or create session
        sessions = list_active_sessions()
        if not sessions and not topic:
            return format_mcp_result({"error": "No active session. Call session_start first."})

        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

        decision = collector.capture_decision(
            decision_id=decision_id,
            name=name,
            context=context,
            rationale=rationale
        )

        return format_mcp_result({"decision_id": decision_id, "session_id": collector.session_id, "name": name,
                           "indexed_to_typedb": TYPEDB_AVAILABLE, "message": f"Decision {decision_id} recorded and indexed"})

    @mcp.tool()
    def session_task(task_id: str, name: str, description: str, status: str = "pending",
                     priority: str = "MEDIUM", topic: Optional[str] = None) -> str:
        """Record a task in the current session."""
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        # Get or create session
        sessions = list_active_sessions()
        if not sessions and not topic:
            return format_mcp_result({"error": "No active session. Call session_start first."})

        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

        task = collector.capture_task(
            task_id=task_id,
            name=name,
            description=description,
            status=status,
            priority=priority
        )

        return format_mcp_result({
            "task_id": task_id,
            "session_id": collector.session_id,
            "name": name,
            "status": status,
            "message": f"Task {task_id} recorded"
        })

    @mcp.tool()
    def session_end(topic: str) -> str:
        """End session and generate evidence artifacts."""
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        log_path = end_session(topic)

        if log_path:
            return format_mcp_result({
                "topic": topic,
                "log_path": log_path,
                "synced_to_chromadb": True,
                "message": f"Session ended. Log: {log_path}"
            })
        else:
            return format_mcp_result({
                "error": f"Session for topic '{topic}' not found"
            })

    @mcp.tool()
    def session_list() -> str:
        """List all active sessions."""
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        sessions = list_active_sessions()

        return format_mcp_result({
            "active_sessions": sessions,
            "count": len(sessions)
        })

    @mcp.tool()
    def session_tool_call(tool_name: str, arguments: str = "{}", result_summary: Optional[str] = None,
                          duration_ms: int = 0, success: bool = True, topic: Optional[str] = None,
                          correlation_id: Optional[str] = None, applied_rules: Optional[str] = None) -> str:
        """Record a tool call in the current session. Per Task 2.3, RD-DEBUG-AUDIT."""
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        sessions = list_active_sessions()
        if not sessions and not topic:
            return format_mcp_result({"error": "No active session. Call session_start first."})
        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())
        try:
            args_dict = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            args_dict = {"raw": arguments}
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

        return format_mcp_result({
            "tool_name": tool_name,
            "session_id": collector.session_id,
            "duration_ms": duration_ms,
            "success": success,
            "correlation_id": correlation_id,
            "applied_rules": rules_list,
            "message": f"Tool call {tool_name} recorded"
        })

    @mcp.tool()
    def session_thought(thought: str, thought_type: str = "reasoning", related_tools: Optional[str] = None,
                        confidence: float = 0.0, topic: Optional[str] = None) -> str:
        """Record a thought/reasoning step in the current session. Per Task 2.3."""
        if not SESSION_COLLECTOR_AVAILABLE:
            return format_mcp_result({"error": "SessionCollector not available"})

        sessions = list_active_sessions()
        if not sessions and not topic:
            return format_mcp_result({"error": "No active session. Call session_start first."})
        collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())
        tools_list = [t.strip() for t in related_tools.split(",")] if related_tools else []
        collector.capture_thought(
            thought=thought,
            thought_type=thought_type,
            related_tools=tools_list,
            confidence=confidence if confidence > 0 else None
        )

        return format_mcp_result({
            "thought_type": thought_type,
            "session_id": collector.session_id,
            "related_tools": tools_list,
            "message": f"Thought ({thought_type}) recorded"
        })
