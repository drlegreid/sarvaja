"""
Chat Session Bridge.

Per A.2: Bridge between chat operations and gov-sessions MCP.
Creates governance SessionCollector instances during chat,
records tool calls and thoughts, and syncs on session end.

Per GAP-GOVSESS-CAPTURE-001: Sessions MUST persist to TypeDB via service layer.
Per RULE-012: Single Responsibility - only chat↔session bridging.
Per DOC-SIZE-01-v1: Files under 300 lines.

Created: 2026-02-01
Updated: 2026-02-09 - TypeDB persistence via service layer (GAP-GOVSESS-CAPTURE-001)
"""
import logging
from datetime import datetime
from typing import Optional

from governance.session_collector.collector import SessionCollector
from governance.services.sessions import create_session
from governance.services.sessions_lifecycle import end_session
from governance.stores import _sessions_store
from governance.stores.session_persistence import persist_session

logger = logging.getLogger(__name__)

# Claude Code built-in tools (not MCP)
_CC_BUILTIN_TOOLS = frozenset({
    "Read", "Write", "Edit", "Bash", "Glob", "Grep",
    "TodoWrite", "Task", "WebSearch", "WebFetch",
    "NotebookEdit", "AskUserQuestion", "EnterPlanMode",
    "ExitPlanMode", "ToolSearch", "Skill",
})

# MCP governance server prefixes
_GOV_MCP_PREFIXES = ("mcp__gov-core__", "mcp__gov-sessions__",
                      "mcp__gov-tasks__", "mcp__gov-agents__")


def is_chat_command(text: str) -> bool:
    """Check if text is a slash command (local skill, not an MCP tool)."""
    return bool(text) and text.startswith("/")


def classify_tool(tool_name: str) -> str:
    """Classify a tool by category for session analytics.

    Returns one of: mcp_governance, mcp_other, cc_builtin, chat_command, unknown.
    """
    if not tool_name:
        return "unknown"
    if tool_name.startswith("/"):
        return "chat_command"
    if tool_name in _CC_BUILTIN_TOOLS:
        return "cc_builtin"
    if any(tool_name.startswith(p) for p in _GOV_MCP_PREFIXES):
        return "mcp_governance"
    if tool_name.startswith("mcp__"):
        return "mcp_other"
    return "unknown"


def start_chat_session(
    agent_id: str,
    topic: str,
    session_type: str = "general",
) -> SessionCollector:
    """
    Start a governance session for a chat interaction.

    Creates a SessionCollector, persists to TypeDB via service layer,
    and registers in _sessions_store for dashboard visibility.

    Args:
        agent_id: The agent handling this chat
        topic: Chat topic or first message summary
        session_type: Session type (general, research, debug)

    Returns:
        SessionCollector instance for recording events
    """
    # Sanitize topic: replace spaces, slashes, and other path-unsafe chars
    # BUG-210-BRIDGE-SANITIZE-001: Strip control chars + additional path-unsafe chars
    import re
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', topic[:40]).replace(' ', '-').replace('/', '-').replace('\\', '-')
    safe_topic = f"CHAT-{sanitized.upper()}"
    collector = SessionCollector(
        topic=safe_topic,
        session_type=session_type,
        agent_id=agent_id,
    )

    # Per GAP-GOVSESS-CAPTURE-001: Persist to TypeDB via service layer
    try:
        result = create_session(
            session_id=collector.session_id,
            description=safe_topic,
            agent_id=agent_id,
            source="chat-bridge",
        )
        p_status = result.get("persistence_status", "unknown")
        if p_status != "persisted":
            logger.error(
                f"Session {collector.session_id} NOT persisted to TypeDB "
                f"(status={p_status}) — will appear as orphan until sync"
            )
    except Exception as e:
        # BUG-424-BRG-001: Add exc_info for stack trace preservation
        logger.error(f"TypeDB session create failed: {e}", exc_info=True)

    # Always ensure _sessions_store has session data for bridge syncing
    # (create_session may have stored in TypeDB but not in _sessions_store)
    if collector.session_id not in _sessions_store:
        _sessions_store[collector.session_id] = {
            "session_id": collector.session_id,
            "start_time": collector.start_time.isoformat(),
            "status": "ACTIVE",
            "tasks_completed": 0,
            "description": safe_topic,
            "agent_id": agent_id,
        }
    # Enrich with bridge-specific fields
    _sessions_store[collector.session_id].update({
        "topic": safe_topic,
        "session_type": session_type,
        "intent": topic,
    })
    persist_session(collector.session_id, _sessions_store[collector.session_id])

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
            "tool_category": classify_tool(tool_name),
            "arguments": arguments or {},
            "result": result,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })
        # BUG-210-BRIDGE-CAP-001: Cap tool_calls to prevent unbounded growth
        if len(_sessions_store[session_id]["tool_calls"]) > 500:
            _sessions_store[session_id]["tool_calls"] = _sessions_store[session_id]["tool_calls"][-500:]
        persist_session(session_id, _sessions_store[session_id])


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
            "thought": thought,
            "thought_type": thought_type,
            "related_tools": related_tools,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        })
        # BUG-210-BRIDGE-CAP-002: Cap thoughts to prevent unbounded growth
        if len(_sessions_store[session_id]["thoughts"]) > 200:
            _sessions_store[session_id]["thoughts"] = _sessions_store[session_id]["thoughts"][-200:]
        persist_session(session_id, _sessions_store[session_id])


