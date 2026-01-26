"""
Chat State Library for Robot Framework
Tests for chat state constants, transforms, and helpers.
Migrated from tests/test_chat.py
Per: RF-005 Robot Framework Migration
"""
from robot.api.deco import keyword


class ChatStateLibrary:
    """Robot Framework keywords for chat state tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Chat State Constants Tests
    # =========================================================================

    @keyword("Role Colors Defined")
    def role_colors_defined(self):
        """Test that chat role colors are defined."""
        try:
            from agent.governance_ui import CHAT_ROLE_COLORS

            return {
                "has_user": 'user' in CHAT_ROLE_COLORS,
                "has_agent": 'agent' in CHAT_ROLE_COLORS,
                "has_system": 'system' in CHAT_ROLE_COLORS,
                "has_error": 'error' in CHAT_ROLE_COLORS
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Status Icons Defined")
    def status_icons_defined(self):
        """Test that chat status icons are defined."""
        try:
            from agent.governance_ui import CHAT_STATUS_ICONS

            return {
                "has_pending": 'pending' in CHAT_STATUS_ICONS,
                "has_processing": 'processing' in CHAT_STATUS_ICONS,
                "has_complete": 'complete' in CHAT_STATUS_ICONS,
                "has_error": 'error' in CHAT_STATUS_ICONS
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Chat State Transforms Tests
    # =========================================================================

    @keyword("With Chat Messages Transform")
    def with_chat_messages_transform(self):
        """Test setting chat messages."""
        try:
            from agent.governance_ui import with_chat_messages

            state = {'chat_messages': []}
            messages = [{'id': 'MSG-1', 'role': 'user', 'content': 'Hello'}]
            new_state = with_chat_messages(state, messages)

            return {
                "new_state_correct": new_state['chat_messages'] == messages,
                "original_unchanged": state['chat_messages'] == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Chat Message Append")
    def with_chat_message_append(self):
        """Test appending a chat message."""
        try:
            from agent.governance_ui import with_chat_message

            state = {'chat_messages': [{'id': 'MSG-1', 'role': 'user', 'content': 'Hello'}]}
            message = {'id': 'MSG-2', 'role': 'agent', 'content': 'Hi there!'}
            new_state = with_chat_message(state, message)

            return {
                "length_increased": len(new_state['chat_messages']) == 2,
                "message_appended": new_state['chat_messages'][1] == message
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Chat Loading Transform")
    def with_chat_loading_transform(self):
        """Test setting chat loading state."""
        try:
            from agent.governance_ui import with_chat_loading

            state = {'chat_loading': False}
            new_state = with_chat_loading(state, True)

            return {"loading_set": new_state['chat_loading'] is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Chat Input Transform")
    def with_chat_input_transform(self):
        """Test setting chat input text."""
        try:
            from agent.governance_ui import with_chat_input

            state = {'chat_input': ''}
            new_state = with_chat_input(state, '/help')

            return {"input_set": new_state['chat_input'] == '/help'}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Chat Agent Transform")
    def with_chat_agent_transform(self):
        """Test setting selected chat agent."""
        try:
            from agent.governance_ui import with_chat_agent

            state = {'chat_selected_agent': None}
            new_state = with_chat_agent(state, 'AGENT-001')

            return {"agent_set": new_state['chat_selected_agent'] == 'AGENT-001'}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Chat Session Transform")
    def with_chat_session_transform(self):
        """Test setting chat session ID."""
        try:
            from agent.governance_ui import with_chat_session

            state = {'chat_session_id': None}
            new_state = with_chat_session(state, 'CHAT-ABC12345')

            return {"session_set": new_state['chat_session_id'] == 'CHAT-ABC12345'}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("With Chat Task Transform")
    def with_chat_task_transform(self):
        """Test setting chat task ID."""
        try:
            from agent.governance_ui import with_chat_task

            state = {'chat_task_id': None}
            new_state = with_chat_task(state, 'TASK-001')

            return {"task_set": new_state['chat_task_id'] == 'TASK-001'}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Chat Helper Functions Tests
    # =========================================================================

    @keyword("Get Chat Role Color")
    def get_chat_role_color(self):
        """Test getting color for chat role."""
        try:
            from agent.governance_ui import get_chat_role_color

            return {
                "user_primary": get_chat_role_color('user') == 'primary',
                "agent_success": get_chat_role_color('agent') == 'success',
                "system_grey": get_chat_role_color('system') == 'grey',
                "error_error": get_chat_role_color('error') == 'error',
                "unknown_default": get_chat_role_color('unknown') == 'grey'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Chat Status Icon")
    def get_chat_status_icon(self):
        """Test getting icon for chat status."""
        try:
            from agent.governance_ui import get_chat_status_icon

            return {
                "pending_clock": 'clock' in get_chat_status_icon('pending'),
                "processing_loading": 'loading' in get_chat_status_icon('processing'),
                "complete_check": 'check' in get_chat_status_icon('complete'),
                "error_alert": 'alert' in get_chat_status_icon('error')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
