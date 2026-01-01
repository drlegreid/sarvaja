"""
Chat Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per ORCH-006: Agent Chat UI.

Created: 2024-12-28
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
    _sessions_store, generate_chat_session_id,
    get_available_agents_for_chat
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])

# =============================================================================
# DELEGATION PROTOCOL INTEGRATION (ORCH-006)
# =============================================================================

# Lazy-loaded protocol instance
_delegation_protocol = None
_orchestrator_engine = None


def _get_delegation_protocol():
    """
    Get or create the DelegationProtocol instance.

    Lazy initialization to avoid circular imports.
    """
    global _delegation_protocol, _orchestrator_engine

    if _delegation_protocol is not None:
        return _delegation_protocol

    try:
        from agent.orchestrator.delegation import DelegationProtocol
        from agent.orchestrator.engine import OrchestratorEngine, AgentInfo, AgentRole

        # Create a minimal orchestrator engine for delegation
        client = get_client()
        _orchestrator_engine = OrchestratorEngine(client)

        # Register agents from store
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
    """
    Delegate a task using the DelegationProtocol.

    Args:
        task_desc: Task description
        agent_id: Source agent ID

    Returns:
        Delegation result message
    """
    protocol = _get_delegation_protocol()
    if protocol is None:
        # Fallback to simple task creation
        task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
        _tasks_store[task_id] = {
            "task_id": task_id,
            "name": task_desc[:50],
            "description": task_desc,
            "status": "pending",
            "priority": "MEDIUM",
            "created_at": datetime.now().isoformat(),
        }
        return f"Task created: {task_id}\nDescription: {task_desc}\nStatus: Pending (DelegationProtocol not available)"

    try:
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

        # Delegate using protocol
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
        return f"Task created: {task_id}\nDelegation error: {str(e)}\nStatus: Pending manual assignment"


# =============================================================================
# CHAT COMMAND PROCESSING
# =============================================================================

def _process_chat_command(content: str, agent_id: str) -> str:
    """
    Process a chat command and return response.

    This is a simplified implementation. In production,
    this would use the DelegationProtocol to dispatch to agents.
    """
    content_lower = content.lower()

    # Get counts from stores (with safe defaults)
    tasks_count = len(_tasks_store) if _tasks_store else 0
    agents_count = len(_agents_store) if _agents_store else 0
    sessions_count = len(_sessions_store) if _sessions_store else 0

    # Try to get rules count from TypeDB
    rules_count = 0
    try:
        client = get_client()
        if client:
            rules = client.get_all_rules()
            rules_count = len(rules) if rules else 0
    except Exception:
        rules_count = 0

    # Command recognition
    if content_lower.startswith("/status"):
        return f"System Status:\n- Rules: {rules_count} loaded\n- Tasks: {tasks_count} total\n- Agents: {agents_count} registered\n- Sessions: {sessions_count} active"

    elif content_lower.startswith("/tasks"):
        pending = [t for t in _tasks_store.values() if t.get("status") == "pending"]
        if pending:
            task_list = "\n".join([f"- {t.get('task_id')}: {t.get('name')}" for t in pending[:5]])
            return f"Pending Tasks ({len(pending)} total):\n{task_list}"
        return "No pending tasks."

    elif content_lower.startswith("/rules"):
        try:
            client = get_client()
            if client:
                rules = client.get_all_rules()
                active = [r for r in rules if r.status == "ACTIVE"] if rules else []
                if active:
                    rule_list = "\n".join([f"- {r.id}: {r.name}" for r in active[:5]])
                    return f"Active Rules ({len(active)} total):\n{rule_list}"
        except Exception:
            pass
        return "No active rules found."

    elif content_lower.startswith("/help"):
        return """Available Commands:
- /status - Show system status
- /tasks - List pending tasks
- /rules - List active rules
- /agents - List available agents
- /search <query> - Search evidence
- /delegate <task> - Delegate a task
- /help - Show this help message

You can also type natural language commands and I'll do my best to help!"""

    elif content_lower.startswith("/agents"):
        agents = list(_agents_store.values())
        if agents:
            agent_list = "\n".join([f"- {a.get('agent_id')}: {a.get('name')} (trust: {a.get('trust_score', 0):.2f})" for a in agents[:5]])
            return f"Registered Agents ({len(agents)} total):\n{agent_list}"
        return "No agents registered."

    elif content_lower.startswith("/search"):
        query = content[7:].strip()
        if not query:
            return "Usage: /search <query>"
        # Simple search in rules and tasks
        results = []
        # Search rules from TypeDB
        try:
            client = get_client()
            if client:
                rules = client.get_all_rules() or []
                for rule in rules:
                    if query.lower() in (rule.name or "" + rule.directive or "").lower():
                        results.append(f"Rule: {rule.id} - {rule.name}")
        except Exception:
            pass
        # Search tasks from in-memory store
        for task in _tasks_store.values():
            if query.lower() in (task.get("name", "") + task.get("description", "")).lower():
                results.append(f"Task: {task.get('task_id')} - {task.get('name')}")
        if results:
            return f"Search Results for '{query}':\n" + "\n".join(results[:10])
        return f"No results found for '{query}'."

    elif content_lower.startswith("/delegate"):
        task_desc = content[9:].strip()
        if not task_desc:
            return "Usage: /delegate <task description>"
        # Return marker for async delegation (processed in endpoint)
        return f"__DELEGATE__:{task_desc}"

    else:
        # Natural language processing (simplified)
        if "status" in content_lower:
            return f"Current system status:\n- {rules_count} rules configured\n- {tasks_count} tasks tracked\n- {agents_count} agents available\n- All systems operational."
        elif "help" in content_lower:
            return "I can help you with governance tasks. Try commands like /status, /tasks, /rules, or just describe what you need!"
        else:
            return f"Received: '{content}'\n\nI'm here to help with governance tasks. Use /help to see available commands, or describe what you need in natural language."


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@router.post("/chat/send", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest):
    """
    Send a chat message to an agent.

    Per ORCH-006: Agent Chat UI.

    The message is processed by the orchestrator which:
    1. Analyzes the command
    2. Selects appropriate agent (or uses specified agent)
    3. Creates a task if needed
    4. Returns agent response
    """
    # Get or create session
    session_id = request.session_id
    if not session_id:
        session_id = generate_chat_session_id()
        _chat_sessions[session_id] = {
            "session_id": session_id,
            "messages": [],
            "active_task_id": None,
            "selected_agent_id": request.agent_id,
            "created_at": datetime.now().isoformat(),
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
        # Auto-select: prefer highest trust score
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

    # Process command and generate response
    response_content = _process_chat_command(request.content, agent_id)

    # Handle async delegation if needed (ORCH-006)
    if response_content.startswith("__DELEGATE__:"):
        task_desc = response_content[13:]  # Remove marker
        response_content = await _delegate_task_async(task_desc, agent_id)

    # Create response message
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

    # Update session
    _chat_sessions[session_id] = session

    return ChatMessageResponse(**response_msg)


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str):
    """
    Get a chat session by ID.

    Per ORCH-006: Agent Chat UI.
    """
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
    """
    List all chat sessions.

    Per ORCH-006: Agent Chat UI.
    """
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
    """
    Delete a chat session.

    Per ORCH-006: Agent Chat UI.
    """
    if session_id not in _chat_sessions:
        raise HTTPException(status_code=404, detail=f"Chat session {session_id} not found")

    del _chat_sessions[session_id]
    return {"status": "deleted", "session_id": session_id}
