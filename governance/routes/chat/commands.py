"""
Chat Command Processing.

Per GAP-FILE-023: Extracted from routes/chat.py
Per DOC-SIZE-01-v1: Files under 400 lines
Per PLAN-UI-OVERHAUL-001 Task 3.5: LLM integration for natural language.

Handles chat command parsing and response generation.

Created: 2024-12-28
Refactored: 2026-01-14
Updated: 2026-01-30 - LLM integration via LiteLLM
"""
import logging
import os

logger = logging.getLogger(__name__)

from governance.client import get_client
from governance.stores import _tasks_store, _agents_store, _sessions_store
from governance.context_preloader import preload_session_context
from governance.services.sessions import list_sessions

# LiteLLM proxy configuration
LITELLM_BASE_URL = os.environ.get("LITELLM_BASE_URL", "http://litellm:4000")
LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", "sk-litellm-dev-key")
LLM_MODEL = os.environ.get("MODEL_NAME", "claude-sonnet")

GOVERNANCE_SYSTEM_PROMPT = (
    "You are a governance assistant for the Sarvaja platform (multi-agent governance with TypeDB). "
    "You help users understand rules, tasks, sessions, decisions, and agent trust scores. "
    "Keep responses concise and actionable. "
    "Available commands: /status, /tasks, /rules, /agents, /sessions, /context, /search, /delegate. "
    "If you don't know something, suggest using /help for available commands."
)


def query_llm(message: str, system_prompt: str = "") -> str:
    """
    Query LLM via LiteLLM proxy for natural language chat responses.

    Falls back to a helpful message if LiteLLM is unavailable.
    """
    try:
        import httpx
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        resp = httpx.post(
            f"{LITELLM_BASE_URL}/v1/chat/completions",
            json={"model": LLM_MODEL, "messages": messages, "max_tokens": 2048},
            headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
            timeout=30.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        logger.warning(f"LLM query failed: HTTP {resp.status_code} - {resp.text[:200]}")
        return (
            f"LLM returned an error (HTTP {resp.status_code}). "
            "Use /help to see available commands, or try again later."
        )
    except Exception as e:
        logger.warning(f"LLM query error: {e}")

    return (
        "Cannot reach the LLM service (LiteLLM proxy). "
        "Check that the LiteLLM container is running. "
        "Use /help to see available commands."
    )


def process_chat_command(content: str, agent_id: str) -> str:
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
    except Exception as e:
        logger.debug(f"Failed to query rules for chat context: {e}")
        rules_count = 0

    # Command recognition
    if content_lower.startswith("/status"):
        # GAP-CHAT-COUNT-001: Use service layer for authoritative count
        try:
            result = list_sessions(limit=1)
            total_sessions = result.get("pagination", {}).get("total", sessions_count)
        except Exception:
            total_sessions = sessions_count
        return (
            f"System Status:\n"
            f"- Rules: {rules_count} loaded\n"
            f"- Tasks: {tasks_count} total\n"
            f"- Agents: {agents_count} registered\n"
            f"- Sessions: {total_sessions} total"
        )

    elif content_lower.startswith("/tasks"):
        pending = [t for t in _tasks_store.values() if t.get("status") == "pending"]
        if pending:
            task_list = "\n".join([
                f"- {t.get('task_id')}: {t.get('name')}"
                for t in pending[:5]
            ])
            return f"Pending Tasks ({len(pending)} total):\n{task_list}"
        return "No pending tasks."

    elif content_lower.startswith("/rules"):
        try:
            client = get_client()
            if client:
                rules = client.get_all_rules()
                active = [r for r in rules if r.status == "ACTIVE"] if rules else []
                if active:
                    rule_list = "\n".join([
                        f"- {r.id}: {r.name}"
                        for r in active[:5]
                    ])
                    return f"Active Rules ({len(active)} total):\n{rule_list}"
        except Exception as e:
            logger.debug(f"Failed to query active rules: {e}")
        return "No active rules found."

    elif content_lower.startswith("/help"):
        return """Available Commands:
- /status - Show system status
- /tasks - List pending tasks
- /rules - List active rules
- /agents - List available agents
- /sessions - List recent sessions
- /context - Show loaded strategic context
- /search <query> - Search evidence
- /delegate <task> - Delegate a task
- /help - Show this help message

You can also type natural language commands and I'll do my best to help!"""

    elif content_lower.startswith("/context"):
        # P12.6: Show preloaded context
        try:
            context = preload_session_context()
            return context.to_agent_prompt()
        except Exception as e:
            return f"Failed to load context: {str(e)}"

    elif content_lower.startswith("/sessions"):
        # Query TypeDB via service layer (with in-memory fallback)
        try:
            result = list_sessions(sort_by="started_at", order="desc", limit=10)
            sessions = result.get("items", [])
            total = result.get("pagination", {}).get("total", len(sessions))
        except Exception as e:
            logger.debug(f"Service layer session query failed: {e}")
            sessions = sorted(
                _sessions_store.values(),
                key=lambda s: s.get("start_time", ""),
                reverse=True,
            )[:10]
            total = len(_sessions_store)

        if sessions:
            active_count = sum(1 for s in sessions if s.get("status") == "ACTIVE")
            session_list = "\n".join([
                f"- {s.get('session_id', 'unknown')}: "
                f"{s.get('status', 'UNKNOWN')} | "
                f"agent: {s.get('agent_id', 'none')} | "
                f"started: {s.get('start_time', 'N/A')[:16]}"
                + (f"\n  evidence: {len(s.get('evidence_files', []))} files"
                   if s.get("evidence_files") else "")
                for s in sessions
            ])
            return (
                f"Sessions ({total} total, {active_count} active):\n{session_list}"
            )
        return "No sessions found. Sessions are created when agents perform work."

    elif content_lower.startswith("/agents"):
        agents = list(_agents_store.values())
        if agents:
            agent_list = "\n".join([
                f"- {a.get('agent_id')}: {a.get('name')} (trust: {a.get('trust_score', 0):.2f})"
                for a in agents[:5]
            ])
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
        except Exception as e:
            logger.debug(f"Failed to search rules: {e}")
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
        # Natural language processing via LLM (PLAN-UI-OVERHAUL-001 Task 3.5)
        # A.3: Enriched context with active tasks, recent sessions, available commands
        active_tasks = [
            t for t in _tasks_store.values()
            if t.get("status") in ("pending", "IN_PROGRESS", "in_progress")
        ]
        active_task_summary = ""
        if active_tasks:
            active_task_summary = "\n\nActive tasks:\n" + "\n".join(
                f"- {t.get('task_id')}: {t.get('name')} ({t.get('status')})"
                for t in active_tasks[:5]
            )

        recent_sessions_summary = ""
        try:
            sr = list_sessions(sort_by="started_at", order="desc", limit=5)
            recent = sr.get("items", [])
            if recent:
                recent_sessions_summary = "\n\nRecent sessions:\n" + "\n".join(
                    f"- {s.get('session_id')}: {s.get('status')} "
                    f"(agent: {s.get('agent_id', 'none')})"
                    for s in recent
                )
        except Exception:
            pass

        context = (
            f"{GOVERNANCE_SYSTEM_PROMPT}\n\n"
            f"Platform context: {rules_count} rules, {tasks_count} tasks, "
            f"{agents_count} agents, {sessions_count} sessions."
            f"{active_task_summary}"
            f"{recent_sessions_summary}"
        )
        return query_llm(content, system_prompt=context)


__all__ = ["process_chat_command", "query_llm"]
