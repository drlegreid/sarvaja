"""
Tests for Task Execution Viewer (ORCH-007).

Per RULE-023: Test Coverage Protocol
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# =============================================================================
# Import Tests
# =============================================================================

class TestTaskExecutionImports:
    """Test task execution module imports."""

    def test_import_execution_event_types(self):
        """Import EXECUTION_EVENT_TYPES constant."""
        from agent.governance_ui import EXECUTION_EVENT_TYPES

        assert 'claimed' in EXECUTION_EVENT_TYPES
        assert 'started' in EXECUTION_EVENT_TYPES
        assert 'completed' in EXECUTION_EVENT_TYPES
        assert 'failed' in EXECUTION_EVENT_TYPES
        assert 'evidence' in EXECUTION_EVENT_TYPES

    def test_import_with_task_execution_log(self):
        """Import with_task_execution_log transform."""
        from agent.governance_ui import with_task_execution_log

        assert callable(with_task_execution_log)

    def test_import_with_task_execution_loading(self):
        """Import with_task_execution_loading transform."""
        from agent.governance_ui import with_task_execution_loading

        assert callable(with_task_execution_loading)

    def test_import_with_task_execution_event(self):
        """Import with_task_execution_event transform."""
        from agent.governance_ui import with_task_execution_event

        assert callable(with_task_execution_event)

    def test_import_clear_task_execution(self):
        """Import clear_task_execution transform."""
        from agent.governance_ui import clear_task_execution

        assert callable(clear_task_execution)

    def test_import_get_execution_event_style(self):
        """Import get_execution_event_style helper."""
        from agent.governance_ui import get_execution_event_style

        assert callable(get_execution_event_style)

    def test_import_format_execution_event(self):
        """Import format_execution_event helper."""
        from agent.governance_ui import format_execution_event

        assert callable(format_execution_event)


# =============================================================================
# State Transform Tests
# =============================================================================

class TestExecutionStateTransforms:
    """Test task execution state transforms."""

    def test_initial_state_has_execution_fields(self):
        """Initial state includes execution log fields."""
        from agent.governance_ui import get_initial_state

        state = get_initial_state()

        assert 'task_execution_log' in state
        assert 'task_execution_loading' in state
        assert 'show_task_execution' in state

        assert state['task_execution_log'] == []
        assert state['task_execution_loading'] is False
        assert state['show_task_execution'] is False

    def test_with_task_execution_log(self):
        """Set task execution log."""
        from agent.governance_ui import with_task_execution_log, get_initial_state

        state = get_initial_state()
        events = [
            {'event_id': 'E1', 'event_type': 'started', 'timestamp': '2024-12-28T10:00:00'},
            {'event_id': 'E2', 'event_type': 'completed', 'timestamp': '2024-12-28T11:00:00'},
        ]

        new_state = with_task_execution_log(state, events)

        assert new_state['task_execution_log'] == events
        assert new_state['task_execution_loading'] is False
        assert new_state['show_task_execution'] is True
        # Original unchanged
        assert state['task_execution_log'] == []

    def test_with_task_execution_loading(self):
        """Set task execution loading state."""
        from agent.governance_ui import with_task_execution_loading, get_initial_state

        state = get_initial_state()
        new_state = with_task_execution_loading(state)

        assert new_state['task_execution_loading'] is True
        assert new_state['task_execution_log'] == []

    def test_with_task_execution_event(self):
        """Add event to task execution log."""
        from agent.governance_ui import with_task_execution_event

        state = {
            'task_execution_log': [
                {'event_id': 'E1', 'event_type': 'started'}
            ]
        }
        new_event = {'event_id': 'E2', 'event_type': 'completed'}

        new_state = with_task_execution_event(state, new_event)

        assert len(new_state['task_execution_log']) == 2
        assert new_state['task_execution_log'][1] == new_event
        # Original unchanged
        assert len(state['task_execution_log']) == 1

    def test_clear_task_execution(self):
        """Clear task execution log."""
        from agent.governance_ui import clear_task_execution

        state = {
            'task_execution_log': [{'event_id': 'E1'}],
            'task_execution_loading': True,
            'show_task_execution': True,
        }

        new_state = clear_task_execution(state)

        assert new_state['task_execution_log'] == []
        assert new_state['task_execution_loading'] is False
        assert new_state['show_task_execution'] is False


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestExecutionHelpers:
    """Test task execution helper functions."""

    def test_get_execution_event_style_claimed(self):
        """Get style for claimed event."""
        from agent.governance_ui import get_execution_event_style

        style = get_execution_event_style('claimed')

        assert style['icon'] == 'mdi-hand-back-right'
        assert style['color'] == 'info'

    def test_get_execution_event_style_completed(self):
        """Get style for completed event."""
        from agent.governance_ui import get_execution_event_style

        style = get_execution_event_style('completed')

        assert style['icon'] == 'mdi-check-circle'
        assert style['color'] == 'success'

    def test_get_execution_event_style_failed(self):
        """Get style for failed event."""
        from agent.governance_ui import get_execution_event_style

        style = get_execution_event_style('failed')

        assert style['icon'] == 'mdi-alert-circle'
        assert style['color'] == 'error'

    def test_get_execution_event_style_unknown(self):
        """Get default style for unknown event type."""
        from agent.governance_ui import get_execution_event_style

        style = get_execution_event_style('unknown_type')

        assert style['icon'] == 'mdi-circle'
        assert style['color'] == 'grey'

    def test_format_execution_event(self):
        """Format execution event for display."""
        from agent.governance_ui import format_execution_event

        event = {
            'event_id': 'EVT-001',
            'event_type': 'completed',
            'timestamp': '2024-12-28T10:30:45.123456',
            'agent_id': 'AGENT-001',
            'message': 'Task completed successfully',
        }

        formatted = format_execution_event(event)

        assert formatted['icon'] == 'mdi-check-circle'
        assert formatted['color'] == 'success'
        assert formatted['formatted_time'] == '2024-12-28 10:30:45'
        assert formatted['event_id'] == 'EVT-001'
        assert formatted['message'] == 'Task completed successfully'


# =============================================================================
# API Model Tests
# =============================================================================

class TestExecutionAPIModels:
    """Test task execution API models."""

    def test_task_execution_event_model(self):
        """TaskExecutionEvent model has correct fields."""
        from governance.api import TaskExecutionEvent

        event = TaskExecutionEvent(
            event_id="EVT-001",
            task_id="TASK-001",
            event_type="claimed",
            timestamp="2024-12-28T10:00:00",
            agent_id="AGENT-001",
            message="Task claimed",
        )

        assert event.event_id == "EVT-001"
        assert event.task_id == "TASK-001"
        assert event.event_type == "claimed"
        assert event.agent_id == "AGENT-001"

    def test_task_execution_response_model(self):
        """TaskExecutionResponse model has correct fields."""
        from governance.api import TaskExecutionResponse, TaskExecutionEvent

        response = TaskExecutionResponse(
            task_id="TASK-001",
            events=[
                TaskExecutionEvent(
                    event_id="EVT-001",
                    task_id="TASK-001",
                    event_type="started",
                    timestamp="2024-12-28T10:00:00",
                )
            ],
            current_status="in_progress",
            current_agent="AGENT-001",
        )

        assert response.task_id == "TASK-001"
        assert len(response.events) == 1
        assert response.current_status == "in_progress"
        assert response.current_agent == "AGENT-001"


# =============================================================================
# API Endpoint Tests
# =============================================================================

class TestExecutionAPIEndpoints:
    """Test task execution API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from governance.api import app

        return TestClient(app)

    def test_get_task_execution_not_found(self, client):
        """Get execution for non-existent task returns 404."""
        response = client.get("/api/tasks/NONEXISTENT-TASK/execution")

        assert response.status_code == 404

    def test_add_execution_event_not_found(self, client):
        """Add event to non-existent task returns 404."""
        response = client.post(
            "/api/tasks/NONEXISTENT-TASK/execution",
            params={"event_type": "started", "message": "Test"}
        )

        assert response.status_code == 404

    def test_add_and_get_execution_event(self, client):
        """Add event and retrieve execution history."""
        # First create a task
        task_data = {
            "task_id": "TASK-EXEC-TEST-001",
            "description": "Test task for execution",
            "phase": "P10",
            "status": "TODO",
        }
        create_response = client.post("/api/tasks", json=task_data)
        assert create_response.status_code == 201

        try:
            # Add execution event
            add_response = client.post(
                "/api/tasks/TASK-EXEC-TEST-001/execution",
                params={
                    "event_type": "claimed",
                    "message": "Claimed by test agent",
                    "agent_id": "TEST-AGENT"
                }
            )
            assert add_response.status_code == 201
            event = add_response.json()
            assert event["event_type"] == "claimed"
            assert event["agent_id"] == "TEST-AGENT"
            assert "event_id" in event

            # Get execution history
            get_response = client.get("/api/tasks/TASK-EXEC-TEST-001/execution")
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["task_id"] == "TASK-EXEC-TEST-001"
            assert len(data["events"]) >= 1

        finally:
            # Cleanup
            client.delete("/api/tasks/TASK-EXEC-TEST-001")

    def test_execution_event_types_valid(self, client):
        """Verify all execution event types are accepted."""
        task_data = {
            "task_id": "TASK-EXEC-TYPES-001",
            "description": "Test event types",
            "phase": "P10",
            "status": "TODO",
        }
        client.post("/api/tasks", json=task_data)

        event_types = ["claimed", "started", "progress", "delegated", "completed", "failed", "evidence"]

        try:
            for event_type in event_types:
                response = client.post(
                    "/api/tasks/TASK-EXEC-TYPES-001/execution",
                    params={
                        "event_type": event_type,
                        "message": f"Testing {event_type}"
                    }
                )
                assert response.status_code == 201, f"Failed for event_type: {event_type}"
                assert response.json()["event_type"] == event_type

        finally:
            client.delete("/api/tasks/TASK-EXEC-TYPES-001")


