"""
Chat Command Processing.

Per GAP-FILE-023: Extracted from routes/chat.py
Per DOC-SIZE-01-v1: Files under 400 lines

Handles chat command parsing and response generation.

Created: 2024-12-28
Refactored: 2026-01-14
"""

from governance.client import get_client
from governance.stores import _tasks_store, _agents_store, _sessions_store
from governance.context_preloader import preload_session_context


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
    except Exception:
        rules_count = 0

    # Command recognition
    if content_lower.startswith("/status"):
        return (
            f"System Status:\n"
            f"- Rules: {rules_count} loaded\n"
            f"- Tasks: {tasks_count} total\n"
            f"- Agents: {agents_count} registered\n"
            f"- Sessions: {sessions_count} active"
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
        except Exception:
            pass
        return "No active rules found."

    elif content_lower.startswith("/help"):
        return """Available Commands:
- /status - Show system status
- /tasks - List pending tasks
- /rules - List active rules
- /agents - List available agents
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
            return (
                f"Current system status:\n"
                f"- {rules_count} rules configured\n"
                f"- {tasks_count} tasks tracked\n"
                f"- {agents_count} agents available\n"
                f"- All systems operational."
            )
        elif "help" in content_lower:
            return (
                "I can help you with governance tasks. "
                "Try commands like /status, /tasks, /rules, "
                "or just describe what you need!"
            )
        else:
            return (
                f"Received: '{content}'\n\n"
                "I'm here to help with governance tasks. "
                "Use /help to see available commands, "
                "or describe what you need in natural language."
            )


__all__ = ["process_chat_command"]
