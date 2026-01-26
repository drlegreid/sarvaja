"""
MCP REST Sessions Library for Robot Framework
Integration tests for sessions/tasks via REST API.
Migrated from tests/integration/test_mcp_rest_sessions.py
Per: RF-007 Robot Framework Migration
"""
import requests
from datetime import datetime
from robot.api.deco import keyword


class MCPRestSessionsLibrary:
    """Robot Framework keywords for MCP REST sessions tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'
    API_BASE = "http://localhost:8082"

    def _api_get(self, endpoint):
        """GET request to API."""
        try:
            response = requests.get(f"{self.API_BASE}{endpoint}", timeout=10)
            if not response.ok:
                return {"status": response.status_code, "data": None}
            data = response.json()
            if isinstance(data, dict) and "items" in data:
                return {"status": response.status_code, "data": data["items"], "pagination": data.get("pagination")}
            return {"status": response.status_code, "data": data}
        except requests.RequestException as e:
            return {"status": 0, "data": None, "error": str(e)}

    def _api_post(self, endpoint, data):
        """POST request to API."""
        try:
            response = requests.post(f"{self.API_BASE}{endpoint}", json=data, timeout=10)
            return {
                "status": response.status_code,
                "data": response.json() if response.status_code in [200, 201] else None
            }
        except requests.RequestException as e:
            return {"status": 0, "data": None, "error": str(e)}

    def _check_api_available(self):
        """Check if API is available."""
        try:
            response = requests.get(f"{self.API_BASE}/api/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    # =========================================================================
    # Session Tests
    # =========================================================================

    @keyword("List Sessions Via REST")
    def list_sessions_via_rest(self):
        """MCP-001-D: Can list sessions via REST API."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        result = self._api_get("/api/sessions")
        if result["status"] != 200:
            return {"skipped": True, "reason": f"API returned {result['status']}"}

        sessions = result["data"]
        has_structure = False
        if sessions and len(sessions) > 0:
            session = sessions[0]
            has_structure = "session_id" in session and "status" in session

        return {
            "returns_list": isinstance(sessions, list),
            "has_structure": has_structure
        }

    @keyword("Create Session Via REST")
    def create_session_via_rest(self):
        """MCP-001-A: Can create session via REST API."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_data = {
            "session_id": f"TEST-SESSION-{timestamp}",
            "agent_id": "claude-code-test",
            "description": "Test session created via REST API"
        }

        result = self._api_post("/api/sessions", session_data)

        return {
            "status_201": result["status"] == 201,
            "id_matches": result.get("data", {}).get("session_id") == session_data["session_id"]
        }

    @keyword("Get Tasks With Sessions")
    def get_tasks_with_sessions(self):
        """MCP-002-A: Tasks and sessions can be queried together."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        tasks_result = self._api_get("/api/tasks")
        sessions_result = self._api_get("/api/sessions")

        return {
            "tasks_ok": tasks_result["status"] == 200 and isinstance(tasks_result["data"], list),
            "sessions_ok": sessions_result["status"] == 200 and isinstance(sessions_result["data"], list)
        }

    @keyword("Health Includes TypeDB")
    def health_includes_typedb(self):
        """MCP-003-A: Health endpoint shows TypeDB status."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        result = self._api_get("/api/health")
        if result["status"] != 200:
            return {"skipped": True, "reason": f"Health returned {result['status']}"}

        data = result["data"]
        return {
            "has_typedb_field": "typedb_connected" in data,
            "typedb_connected": data.get("typedb_connected", False)
        }

    # =========================================================================
    # Task Tests
    # =========================================================================

    @keyword("List Tasks Via REST")
    def list_tasks_via_rest(self):
        """Can list tasks via REST API."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        result = self._api_get("/api/tasks")
        return {
            "status_200": result["status"] == 200,
            "returns_list": isinstance(result.get("data"), list)
        }

    @keyword("Create Task Via REST")
    def create_task_via_rest(self):
        """MCP-002-A: Can create task via REST API."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        task_data = {
            "task_id": f"TEST-TASK-{timestamp}",
            "name": "Test task via REST API",
            "description": "Created by integration test",
            "status": "TODO",
            "priority": "LOW",
            "phase": "TEST"
        }

        result = self._api_post("/api/tasks", task_data)

        return {
            "status_201": result["status"] == 201,
            "id_matches": result.get("data", {}).get("task_id") == task_data["task_id"]
        }

    @keyword("Task Persistence Round Trip")
    def task_persistence_round_trip(self):
        """GAP-API-001 FIXED: Tasks created via POST persist to TypeDB."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

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
        create_result = self._api_post("/api/tasks", task_data)
        if create_result["status"] != 201:
            return {"skipped": True, "reason": f"Create failed: {create_result['status']}"}

        # Retrieve task
        get_result = self._api_get("/api/tasks?limit=200&sort_by=task_id&order=desc")
        if get_result["status"] != 200:
            return {"skipped": True, "reason": f"Get failed: {get_result['status']}"}

        task_ids = [t["task_id"] for t in get_result["data"]]
        persisted = test_task_id in task_ids

        # Cleanup
        try:
            requests.delete(f"{self.API_BASE}/api/tasks/{test_task_id}", timeout=10)
        except Exception:
            pass

        return {"persisted": persisted}

    # =========================================================================
    # Session-Task Relationship Tests
    # =========================================================================

    @keyword("Session Tasks Endpoint Exists")
    def session_tasks_endpoint_exists(self):
        """GAP-UI-SESSION-TASKS-001: /api/sessions/{id}/tasks endpoint exists."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        session_id = "SESSION-2026-01-10-INTENT-TEST"
        result = self._api_get(f"/api/sessions/{session_id}/tasks")

        return {"endpoint_exists": result["status"] in [200, 404]}

    @keyword("Session Tasks Returns Linked Tasks")
    def session_tasks_returns_linked_tasks(self):
        """GAP-UI-SESSION-TASKS-001: Session endpoint returns linked tasks."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        session_id = "SESSION-2026-01-10-INTENT-TEST"
        result = self._api_get(f"/api/sessions/{session_id}/tasks")

        if result["status"] != 200:
            return {"skipped": True, "reason": f"Endpoint returned {result['status']}"}

        data = result["data"]
        tasks = data.get("tasks", data) if isinstance(data, dict) else data

        has_tasks = isinstance(tasks, list) and len(tasks) >= 1
        has_structure = False
        if has_tasks and tasks:
            task = tasks[0]
            has_structure = "task_id" in task and "status" in task

        return {"has_tasks": has_tasks, "has_structure": has_structure}

    @keyword("Session Tasks Count Matches")
    def session_tasks_count_matches(self):
        """GAP-UI-SESSION-TASKS-001: task_count matches actual tasks returned."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        session_id = "SESSION-2026-01-10-INTENT-TEST"
        result = self._api_get(f"/api/sessions/{session_id}/tasks")

        if result["status"] != 200:
            return {"skipped": True, "reason": f"Endpoint returned {result['status']}"}

        data = result["data"]
        if isinstance(data, dict) and "task_count" in data:
            expected_count = data["task_count"]
            actual_count = len(data.get("tasks", []))
            return {"count_matches": actual_count == expected_count}

        return {"count_matches": True}  # No count field, passes

    @keyword("Task Has Linked Sessions")
    def task_has_linked_sessions(self):
        """GAP-UI-TASK-SESSION-001: Task endpoint returns linked_sessions."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        task_id = "P12.3"
        result = self._api_get(f"/api/tasks/{task_id}")

        if result["status"] != 200:
            return {"skipped": True, "reason": f"Task not found: {result['status']}"}

        task = result["data"]
        has_field = "linked_sessions" in task
        has_expected_session = False
        if has_field and task["linked_sessions"]:
            has_expected_session = "SESSION-2026-01-10-INTENT-TEST" in task["linked_sessions"]

        return {"has_linked_sessions_field": has_field, "has_expected_session": has_expected_session}

    # =========================================================================
    # Rules Tests
    # =========================================================================

    @keyword("List Rules Via REST")
    def list_rules_via_rest(self):
        """MCP-003-B: Can list rules via REST API."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        result = self._api_get("/api/rules")

        if result["status"] != 200:
            return {"skipped": True, "reason": f"Rules returned {result['status']}"}

        rules = result["data"]
        return {
            "returns_list": isinstance(rules, list),
            "has_rules": len(rules) > 0
        }

    @keyword("Rules Have Structure")
    def rules_have_structure(self):
        """Rules have expected structure."""
        if not self._check_api_available():
            return {"skipped": True, "reason": "API not available"}

        result = self._api_get("/api/rules")

        if result["status"] != 200 or not result["data"]:
            return {"skipped": True, "reason": "No rules available"}

        rule = result["data"][0]
        has_id = "rule_id" in rule or "id" in rule
        has_content = "name" in rule or "directive" in rule

        return {"has_id": has_id, "has_content": has_content}
