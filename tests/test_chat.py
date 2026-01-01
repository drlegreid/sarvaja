"""
Tests for Agent Chat (ORCH-006).

Per RULE-023: Test Coverage Protocol
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch


# =============================================================================
# Chat State Tests
# =============================================================================

class TestChatStateConstants:
    """Test chat state constants."""

    def test_role_colors_defined(self):
        """Chat role colors are defined."""
        from agent.governance_ui import CHAT_ROLE_COLORS

        assert 'user' in CHAT_ROLE_COLORS
        assert 'agent' in CHAT_ROLE_COLORS
        assert 'system' in CHAT_ROLE_COLORS
        assert 'error' in CHAT_ROLE_COLORS

    def test_status_icons_defined(self):
        """Chat status icons are defined."""
        from agent.governance_ui import CHAT_STATUS_ICONS

        assert 'pending' in CHAT_STATUS_ICONS
        assert 'processing' in CHAT_STATUS_ICONS
        assert 'complete' in CHAT_STATUS_ICONS
        assert 'error' in CHAT_STATUS_ICONS


class TestChatStateTransforms:
    """Test chat state pure transforms."""

    def test_with_chat_messages(self):
        """Set chat messages."""
        from agent.governance_ui import with_chat_messages

        state = {'chat_messages': []}
        messages = [{'id': 'MSG-1', 'role': 'user', 'content': 'Hello'}]
        new_state = with_chat_messages(state, messages)

        assert new_state['chat_messages'] == messages
        assert state['chat_messages'] == []  # Original unchanged

    def test_with_chat_message_append(self):
        """Append a chat message."""
        from agent.governance_ui import with_chat_message

        state = {'chat_messages': [{'id': 'MSG-1', 'role': 'user', 'content': 'Hello'}]}
        message = {'id': 'MSG-2', 'role': 'agent', 'content': 'Hi there!'}
        new_state = with_chat_message(state, message)

        assert len(new_state['chat_messages']) == 2
        assert new_state['chat_messages'][1] == message

    def test_with_chat_loading(self):
        """Set chat loading state."""
        from agent.governance_ui import with_chat_loading

        state = {'chat_loading': False}
        new_state = with_chat_loading(state, True)

        assert new_state['chat_loading'] is True

    def test_with_chat_input(self):
        """Set chat input text."""
        from agent.governance_ui import with_chat_input

        state = {'chat_input': ''}
        new_state = with_chat_input(state, '/help')

        assert new_state['chat_input'] == '/help'

    def test_with_chat_agent(self):
        """Set selected chat agent."""
        from agent.governance_ui import with_chat_agent

        state = {'chat_selected_agent': None}
        new_state = with_chat_agent(state, 'AGENT-001')

        assert new_state['chat_selected_agent'] == 'AGENT-001'

    def test_with_chat_session(self):
        """Set chat session ID."""
        from agent.governance_ui import with_chat_session

        state = {'chat_session_id': None}
        new_state = with_chat_session(state, 'CHAT-ABC12345')

        assert new_state['chat_session_id'] == 'CHAT-ABC12345'

    def test_with_chat_task(self):
        """Set chat task ID."""
        from agent.governance_ui import with_chat_task

        state = {'chat_task_id': None}
        new_state = with_chat_task(state, 'TASK-001')

        assert new_state['chat_task_id'] == 'TASK-001'


class TestChatHelpers:
    """Test chat helper functions."""

    def test_get_chat_role_color(self):
        """Get color for chat role."""
        from agent.governance_ui import get_chat_role_color

        assert get_chat_role_color('user') == 'primary'
        assert get_chat_role_color('agent') == 'success'
        assert get_chat_role_color('system') == 'grey'
        assert get_chat_role_color('error') == 'error'
        assert get_chat_role_color('unknown') == 'grey'  # Default

    def test_get_chat_status_icon(self):
        """Get icon for chat status."""
        from agent.governance_ui import get_chat_status_icon

        assert 'clock' in get_chat_status_icon('pending')
        assert 'loading' in get_chat_status_icon('processing')
        assert 'check' in get_chat_status_icon('complete')
        assert 'alert' in get_chat_status_icon('error')


class TestChatMessageFormatting:
    """Test chat message formatting."""

    def test_format_chat_message_user(self):
        """Format user message."""
        from agent.governance_ui import format_chat_message

        message = {
            'id': 'MSG-001',
            'role': 'user',
            'content': 'Hello, agent!',
            'timestamp': '2024-12-28T10:00:00',
            'status': 'complete',
        }

        formatted = format_chat_message(message)

        assert formatted['role'] == 'user'
        assert formatted['is_user'] is True
        assert formatted['is_agent'] is False
        assert formatted['role_color'] == 'primary'

    def test_format_chat_message_agent(self):
        """Format agent message."""
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

        assert formatted['role'] == 'agent'
        assert formatted['is_user'] is False
        assert formatted['is_agent'] is True
        assert formatted['agent_name'] == 'Claude Code'
        assert formatted['role_color'] == 'success'


class TestChatMessageCreation:
    """Test chat message creation functions."""

    def test_create_user_message(self):
        """Create user message."""
        from agent.governance_ui import create_user_message

        message = create_user_message('Hello!')

        assert message['role'] == 'user'
        assert message['content'] == 'Hello!'
        assert message['status'] == 'complete'
        assert message['id'].startswith('MSG-')
        assert message['timestamp'] is not None

    def test_create_agent_message(self):
        """Create agent message."""
        from agent.governance_ui import create_agent_message

        message = create_agent_message(
            content='Hello! I can help.',
            agent_id='AGENT-001',
            agent_name='Test Agent',
        )

        assert message['role'] == 'agent'
        assert message['content'] == 'Hello! I can help.'
        assert message['agent_id'] == 'AGENT-001'
        assert message['agent_name'] == 'Test Agent'
        assert message['id'].startswith('MSG-')

    def test_create_system_message(self):
        """Create system message."""
        from agent.governance_ui import create_system_message

        message = create_system_message('Session started.')

        assert message['role'] == 'system'
        assert message['content'] == 'Session started.'
        assert message['status'] == 'complete'


# =============================================================================
# Chat API Tests
# =============================================================================

class TestChatAPIModels:
    """Test chat API Pydantic models."""

    def test_chat_message_request(self):
        """ChatMessageRequest model."""
        from governance.api import ChatMessageRequest

        request = ChatMessageRequest(
            content='/status',
            agent_id='AGENT-001',
            session_id='CHAT-001',
        )

        assert request.content == '/status'
        assert request.agent_id == 'AGENT-001'
        assert request.session_id == 'CHAT-001'

    def test_chat_message_request_defaults(self):
        """ChatMessageRequest with defaults."""
        from governance.api import ChatMessageRequest

        request = ChatMessageRequest(content='Hello')

        assert request.content == 'Hello'
        assert request.agent_id is None
        assert request.session_id is None

    def test_chat_message_response(self):
        """ChatMessageResponse model."""
        from governance.api import ChatMessageResponse

        response = ChatMessageResponse(
            id='MSG-001',
            role='agent',
            content='Hello!',
            timestamp='2024-12-28T10:00:00',
            agent_id='AGENT-001',
            agent_name='Test Agent',
            status='complete',
        )

        assert response.id == 'MSG-001'
        assert response.role == 'agent'
        assert response.agent_name == 'Test Agent'


class TestChatCommandProcessing:
    """Test chat command processing."""

    def test_help_command(self):
        """Process /help command."""
        from governance.api import _process_chat_command

        response = _process_chat_command('/help', 'AGENT-001')

        assert 'Available Commands' in response
        assert '/status' in response
        assert '/tasks' in response

    def test_status_command(self):
        """Process /status command."""
        from governance.api import _process_chat_command

        response = _process_chat_command('/status', 'AGENT-001')

        assert 'System Status' in response or 'status' in response.lower()

    def test_tasks_command(self):
        """Process /tasks command."""
        from governance.api import _process_chat_command

        response = _process_chat_command('/tasks', 'AGENT-001')

        # Either shows tasks or "No pending tasks"
        assert 'task' in response.lower()

    def test_rules_command(self):
        """Process /rules command."""
        from governance.api import _process_chat_command

        response = _process_chat_command('/rules', 'AGENT-001')

        assert 'rule' in response.lower()

    def test_agents_command(self):
        """Process /agents command."""
        from governance.api import _process_chat_command

        response = _process_chat_command('/agents', 'AGENT-001')

        assert 'agent' in response.lower()

    def test_search_command_no_query(self):
        """Process /search without query."""
        from governance.api import _process_chat_command

        response = _process_chat_command('/search', 'AGENT-001')

        assert 'Usage' in response or 'search' in response.lower()

    def test_delegate_command_no_task(self):
        """Process /delegate without task."""
        from governance.api import _process_chat_command

        response = _process_chat_command('/delegate', 'AGENT-001')

        assert 'Usage' in response or 'delegate' in response.lower()

    def test_natural_language_fallback(self):
        """Natural language processing."""
        from governance.api import _process_chat_command

        response = _process_chat_command('What is the current status?', 'AGENT-001')

        assert len(response) > 0  # Returns some response


class TestChatSessionManagement:
    """Test chat session management."""

    def test_generate_session_id(self):
        """Generate chat session ID."""
        from governance.api import _generate_chat_session_id

        session_id = _generate_chat_session_id()

        assert session_id.startswith('CHAT-')
        assert len(session_id) > 5

    def test_generate_unique_session_ids(self):
        """Session IDs are unique."""
        from governance.api import _generate_chat_session_id

        ids = [_generate_chat_session_id() for _ in range(10)]

        assert len(set(ids)) == 10  # All unique


# =============================================================================
# Integration Tests
# =============================================================================

class TestChatIntegration:
    """Integration tests for chat functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from governance.api import app

        return TestClient(app)

    def test_send_message_creates_session(self, client):
        """Sending message creates new session."""
        response = client.post("/api/chat/send", json={
            "content": "/help",
        })

        assert response.status_code == 200
        data = response.json()
        assert data['role'] == 'agent'
        assert 'Available Commands' in data['content']

    def test_send_message_with_agent(self, client):
        """Send message to specific agent."""
        response = client.post("/api/chat/send", json={
            "content": "/status",
            "agent_id": "AGENT-001",
        })

        assert response.status_code == 200
        data = response.json()
        assert data['agent_id'] is not None

    def test_list_chat_sessions(self, client):
        """List chat sessions."""
        # Create a session first
        client.post("/api/chat/send", json={"content": "test"})

        response = client.get("/api/chat/sessions")

        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)

    def test_get_nonexistent_session(self, client):
        """Get nonexistent session returns 404."""
        response = client.get("/api/chat/sessions/NONEXISTENT")

        assert response.status_code == 404
