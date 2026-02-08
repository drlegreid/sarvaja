"""
Chat Session Bridge.

Per A.2: Bridge between chat operations and gov-sessions MCP.
Creates governance SessionCollector instances during chat,
records tool calls and thoughts, and syncs on session end.

Per RULE-012: Single Responsibility - only chat↔session bridging.
Per DOC-SIZE-01-v1: Files under 300 lines.

Created: 2026-02-01
"""
import logging
from datetime import datetime
from typing import Optional

from governance.session_collector.collector import SessionCollector
from governance.stores import _sessions_store

logger = logging.getLogger(__name__)


def start_chat_session(
    agent_id: str,
    topic: str,
    session_type: str = "general",
) -> SessionCollector:
    """
    Start a governance session for a chat interaction.

    Creates a SessionCollector and registers the session in
    _sessions_store so it appears in /sessions and dashboard.

    Args:
        agent_id: The agent handling this chat
        topic: Chat topic or first message summary
        session_type: Session type (general, research, debug)

    Returns:
        SessionCollector instance for recording events
    """
    safe_topic = f"CHAT-{topic[:40].replace(' ', '-').upper()}"
    collector = SessionCollector(
        topic=safe_topic,
        session_type=session_type,
        agent_id=agent_id,
    )

    # Register in sessions store for dashboard visibility
    _sessions_store[collector.session_id] = {
        "session_id": collector.session_id,
        "agent_id": agent_id,
        "status": "ACTIVE",
        "start_time": collector.start_time.isoformat(),
        "topic": safe_topic,
        "session_type": session_type,
        "intent": topic,
    }

    logger.info(
        f"Chat session started: {collector.session_id} "
        f"(agent={agent_id}, topic={safe_topic})"
    )
    return collector


def record_chat_tool_call(
    collector: SessionCollector,
    tool_name: str,
    arguments: dict = None,
    result: str = None,
    duration_ms: int = None,
    success: bool = True,
) -> None:
    """
    Record a tool call (chat command execution) in the session.

    Per DATA-COMPLETE-01-v1: Tool calls are synced to _sessions_store
    for visibility via /sessions/{id}/tool_calls API.

    Args:
        collector: Active SessionCollector
        tool_name: Command or tool name (e.g., "/status", "query_llm")
        arguments: Tool arguments
        result: Result text (truncated internally)
        duration_ms: Execution duration in milliseconds
        success: Whether the call succeeded
    """
    collector.capture_tool_call(
        tool_name=tool_name,
        arguments=arguments or {},
        result=result,
        duration_ms=duration_ms,
        success=success,
    )

    # Per DATA-COMPLETE-01-v1: Sync to _sessions_store for API visibility
    session_id = collector.session_id
    if session_id in _sessions_store:
        if "tool_calls" not in _sessions_store[session_id]:
            _sessions_store[session_id]["tool_calls"] = []
        _sessions_store[session_id]["tool_calls"].append({
            "tool_name": tool_name,
            "arguments": arguments or {},
            "result": (result[:200] + "...") if result and len(result) > 200 else result,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })


def record_chat_thought(
    collector: SessionCollector,
    thought: str,
    thought_type: str = "reasoning",
    related_tools: list = None,
    confidence: float = None,
) -> None:
    """
    Record a thought/reasoning step in the session.

    Per DATA-COMPLETE-01-v1: Thoughts are synced to _sessions_store
    for visibility via /sessions/{id}/thoughts API.

    Args:
        collector: Active SessionCollector
        thought: The thought content
        thought_type: Type (reasoning, observation, hypothesis)
        related_tools: Related tool names
        confidence: Confidence level 0.0-1.0
    """
    collector.capture_thought(
        thought=thought,
        thought_type=thought_type,
        related_tools=related_tools,
        confidence=confidence,
    )

    # Per DATA-COMPLETE-01-v1: Sync to _sessions_store for API visibility
    session_id = collector.session_id
    if session_id in _sessions_store:
        if "thoughts" not in _sessions_store[session_id]:
            _sessions_store[session_id]["thoughts"] = []
        _sessions_store[session_id]["thoughts"].append({
            "thought": thought[:500] if len(thought) > 500 else thought,
            "thought_type": thought_type,
            "related_tools": related_tools,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        })


def end_chat_session(
    collector: SessionCollector,
    summary: str = None,
) -> Optional[str]:
    """
    End a chat session - update store and optionally generate log.

    Args:
        collector: Active SessionCollector
        summary: Optional session summary

    Returns:
        Path to evidence file if generated, None otherwise
    """
    session_id = collector.session_id

    # Update store
    if session_id in _sessions_store:
        _sessions_store[session_id]["status"] = "ENDED"
        _sessions_store[session_id]["end_time"] = datetime.now().isoformat()
        if summary:
            _sessions_store[session_id]["summary"] = summary

    # Generate evidence log
    evidence_path = None
    try:
        evidence_path = collector.generate_session_log()
    except Exception as e:
        logger.warning(f"Failed to generate session log: {e}")

    # Sync to ChromaDB for semantic search
    try:
        collector.sync_to_chromadb()
    except Exception as e:
        logger.warning(f"Failed to sync session to ChromaDB: {e}")

    logger.info(f"Chat session ended: {session_id}")
    return evidence_path