def end_chat_session(
    collector: SessionCollector,
    summary: str = None,
) -> Optional[str]:
    """
    End a chat session - persist to TypeDB, generate evidence, sync ChromaDB.

    Per GAP-GOVSESS-CAPTURE-001: Sessions MUST be ended via service layer
    to persist end_time and COMPLETED status to TypeDB.

    Args:
        collector: Active SessionCollector
        summary: Optional session summary

    Returns:
        Path to evidence file if generated, None otherwise
    """
    session_id = collector.session_id

    # Count tool calls for tasks_completed metric
    tool_call_count = len([
        e for e in collector.events if e.event_type == "tool_call"
    ])

    # Per GAP-GOVSESS-CAPTURE-001: End via service layer for TypeDB persistence
    try:
        end_session(
            session_id=session_id,
            tasks_completed=tool_call_count,
            source="chat-bridge",
        )
    except Exception as e:
        # BUG-424-BRG-002: Add exc_info for stack trace preservation
        logger.error(f"TypeDB session end failed: {e}", exc_info=True)

    # Always update _sessions_store for consistency
    if session_id in _sessions_store:
        _sessions_store[session_id]["status"] = "COMPLETED"
        _sessions_store[session_id]["end_time"] = datetime.now().isoformat()
        _sessions_store[session_id]["tasks_completed"] = tool_call_count
        if summary:
            _sessions_store[session_id]["summary"] = summary

    # Generate evidence log
    evidence_path = None
    try:
        evidence_path = collector.generate_session_log()
    except Exception as e:
        # BUG-424-BRG-003: Add exc_info for stack trace preservation
        logger.warning(f"Failed to generate session log: {e}", exc_info=True)

    # BUG-SESSION-EVIDENCE-001: Auto-link evidence to TypeDB after generation
    if evidence_path:
        try:
            from governance.stores import get_typedb_client
            client = get_typedb_client()
            if client:
                client.link_evidence_to_session(session_id, evidence_path)
                logger.info(f"Evidence linked: {session_id} -> {evidence_path}")
            else:
                logger.warning(f"TypeDB unavailable; evidence not linked: {session_id} -> {evidence_path}")
        except Exception as e:
            # BUG-424-BRG-004: Add exc_info for stack trace preservation
            logger.error(f"Evidence linking failed for {session_id}: {e}", exc_info=True)
        # Also store in _sessions_store for fallback
        if session_id in _sessions_store:
            existing = _sessions_store[session_id].get("evidence_files") or []
            if evidence_path not in existing:
                existing.append(evidence_path)
                _sessions_store[session_id]["evidence_files"] = existing

    # Sync to ChromaDB for semantic search
    try:
        collector.sync_to_chromadb()
    except Exception as e:
        # BUG-424-BRG-005: Add exc_info for stack trace preservation
        logger.warning(f"Failed to sync session to ChromaDB: {e}", exc_info=True)

    # Per TEST-CVP-01-v1 Tier 2: Post-session validation
    _run_post_session_checks(session_id, collector)

    logger.info(f"Chat session ended: {session_id}")
    return evidence_path


def _run_post_session_checks(session_id: str, collector: SessionCollector) -> None:
    """
    Run lightweight post-session validation checks (Tier 2, <5s budget).

    Per TEST-CVP-01-v1: Validates session completeness after end.
    Runs asynchronously to avoid blocking the caller.
    """
    try:
        has_agent = bool(getattr(collector, "agent_id", None))
        has_tool_calls = any(e.event_type == "tool_call" for e in collector.events)
        has_thoughts = any(e.event_type == "thought" for e in collector.events)
        issues = []
        if not has_agent:
            issues.append("missing agent_id")
        if not has_tool_calls:
            issues.append("no tool calls recorded")
        if not has_thoughts:
            issues.append("no thoughts recorded")
        if issues:
            logger.warning(
                f"Post-session validation [{session_id}]: {', '.join(issues)}"
            )
        else:
            logger.info(f"Post-session validation [{session_id}]: OK")
    except Exception as e:
        # BUG-424-BRG-006: Upgrade debug→warning + exc_info (data integrity)
        logger.warning(f"Post-session validation failed: {e}", exc_info=True)
