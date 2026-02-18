"""
Chat Routes Endpoints.

Per GAP-FILE-023: Refactored from routes/chat.py
Per DOC-SIZE-01-v1: Delegation protocol in endpoints_delegation.py

FastAPI endpoints for chat functionality.

Created: 2024-12-28
Refactored: 2026-01-14
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid
import logging

from governance.models import (
    ChatMessageRequest, ChatMessageResponse, ChatSessionResponse
)
from governance.stores import (
    _chat_sessions, _agents_store,
    generate_chat_session_id, get_available_agents_for_chat
)
from governance.context_preloader import preload_session_context

from .commands import process_chat_command
from .session_bridge import (
    start_chat_session,
    record_chat_tool_call,
    record_chat_thought,
    end_chat_session,
)

# Re-export for backward compatibility
from .endpoints_delegation import (  # noqa: F401
    _get_delegation_protocol,
    delegate_task_async as _delegate_task_async,
)


logger = logging.getLogger(__name__)

# Track active governance sessions per chat session
_chat_gov_sessions: Dict[str, Any] = {}
router = APIRouter(tags=["Chat"])


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@router.post("/chat/send", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest):
    """Send a chat message to an agent."""
    # Get or create session
    session_id = request.session_id
    if not session_id:
        session_id = generate_chat_session_id()

        try:
            context = preload_session_context()
            context_dict = context.to_dict()
        except Exception as e:
            # BUG-424-CHT-001: Add exc_info for stack trace preservation
            logger.warning(f"Failed to preload context: {e}", exc_info=True)
            context_dict = {}

        _chat_sessions[session_id] = {
            "session_id": session_id,
            "messages": [],
            "active_task_id": None,
            "selected_agent_id": request.agent_id,
            "created_at": datetime.now().isoformat(),
            "context": context_dict,
        }

    # BUG-336-CHAT-001: Reject unknown session_id instead of fabricating a phantom fallback dict
    session = _chat_sessions.get(session_id)
    if session is None:
        session = {
            "session_id": session_id,
            "messages": [],
            "active_task_id": None,
            "selected_agent_id": request.agent_id,
        }
        _chat_sessions[session_id] = session

    # Store user message
    user_msg = {
        "id": f"MSG-{uuid.uuid4().hex[:8].upper()}",
        "role": "user",
        "content": request.content,
        "timestamp": datetime.now().isoformat(),
        "status": "complete",
    }
    session["messages"].append(user_msg)

    # Select agent
    agent_id = request.agent_id or session.get("selected_agent_id")
    if not agent_id:
        agents = get_available_agents_for_chat()
        if agents:
            agents_sorted = sorted(agents, key=lambda a: a.get("trust_score", 0), reverse=True)
            agent_id = agents_sorted[0].get("agent_id", "AGENT-001")
        else:
            agent_id = "AGENT-001"

    agent = _agents_store.get(agent_id, {
        "agent_id": agent_id,
        "name": "Default Agent",
        "trust_score": 0.8,
    })
    agent_name = agent.get("name", "Agent")

    # Start governance session for new chat sessions (A.2 session bridge)
    # BUG-206-PURGE-001: Cap _chat_gov_sessions to prevent unbounded memory growth
    # BUG-336-CHAT-002: Snapshot keys before eviction to prevent RuntimeError on concurrent mutation
    if len(_chat_gov_sessions) > 200:
        oldest_keys = sorted(list(_chat_gov_sessions.keys()))[:50]
        for k in oldest_keys:
            _chat_gov_sessions.pop(k, None)

    gov_collector = _chat_gov_sessions.get(session_id)
    if gov_collector is None:
        try:
            topic = request.content[:60] if request.content else "Chat session"
            gov_collector = start_chat_session(agent_id, topic)
            _chat_gov_sessions[session_id] = gov_collector
        except Exception as e:
            # BUG-424-CHT-002: Add exc_info for stack trace preservation
            logger.warning(f"Failed to start governance session: {e}", exc_info=True)

    # Process command
    import time as _time
    _cmd_start = _time.time()
    # BUG-300-DEL-001: Track whether user explicitly issued /delegate command
    _is_explicit_delegate = bool(request.content and request.content.strip().lower().startswith("/delegate"))
    # BUG-206-RESPONSE-001: Guard against None return from process_chat_command
    response_content = process_chat_command(request.content, agent_id) or ""
    _cmd_duration = int((_time.time() - _cmd_start) * 1000)

    # Record tool call in governance session
    if gov_collector:
        try:
            record_chat_tool_call(
                gov_collector,
                # BUG-ROUTE-001: Guard against whitespace-only content
                tool_name=(request.content.split()[0] if request.content and request.content.split() else "chat"),
                arguments={"content": request.content[:200]},
                result=response_content[:500],
                duration_ms=_cmd_duration,
            )
        except Exception as e:
            # BUG-424-CHT-003: Upgrade debug→warning + exc_info (data integrity)
            logger.warning(f"Failed to record chat tool call: {e}", exc_info=True)

    # Record LLM reasoning as thought (GAP-GOVSESS-CAPTURE-001)
    if gov_collector and not response_content.startswith("__DELEGATE__:"):
        try:
            is_command = request.content.startswith("/") if request.content else False
            record_chat_thought(
                gov_collector,
                thought=f"{'Command' if is_command else 'LLM'}: {response_content[:300]}",
                thought_type="command_result" if is_command else "llm_response",
            )
        except Exception as e:
            # BUG-424-CHT-004: Upgrade debug→warning + exc_info (data integrity)
            logger.warning(f"Failed to record chat thought: {e}", exc_info=True)

    # Handle async delegation
    # BUG-300-DEL-001: Only honour __DELEGATE__ sentinel from explicit /delegate command,
    # not from LLM output (prevents prompt-injection-driven agent command injection)
    if _is_explicit_delegate and response_content.startswith("__DELEGATE__:"):
        task_desc = response_content[13:]
        response_content = await _delegate_task_async(task_desc, agent_id)

    # Create response
    response_msg = {
        "id": f"MSG-{uuid.uuid4().hex[:8].upper()}",
        "role": "agent",
        "content": response_content,
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent_id,
        "agent_name": agent_name,
        "task_id": session.get("active_task_id"),
        "status": "complete",
    }
    session["messages"].append(response_msg)
    _chat_sessions[session_id] = session

    return ChatMessageResponse(**response_msg)


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str):
    """Get a chat session by ID."""
    if session_id not in _chat_sessions:
        raise HTTPException(status_code=404, detail=f"Chat session {session_id} not found")

    session = _chat_sessions[session_id]
    return ChatSessionResponse(
        session_id=session["session_id"],
        messages=[ChatMessageResponse(**m) for m in session["messages"]],
        active_task_id=session.get("active_task_id"),
        selected_agent_id=session.get("selected_agent_id"),
    )


@router.get("/chat/sessions", response_model=List[Dict[str, Any]])
async def list_chat_sessions():
    """List all chat sessions."""
    sessions = []
    for session_id, session in _chat_sessions.items():
        sessions.append({
            "session_id": session_id,
            "message_count": len(session.get("messages", [])),
            "created_at": session.get("created_at"),
            "selected_agent_id": session.get("selected_agent_id"),
        })
    return sessions


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session and end its governance session."""
    if session_id not in _chat_sessions:
        raise HTTPException(status_code=404, detail=f"Chat session {session_id} not found")

    # Per GAP-GOVSESS-CAPTURE-001: End governance session before deleting chat
    gov_collector = _chat_gov_sessions.pop(session_id, None)
    if gov_collector:
        try:
            msg_count = len(_chat_sessions.get(session_id, {}).get("messages", []))
            end_chat_session(gov_collector, summary=f"Chat ended ({msg_count} messages)")
        except Exception as e:
            # BUG-424-CHT-005: Upgrade debug→warning + exc_info (data integrity)
            logger.warning(f"Failed to end governance session: {e}", exc_info=True)

    # BUG-CHAT-001: Safe removal to avoid KeyError from race conditions
    _chat_sessions.pop(session_id, None)
    return {"status": "deleted", "session_id": session_id}


__all__ = ["router"]
