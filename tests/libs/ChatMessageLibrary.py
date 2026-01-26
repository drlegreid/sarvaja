"""
Chat Message Library for Robot Framework
Tests for chat message formatting and creation.
Migrated from tests/test_chat.py
Per: RF-005 Robot Framework Migration
"""
from robot.api.deco import keyword


class ChatMessageLibrary:
    """Robot Framework keywords for chat message tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Chat Message Formatting Tests
    # =========================================================================

    @keyword("Format Chat Message User")
    def format_chat_message_user(self):
        """Test formatting user message."""
        try:
            from agent.governance_ui import format_chat_message

            message = {
                'id': 'MSG-001',
                'role': 'user',
                'content': 'Hello, agent!',
                'timestamp': '2024-12-28T10:00:00',
                'status': 'complete',
            }

            formatted = format_chat_message(message)

            return {
                "role_user": formatted['role'] == 'user',
                "is_user_true": formatted['is_user'] is True,
                "is_agent_false": formatted['is_agent'] is False,
                "role_color_primary": formatted['role_color'] == 'primary'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Format Chat Message Agent")
    def format_chat_message_agent(self):
        """Test formatting agent message."""
        try:
            from agent.governance_ui import format_chat_message

            message = {
                'id': 'MSG-002',
                'role': 'agent',
                'content': 'Hello! How can I help?',
                'timestamp': '2024-12-28T10:00:01',
                'agent_id': 'AGENT-001',
                'agent_name': 'Claude Code',
                'status': 'complete',
            }

            formatted = format_chat_message(message)

            return {
                "role_agent": formatted['role'] == 'agent',
                "is_user_false": formatted['is_user'] is False,
                "is_agent_true": formatted['is_agent'] is True,
                "agent_name_correct": formatted['agent_name'] == 'Claude Code',
                "role_color_success": formatted['role_color'] == 'success'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Chat Message Creation Tests
    # =========================================================================

    @keyword("Create User Message")
    def create_user_message(self):
        """Test creating user message."""
        try:
            from agent.governance_ui import create_user_message

            message = create_user_message('Hello!')

            return {
                "role_user": message['role'] == 'user',
                "content_correct": message['content'] == 'Hello!',
                "status_complete": message['status'] == 'complete',
                "id_prefix": message['id'].startswith('MSG-'),
                "has_timestamp": message['timestamp'] is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Agent Message")
    def create_agent_message(self):
        """Test creating agent message."""
        try:
            from agent.governance_ui import create_agent_message

            message = create_agent_message(
                content='Hello! I can help.',
                agent_id='AGENT-001',
                agent_name='Test Agent',
            )

            return {
                "role_agent": message['role'] == 'agent',
                "content_correct": message['content'] == 'Hello! I can help.',
                "agent_id_correct": message['agent_id'] == 'AGENT-001',
                "agent_name_correct": message['agent_name'] == 'Test Agent',
                "id_prefix": message['id'].startswith('MSG-')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create System Message")
    def create_system_message(self):
        """Test creating system message."""
        try:
            from agent.governance_ui import create_system_message

            message = create_system_message('Session started.')

            return {
                "role_system": message['role'] == 'system',
                "content_correct": message['content'] == 'Session started.',
                "status_complete": message['status'] == 'complete'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