# =============================================================================
# Integration Tests
# =============================================================================

class TestExecutionIntegration:
    """Integration tests for task execution viewer."""

    def test_synthesize_events_from_task_timestamps(self):
        """Synthesize events from task with timestamps."""
        from governance.api import _synthesize_execution_events

        task_data = {
            "created_at": "2024-12-28T10:00:00",
            "claimed_at": "2024-12-28T10:05:00",
            "completed_at": "2024-12-28T11:00:00",
            "agent_id": "AGENT-001",
            "status": "DONE",
            "evidence": "Task completed with all tests passing",
        }

        events = _synthesize_execution_events("TASK-001", task_data)

        # Should have: started, claimed, completed, evidence
        assert len(events) >= 3
        event_types = [e["event_type"] for e in events]
        assert "started" in event_types
        assert "claimed" in event_types
        assert "completed" in event_types

    def test_synthesize_events_empty_task(self):
        """Synthesize events from task with no timestamps."""
        from governance.api import _synthesize_execution_events

        task_data = {
            "status": "TODO",
        }

        events = _synthesize_execution_events("TASK-002", task_data)

        # Should be empty for pending task with no timestamps
        assert len(events) == 0

    def test_execution_response_includes_status(self):
        """Execution response includes current task status."""
        from fastapi.testclient import TestClient
        from governance.api import app

        client = TestClient(app)

        # Create task with specific status
        task_data = {
            "task_id": "TASK-STATUS-TEST",
            "description": "Test status",
            "phase": "P10",
            "status": "IN_PROGRESS",
        }
        client.post("/api/tasks", json=task_data)

        try:
            response = client.get("/api/tasks/TASK-STATUS-TEST/execution")
            assert response.status_code == 200
            data = response.json()
            assert data["current_status"] == "IN_PROGRESS"

        finally:
            client.delete("/api/tasks/TASK-STATUS-TEST")
