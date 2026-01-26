"""
Chat API Library for Robot Framework
Tests for chat API models and command processing.
Migrated from tests/test_chat.py
Per: RF-005 Robot Framework Migration
"""
from robot.api.deco import keyword


class ChatAPILibrary:
    """Robot Framework keywords for chat API tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Chat API Models Tests
    # =========================================================================

    @keyword("Chat Message Request Model")
    def chat_message_request_model(self):
        """Test ChatMessageRequest model."""
        try:
            from governance.models import ChatMessageRequest

            request = ChatMessageRequest(
                content='/status',
                agent_id='AGENT-001',
                session_id='CHAT-001',
            )

            return {
                "content_correct": request.content == '/status',
                "agent_id_correct": request.agent_id == 'AGENT-001',
                "session_id_correct": request.session_id == 'CHAT-001'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chat Message Request Defaults")
    def chat_message_request_defaults(self):
        """Test ChatMessageRequest with defaults."""
        try:
            from governance.models import ChatMessageRequest

            request = ChatMessageRequest(content='Hello')

            return {
                "content_correct": request.content == 'Hello',
                "agent_id_none": request.agent_id is None,
                "session_id_none": request.session_id is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Chat Message Response Model")
    def chat_message_response_model(self):
        """Test ChatMessageResponse model."""
        try:
            from governance.models import ChatMessageResponse

            response = ChatMessageResponse(
                id='MSG-001',
                role='agent',
                content='Hello!',
                timestamp='2024-12-28T10:00:00',
                agent_id='AGENT-001',
                agent_name='Test Agent',
                status='complete',
            )

            return {
                "id_correct": response.id == 'MSG-001',
                "role_correct": response.role == 'agent',
                "agent_name_correct": response.agent_name == 'Test Agent'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Chat Command Processing Tests
    # =========================================================================

    @keyword("Help Command Processing")
    def help_command_processing(self):
        """Test processing /help command."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command('/help', 'AGENT-001')

            return {
                "has_available_commands": 'Available Commands' in response,
                "has_status_command": '/status' in response,
                "has_tasks_command": '/tasks' in response
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Status Command Processing")
    def status_command_processing(self):
        """Test processing /status command."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command('/status', 'AGENT-001')

            return {
                "has_status_info": 'System Status' in response or 'status' in response.lower()
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Tasks Command Processing")
    def tasks_command_processing(self):
        """Test processing /tasks command."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command('/tasks', 'AGENT-001')

            return {"has_task_info": 'task' in response.lower()}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rules Command Processing")
    def rules_command_processing(self):
        """Test processing /rules command."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command('/rules', 'AGENT-001')

            return {"has_rule_info": 'rule' in response.lower()}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Agents Command Processing")
    def agents_command_processing(self):
        """Test processing /agents command."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command('/agents', 'AGENT-001')

            return {"has_agent_info": 'agent' in response.lower()}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Search Command No Query")
    def search_command_no_query(self):
        """Test processing /search without query."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command('/search', 'AGENT-001')

            return {"has_usage_or_search": 'Usage' in response or 'search' in response.lower()}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Delegate Command No Task")
    def delegate_command_no_task(self):
        """Test processing /delegate without task."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command('/delegate', 'AGENT-001')

            return {"has_usage_or_delegate": 'Usage' in response or 'delegate' in response.lower()}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Natural Language Fallback")
    def natural_language_fallback(self):
        """Test natural language processing."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command('What is the current status?', 'AGENT-001')

            return {"has_response": len(response) > 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
