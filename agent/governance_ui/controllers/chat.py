"""
Chat Controllers (GAP-FILE-005)
===============================
Controller functions for agent chat interface (ORCH-006).

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-005: Extracted from governance_dashboard.py

Created: 2024-12-28
"""

import httpx
from datetime import datetime
import uuid
from typing import Any

from agent.governance_ui.trace_bar.transforms import add_api_trace, add_error_trace

# Per antirot caps: prevent unbounded chat message growth
_MAX_CHAT_MESSAGES = 500


def _capped_messages(messages):
    """Return last _MAX_CHAT_MESSAGES to prevent memory leak."""
    if len(messages) > _MAX_CHAT_MESSAGES:
        return messages[-_MAX_CHAT_MESSAGES:]
    return messages


def register_chat_controllers(state: Any, ctrl: Any, api_base_url: str) -> None:
    """
    Register chat controllers with Trame.

    Args:
        state: Trame state object
        ctrl: Trame controller object
        api_base_url: Base URL for API calls
    """

    @ctrl.trigger("send_chat_message")
    def send_chat_message():
        """Send chat message to agent."""
        message = state.chat_input
        if not message or not message.strip():
            return

        # Clear input immediately
        state.chat_input = ""
        state.chat_loading = True

        try:
            # Add user message to UI immediately
            user_msg = {
                'id': f"MSG-{uuid.uuid4().hex[:8].upper()}",
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'status': 'complete',
            }
            messages = list(state.chat_messages or [])
            messages.append(user_msg)
            state.chat_messages = _capped_messages(messages)

            # Send to API
            with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
                payload = {
                    'content': message,
                    'agent_id': state.chat_selected_agent,
                    'session_id': state.chat_session_id,
                }
                response = client.post("/api/chat/send", json=payload)
                add_api_trace(state, "/api/chat/send", "POST", response.status_code, 0)
                if response.status_code == 200:
                    agent_msg = response.json()
                    agent_msg['timestamp'] = datetime.now().strftime("%H:%M:%S")
                    messages = list(state.chat_messages or [])
                    messages.append(agent_msg)
                    state.chat_messages = _capped_messages(messages)

                    if not state.chat_session_id and agent_msg.get('task_id'):
                        state.chat_task_id = agent_msg.get('task_id')
                else:
                    error_msg = {
                        'id': f"MSG-{uuid.uuid4().hex[:8].upper()}",
                        'role': 'system',
                        'content': f"Error: {response.text}",
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'status': 'error',
                    }
                    messages = list(state.chat_messages or [])
                    messages.append(error_msg)
                    state.chat_messages = _capped_messages(messages)
        except Exception as e:
            add_error_trace(state, f"Chat send failed: {e}", "/api/chat/send")
            error_msg = {
                'id': f"MSG-{uuid.uuid4().hex[:8].upper()}",
                'role': 'system',
                'content': f"Connection error: {str(e)}",
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'status': 'error',
            }
            messages = list(state.chat_messages or [])
            messages.append(error_msg)
            state.chat_messages = _capped_messages(messages)
        finally:
            state.chat_loading = False

    @ctrl.trigger("clear_chat")
    def clear_chat():
        """Clear chat history."""
        state.chat_messages = []
        state.chat_session_id = None
        state.chat_task_id = None

    @ctrl.trigger("load_file_content")
    def load_file_content(path: str):
        """Load file content for viewing (GAP-DATA-003)."""
        if not path:
            return

        state.show_file_viewer = True
        state.file_viewer_path = path
        state.file_viewer_loading = True
        state.file_viewer_error = ""
        state.file_viewer_content = ""
        state.file_viewer_html = ""

        try:
            with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
                response = client.get(
                    "/api/files/content",
                    params={"path": path}
                )
                if response.status_code == 200:
                    data = response.json()
                    state.file_viewer_content = data.get("content", "")
                    # Use rendered HTML for markdown files
                    state.file_viewer_html = data.get("rendered_html", "")
                else:
                    try:
                        error_detail = response.json().get("detail", f"HTTP {response.status_code}")
                    except Exception:
                        error_detail = f"HTTP {response.status_code}"
                    state.file_viewer_error = error_detail
        except Exception as e:
            add_error_trace(state, f"Load file failed: {e}", "/api/files/content")
            state.file_viewer_error = str(e)
        finally:
            state.file_viewer_loading = False

    @ctrl.trigger("load_task_execution")
    def load_task_execution(task_id: str):
        """Load task execution history (ORCH-007)."""
        if not task_id:
            return

        state.task_execution_loading = True
        state.task_execution_log = []
        state.show_task_execution = True

        try:
            with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
                response = client.get(f"/api/tasks/{task_id}/execution")
                if response.status_code == 200:
                    data = response.json()
                    state.task_execution_log = data.get("events", [])
                else:
                    state.task_execution_log = []
        except Exception as e:
            add_error_trace(state, f"Load execution failed: {e}", f"/api/tasks/{task_id}/execution")
            state.task_execution_log = []
        finally:
            state.task_execution_loading = False
