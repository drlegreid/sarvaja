"""
Chat & Agent Interaction Handlers.

Per DOC-SIZE-01-v1: Extracted from common_handlers.py (404 lines).
Chat message sending, slash commands, and agent communication.
"""

import os
from typing import Any

import httpx

API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")


def register_chat_handlers(ctrl: Any, state: Any) -> None:
    """Register chat/agent interaction handlers."""

    @ctrl.trigger("send_chat_message")
    def send_chat_message() -> None:
        """Send a chat message to the selected agent."""
        if not state.chat_input or not state.chat_input.strip():
            return

        message = state.chat_input.strip()
        state.chat_input = ""

        # Add user message to history
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        state.chat_messages = state.chat_messages + [user_msg]

        # Process command or send to agent
        if message.startswith("/"):
            _process_chat_command(state, message)
        else:
            _send_to_agent(state, message)

    @ctrl.trigger("clear_chat")
    def clear_chat() -> None:
        """Clear chat history."""
        state.chat_messages = []


def _process_chat_command(state: Any, command: str) -> None:
    """Process a slash command."""
    cmd = command.lower().split()[0]
    responses = {
        "/help": "Available commands: /help, /status, /tasks, /rules, /agents",
        "/status": f"System status: {len(state.rules)} rules, {len(state.tasks)} tasks, {len(state.agents)} agents",
        "/tasks": f"Tasks: {len([t for t in state.tasks if t.get('status') == 'TODO'])} pending",
        "/rules": f"Rules: {len([r for r in state.rules if r.get('status') == 'ACTIVE'])} active",
        "/agents": f"Agents: {len(state.agents)} registered",
    }

    response = responses.get(cmd, f"Unknown command: {cmd}")
    bot_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }
    state.chat_messages = state.chat_messages + [bot_msg]


def _send_to_agent(state: Any, message: str) -> None:
    """Send message to selected agent via API."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{API_BASE_URL}/api/agents/{state.selected_chat_agent or 'claude-code'}/chat",
                json={"message": message}
            )
            if response.status_code == 200:
                result = response.json()
                bot_msg = {
                    "role": "assistant",
                    "content": result.get("response", "No response"),
                    "timestamp": __import__("datetime").datetime.now().isoformat()
                }
            else:
                bot_msg = {
                    "role": "assistant",
                    "content": f"Error: {response.status_code}",
                    "timestamp": __import__("datetime").datetime.now().isoformat()
                }
    except Exception as e:
        bot_msg = {
            "role": "assistant",
            "content": f"Connection error: {str(e)}",
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }

    state.chat_messages = state.chat_messages + [bot_msg]
