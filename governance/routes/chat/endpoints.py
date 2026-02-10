"""
Chat Routes Endpoints.

Per GAP-FILE-023: Refactored from routes/chat.py
Per DOC-SIZE-01-v1: Files under 400 lines

FastAPI endpoints for chat functionality.

Created: 2024-12-28
Refactored: 2026-01-14
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid
import logging

from governance.client import get_client
from governance.models import (
    ChatMessageRequest, ChatMessageResponse, ChatSessionResponse
)
from governance.stores import (
    _chat_sessions, _agents_store, _tasks_store,
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


logger = logging.getLogger(__name__)

# Track active governance sessions per chat session
_chat_gov_sessions: Dict[str, Any] = {}
router = APIRouter(tags=["Chat"])


# =============================================================================
# DELEGATION PROTOCOL INTEGRATION (ORCH-006)
# =============================================================================

_delegation_protocol = None
_orchestrator_engine = None


def _get_delegation_protocol():
    """Get or create the DelegationProtocol instance."""
    global _delegation_protocol, _orchestrator_engine

    if _delegation_protocol is not None:
        return _delegation_protocol

    try:
        from agent.orchestrator.delegation import DelegationProtocol
        from agent.orchestrator.engine import OrchestratorEngine, AgentInfo, AgentRole

        client = get_client()
        _orchestrator_engine = OrchestratorEngine(client)

        for agent_data in _agents_store.values():
            try:
                role = AgentRole(agent_data.get("agent_type", "research").lower())
            except ValueError:
                role = AgentRole.RESEARCH

            agent_info = AgentInfo(
                agent_id=agent_data.get("agent_id"),
                name=agent_data.get("name", "Unknown"),
                role=role,
                trust_score=agent_data.get("trust_score", 0.5),
            )
            _orchestrator_engine.register_agent(agent_info)

        _delegation_protocol = DelegationProtocol(_orchestrator_engine)
        logger.info("DelegationProtocol initialized for chat")
        return _delegation_protocol

    except Exception as e:
        logger.warning(f"DelegationProtocol not available: {e}")
        return None


async def _delegate_task_async(task_desc: str, agent_id: str) -> str:
    """Delegate a task using the DelegationProtocol."""
    protocol = _get_delegation_protocol()

    # Create task in store
    task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
    _tasks_store[task_id] = {
        "task_id": task_id,
        "name": task_desc[:50],
        "description": task_desc,
        "status": "pending",
        "priority": "MEDIUM",
        "created_at": datetime.now().isoformat(),
    }

    if protocol is None:
        return (
            f"Task created: {task_id}\n"
            f"Description: {task_desc}\n"
            f"Status: Pending (DelegationProtocol not available)"
        )

    try:
        result = await protocol.delegate_research(
            task_id=task_id,
            source_agent_id=agent_id,
            query=task_desc,
        )

        if result.success:
            _tasks_store[task_id]["status"] = "in_progress"
            _tasks_store[task_id]["agent_id"] = result.target_agent_id
            return (
                f"Task delegated successfully!\n"
                f"- Task ID: {task_id}\n"
                f"- Assigned to: {result.target_agent_id}\n"
                f"- Duration: {result.duration_ms}ms\n"
                f"- Message: {result.message}"
            )
        else:
            return (
                f"Delegation failed:\n"
                f"- Task ID: {task_id}\n"
                f"- Reason: {result.message}\n"
                f"- Status: Task remains pending"
            )
    except Exception as e:
        logger.error(f"Delegation error: {e}")
        return (
            f"Task created: {task_id}\n"
            f"Delegation error: {str(e)}\n"
            f"Status: Pending manual assignment"
        )


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
            logger.warning(f"Failed to preload context: {e}")
            context_dict = {}

        _chat_sessions[session_id] = {
            "session_id": session_id,
            "messages": [],
            "active_task_id": None,
            "selected_agent_id": request.agent_id,
            "created_at": datetime.now().isoformat(),
            "context": context_dict,
        }

    session = _chat_sessions.get(session_id, {
        "session_id": session_id,
        "messages": [],
        "active_task_id": None,
        "selected_agent_id": request.agent_id,
    })

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
    gov_collector = _chat_gov_sessions.get(session_id)
    if gov_collector is None:
        try:
            topic = request.content[:60] if request.content else "Chat session"
            gov_collector = start_chat_session(agent_id, topic)
            _chat_gov_sessions[session_id] = gov_collector
        except Exception as e:
            logger.warning(f"Failed to start governance session: {e}")

    # Process command
    import time as _time
    _cmd_start = _time.time()
    response_content = process_chat_command(request.content, agent_id)
    _cmd_duration = int((_time.time() - _cmd_start) * 1000)

    # Record tool call in governance session
    if gov_collector:
        try:
            record_chat_tool_call(
                gov_collector,
                tool_name=request.content.split()[0] if request.content else "chat",
                arguments={"content": request.content[:200]},
                result=response_content[:500],
                duration_ms=_cmd_duration,
            )
        except Exception as e:
            logger.debug(f"Failed to record chat tool call: {e}")

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
            logger.debug(f"Failed to record chat thought: {e}")

    # Handle async delegation
    if response_content.startswith("__DELEGATE__:"):
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
            logger.debug(f"Failed to end governance session: {e}")

    del _chat_sessions[session_id]
    return {"status": "deleted", "session_id": session_id}


__all__ = ["router"]
