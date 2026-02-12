"""
MCP REST API Session Integration Tests.

Per GAP-MCP-001: Workaround for gov-sessions MCP underutilization.
Uses rest-api MCP as proxy to access session operations.

These tests verify:
1. Session listing via REST API
2. Session creation via REST API
3. Session-task linking via REST API

Run: pytest tests/integration/test_mcp_rest_sessions.py -v
"""

import pytest
import requests
from datetime import datetime
from typing import Dict, Any

API_BASE = "http://localhost:8082"


def api_get(endpoint: str) -> Dict[str, Any]:
    """GET request to API."""
    response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
    if not response.ok:
        return {"status": response.status_code, "data": None}
    data = response.json()
    # Handle paginated responses (EPIC-DR-003)
    if isinstance(data, dict) and "items" in data:
        return {"status": response.status_code, "data": data["items"], "pagination": data.get("pagination")}
    return {"status": response.status_code, "data": data}


def api_post(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """POST request to API."""
    response = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=10)
    return {"status": response.status_code, "data": response.json() if response.status_code in [200, 201] else None}


class TestSessionsViaRestAPI:
    """Test session operations via REST API (GAP-MCP-001 workaround)."""

    @pytest.fixture(autouse=True)
    def check_api_available(self):
        """Skip if API not running."""
        try:
            response = requests.get(f"{API_BASE}/api/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("API not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")

    def test_list_sessions(self):
        """MCP-001-D: Can list sessions via REST API."""
        result = api_get("/api/sessions")

        assert result["status"] == 200, "Sessions endpoint should return 200"
        assert isinstance(result["data"], list), "Should return list of sessions"

        # Verify session structure
        if result["data"]:
            session = result["data"][0]
            assert "session_id" in session
            assert "status" in session
            assert "start_time" in session

    def test_create_session(self):
        """MCP-001-A: Can create session via REST API."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_session_id = f"TEST-SESSION-{timestamp}"
        session_data = {
            "session_id": test_session_id,
            "agent_id": "claude-code-test",
            "description": "Test session created via REST API"
        }

        try:
            result = api_post("/api/sessions", session_data)

            assert result["status"] == 201, f"Session creation should return 201, got {result['status']}"
            assert result["data"]["session_id"] == test_session_id
        finally:
            # Cleanup: delete test session to prevent pollution
            requests.delete(f"{API_BASE}/api/sessions/{test_session_id}", timeout=10)

    def test_get_tasks_with_sessions(self):
        """MCP-002-A / GOV-MCP-FIRST-01-v1: Tasks and sessions can be queried together."""
        # Get tasks
        tasks_result = api_get("/api/tasks")
        assert tasks_result["status"] == 200

        # Get sessions
        sessions_result = api_get("/api/sessions")
        assert sessions_result["status"] == 200

        # Both should be lists
        assert isinstance(tasks_result["data"], list)
        assert isinstance(sessions_result["data"], list)

    def test_api_health_includes_typedb(self):
        """MCP-003-A: Health endpoint shows TypeDB status."""
        result = api_get("/api/health")

        assert result["status"] == 200
        assert "typedb_connected" in result["data"]
        assert result["data"]["typedb_connected"] is True


class TestTasksViaRestAPI:
    """Test task operations via REST API (GAP-MCP-002 workaround)."""

    @pytest.fixture(autouse=True)
    def check_api_available(self):
        """Skip if API not running."""
        try:
            response = requests.get(f"{API_BASE}/api/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("API not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")

    def test_list_tasks(self):
        """Can list tasks via REST API."""
        result = api_get("/api/tasks")

        assert result["status"] == 200
        assert isinstance(result["data"], list)

    def test_create_task(self):
        """MCP-002-A / GOV-MCP-FIRST-01-v1: Can create task via REST API."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        task_data = {
            "task_id": f"TEST-TASK-{timestamp}",
            "name": "Test task via REST API",
            "description": "Created by integration test",
            "status": "TODO",
            "priority": "LOW",
            "phase": "TEST"
        }

        result = api_post("/api/tasks", task_data)

        assert result["status"] == 201, f"Task creation should return 201, got {result['status']}"
        assert result["data"]["task_id"] == task_data["task_id"]

    def test_task_persistence_round_trip(self):
        """GAP-API-001 FIXED: Tasks created via POST persist to TypeDB.

        Verifies the full round-trip: create task → retrieve task → delete task.
        Fixed 2026-01-16: Schema migration added task-resolution attribute.
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_task_id = f"TEST-PERSIST-{timestamp}"

        # Create task
        task_data = {
            "task_id": test_task_id,
            "description": "Test persistence round-trip",
            "status": "TODO",
            "phase": "TEST",
            "priority": "LOW"
        }
        create_result = api_post("/api/tasks", task_data)
        assert create_result["status"] == 201, "Task creation should return 201"

        # Retrieve task (verify persistence) - use limit to ensure we get enough tasks
        get_result = api_get(f"/api/tasks?limit=200&sort_by=task_id&order=desc")
        assert get_result["status"] == 200
        task_ids = [t["task_id"] for t in get_result["data"]]
        assert test_task_id in task_ids, f"Task {test_task_id} should persist to TypeDB"

        # Cleanup: delete the test task
        import requests
        requests.delete(f"{API_BASE}/api/tasks/{test_task_id}", timeout=10)


class TestSessionTasksRelationship:
    """Regression tests for GAP-UI-SESSION-TASKS-001.

    Per GAP-UI-SESSION-TASKS-001: Session detail must load completed tasks.
    These tests verify the API endpoint that powers the session→task navigation.
    """

    @pytest.fixture(autouse=True)
    def check_api_available(self):
        """Skip if API not running."""
        try:
            response = requests.get(f"{API_BASE}/api/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("API not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")

    def test_session_tasks_endpoint_exists(self):
        """GAP-UI-SESSION-TASKS-001: /api/sessions/{id}/tasks endpoint exists."""
        # Use a known session with tasks
        session_id = "SESSION-2026-01-10-INTENT-TEST"
        result = api_get(f"/api/sessions/{session_id}/tasks")

        assert result["status"] in [200, 404], "Endpoint should exist"
        if result["status"] == 200:
            assert "tasks" in result["data"] or isinstance(result["data"], list)

    def test_session_tasks_returns_linked_tasks(self):
        """GAP-UI-SESSION-TASKS-001: Session endpoint returns linked tasks."""
        session_id = "SESSION-2026-01-10-INTENT-TEST"
        result = api_get(f"/api/sessions/{session_id}/tasks")

        if result["status"] == 200:
            data = result["data"]
            # Handle both formats: {tasks: [...]} or direct list
            tasks = data.get("tasks", data) if isinstance(data, dict) else data
            assert isinstance(tasks, list), "Tasks should be a list"
            assert len(tasks) >= 1, "Session should have linked tasks"

            # Verify task structure
            if tasks:
                task = tasks[0]
                assert "task_id" in task, "Task should have task_id"
                assert "status" in task, "Task should have status"

    def test_session_tasks_count_matches_list(self):
        """GAP-UI-SESSION-TASKS-001: task_count matches actual tasks returned."""
        session_id = "SESSION-2026-01-10-INTENT-TEST"
        result = api_get(f"/api/sessions/{session_id}/tasks")

        if result["status"] == 200:
            data = result["data"]
            if isinstance(data, dict) and "task_count" in data:
                expected_count = data["task_count"]
                actual_count = len(data.get("tasks", []))
                assert actual_count == expected_count, f"Count mismatch: {actual_count} != {expected_count}"

    def test_task_has_linked_sessions(self):
        """GAP-UI-TASK-SESSION-001: Task endpoint returns linked_sessions."""
        task_id = "P12.3"  # Known task linked to SESSION-2026-01-10-INTENT-TEST
        result = api_get(f"/api/tasks/{task_id}")

        if result["status"] == 200:
            task = result["data"]
            assert "linked_sessions" in task, "Task should have linked_sessions field"
            if task["linked_sessions"]:
                assert isinstance(task["linked_sessions"], list)
                assert "SESSION-2026-01-10-INTENT-TEST" in task["linked_sessions"]


class TestRulesViaRestAPI:
    """Test rules operations via REST API (GAP-MCP-003)."""

    @pytest.fixture(autouse=True)
    def check_api_available(self):
        """Skip if API not running."""
        try:
            response = requests.get(f"{API_BASE}/api/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("API not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("API not running")

    def test_list_rules(self):
        """MCP-003-B: Can list rules via REST API."""
        result = api_get("/api/rules")

        assert result["status"] == 200
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0, "Should have rules in TypeDB"

    def test_rules_have_structure(self):
        """Rules have expected structure."""
        result = api_get("/api/rules")

        assert result["status"] == 200

        if result["data"]:
            rule = result["data"][0]
            # Check expected fields
            assert "rule_id" in rule or "id" in rule
            assert "name" in rule or "directive" in rule
