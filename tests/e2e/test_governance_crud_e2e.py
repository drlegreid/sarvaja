"""
E2E Tests for Governance CRUD Operations
Per GAP-UI-028: Tests must verify actual functionality, not just imports
Per RULE-004: Page Object Model testing

These tests verify:
1. Rules CRUD (Create, Read, Update, Delete)
2. Tasks CRUD (Create, Read, Update, Delete)
3. Sessions API
4. Agents API
5. Evidence API

Prerequisites:
- API server running on port 8082
- TypeDB connected (for Rules/Decisions)

Run:
    pytest tests/e2e/test_governance_crud_e2e.py -v
    OR with API server:
    python agent/run_governance_server.py --api-only &
    pytest tests/e2e/test_governance_crud_e2e.py -v

Created: 2024-12-25
"""

import pytest
import httpx
import uuid
from datetime import datetime

# API base URL
API_BASE_URL = "http://localhost:8082"


def check_typedb_connected() -> bool:
    """Check if TypeDB is connected via health endpoint."""
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=5.0) as client:
            response = client.get("/api/health")
            if response.status_code == 200:
                data = response.json()
                return data.get("typedb_connected", False)
    except Exception:
        pass
    return False


# Check TypeDB once at module load
TYPEDB_AVAILABLE = check_typedb_connected()


@pytest.fixture
def api_client():
    """Create HTTP client for API tests."""
    # Increased timeout to handle large task lists (168+ tasks)
    return httpx.Client(base_url=API_BASE_URL, timeout=30.0)


@pytest.fixture
def unique_id():
    """Generate unique ID for test entities."""
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """
    Session-scoped cleanup fixture that removes TEST-* entities.

    Per RULE-004: Clean test environment
    - Runs BEFORE tests (yield) to clean existing pollution
    - Runs AFTER all tests to clean up created data
    """
    client = httpx.Client(base_url=API_BASE_URL, timeout=30.0)

    def do_cleanup():
        """Remove all TEST-* entities from the database."""
        cleaned = {"tasks": 0, "sessions": 0, "rules": 0}

        # Cleanup tasks
        try:
            tasks_resp = client.get("/api/tasks")
            if tasks_resp.status_code == 200:
                for task in tasks_resp.json():
                    task_id = task.get("task_id", "")
                    if task_id.startswith("TEST-"):
                        del_resp = client.delete(f"/api/tasks/{task_id}")
                        if del_resp.status_code == 204:
                            cleaned["tasks"] += 1
        except Exception as e:
            print(f"Task cleanup error: {e}")

        # Cleanup sessions
        try:
            sessions_resp = client.get("/api/sessions")
            if sessions_resp.status_code == 200:
                for session in sessions_resp.json():
                    session_id = session.get("session_id", "")
                    if session_id.startswith("TEST-"):
                        # Sessions can't be deleted, but we can end them
                        try:
                            client.put(f"/api/sessions/{session_id}/end")
                            cleaned["sessions"] += 1
                        except Exception:
                            pass
        except Exception as e:
            print(f"Session cleanup error: {e}")

        # Cleanup rules (TypeDB)
        if TYPEDB_AVAILABLE:
            try:
                rules_resp = client.get("/api/rules")
                if rules_resp.status_code == 200:
                    for rule in rules_resp.json():
                        rule_id = rule.get("id", "")
                        if rule_id.startswith("TEST-"):
                            del_resp = client.delete(f"/api/rules/{rule_id}")
                            if del_resp.status_code == 204:
                                cleaned["rules"] += 1
            except Exception as e:
                print(f"Rule cleanup error: {e}")

        return cleaned

    # Pre-test cleanup (clean existing pollution)
    pre_cleaned = do_cleanup()
    if sum(pre_cleaned.values()) > 0:
        print(f"\n[Pre-test cleanup] Removed: {pre_cleaned}")

    yield  # Run all tests

    # Post-test cleanup
    post_cleaned = do_cleanup()
    if sum(post_cleaned.values()) > 0:
        print(f"\n[Post-test cleanup] Removed: {post_cleaned}")

    client.close()


class TestHealthCheck:
    """Test API health endpoint."""

    def test_api_health_returns_status(self, api_client):
        """Test health endpoint returns expected fields."""
        response = api_client.get("/api/health")
        # May return 200 or 503 depending on TypeDB
        assert response.status_code in (200, 503)

        data = response.json()
        assert "status" in data
        assert "typedb_connected" in data
        assert "version" in data


class TestRulesCRUD:
    """E2E tests for Rules CRUD operations."""

    @pytest.mark.skipif(not TYPEDB_AVAILABLE, reason="TypeDB not connected")
    def test_create_rule_via_api(self, api_client, unique_id):
        """Test creating a new rule through API."""
        rule_data = {
            "rule_id": unique_id,
            "name": f"Test Rule {unique_id}",
            "category": "technical",
            "priority": "HIGH",
            "directive": "This is a test rule created via E2E test",
            "status": "DRAFT"
        }

        response = api_client.post("/api/rules", json=rule_data)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        created = response.json()
        assert created["id"] == unique_id
        assert created["name"] == rule_data["name"]
        assert created["status"] == "DRAFT"

    @pytest.mark.skipif(not TYPEDB_AVAILABLE, reason="TypeDB not connected")
    def test_list_rules_via_api(self, api_client):
        """Test listing rules through API."""
        response = api_client.get("/api/rules")
        assert response.status_code == 200

        rules = response.json()
        assert isinstance(rules, list)
        # If TypeDB has data, verify structure
        if rules:
            assert "id" in rules[0]
            assert "name" in rules[0]

    @pytest.mark.skipif(not TYPEDB_AVAILABLE, reason="TypeDB not connected")
    def test_update_rule_via_api(self, api_client, unique_id):
        """Test updating a rule through API."""
        # First create
        rule_data = {
            "rule_id": unique_id,
            "name": f"Original Name {unique_id}",
            "category": "governance",
            "priority": "MEDIUM",
            "directive": "Original directive",
            "status": "DRAFT"
        }
        api_client.post("/api/rules", json=rule_data)

        # Then update
        update_data = {
            "name": f"Updated Name {unique_id}",
            "status": "ACTIVE"
        }
        response = api_client.put(f"/api/rules/{unique_id}", json=update_data)
        assert response.status_code == 200

        updated = response.json()
        assert updated["name"] == update_data["name"]
        assert updated["status"] == "ACTIVE"

    @pytest.mark.skipif(not TYPEDB_AVAILABLE, reason="TypeDB not connected")
    def test_delete_rule_via_api(self, api_client, unique_id):
        """Test deleting a rule through API."""
        # First create
        rule_data = {
            "rule_id": unique_id,
            "name": f"To Delete {unique_id}",
            "category": "operational",
            "priority": "LOW",
            "directive": "This rule will be deleted",
            "status": "DRAFT"
        }
        api_client.post("/api/rules", json=rule_data)

        # Then delete
        response = api_client.delete(f"/api/rules/{unique_id}")
        assert response.status_code == 204

        # Verify deleted
        get_response = api_client.get(f"/api/rules/{unique_id}")
        assert get_response.status_code == 404


class TestTasksCRUD:
    """E2E tests for Tasks CRUD operations (in-memory store)."""

    def test_create_task_via_api(self, api_client, unique_id):
        """Test creating a new task through API."""
        task_data = {
            "task_id": unique_id,
            "description": f"E2E Test Task {unique_id}",
            "phase": "P10",
            "status": "TODO",
            "agent_id": "test-agent"
        }

        response = api_client.post("/api/tasks", json=task_data)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        created = response.json()
        assert created["task_id"] == unique_id
        assert created["description"] == task_data["description"]
        assert created["status"] == "TODO"
        assert "created_at" in created

    def test_list_tasks_via_api(self, api_client):
        """Test listing tasks through API."""
        response = api_client.get("/api/tasks")
        assert response.status_code == 200

        tasks = response.json()
        assert isinstance(tasks, list)

    def test_update_task_status_via_api(self, api_client, unique_id):
        """Test updating task status through API."""
        # First create
        task_data = {
            "task_id": unique_id,
            "description": "Task to update",
            "phase": "P10",
            "status": "TODO"
        }
        api_client.post("/api/tasks", json=task_data)

        # Then update (API expects JSON body, not params)
        response = api_client.put(f"/api/tasks/{unique_id}", json={"status": "DONE", "agent_id": "code-agent"})
        assert response.status_code == 200

        updated = response.json()
        assert updated["status"] == "DONE"
        assert updated["agent_id"] == "code-agent"
        assert "completed_at" in updated

    def test_delete_task_via_api(self, api_client, unique_id):
        """Test deleting a task through API."""
        # First create
        task_data = {
            "task_id": unique_id,
            "description": "Task to delete",
            "phase": "P10",
            "status": "TODO"
        }
        api_client.post("/api/tasks", json=task_data)

        # Then delete
        response = api_client.delete(f"/api/tasks/{unique_id}")
        assert response.status_code == 204

    def test_filter_tasks_by_status(self, api_client, unique_id):
        """Test filtering tasks by status."""
        # Create tasks with different statuses
        api_client.post("/api/tasks", json={
            "task_id": f"{unique_id}-TODO",
            "description": "TODO task",
            "phase": "P10",
            "status": "TODO"
        })
        api_client.post("/api/tasks", json={
            "task_id": f"{unique_id}-DONE",
            "description": "DONE task",
            "phase": "P10",
            "status": "DONE"
        })

        # Filter by status
        response = api_client.get("/api/tasks", params={"status": "TODO"})
        assert response.status_code == 200
        tasks = response.json()
        assert all(t["status"] == "TODO" for t in tasks)


class TestAgentTaskBacklog:
    """E2E tests for Agent Task Backlog (TODO-6)."""

    def test_list_available_tasks(self, api_client, unique_id):
        """Test listing tasks available for agents to claim."""
        # Create a task with TODO status and no agent
        task_data = {
            "task_id": unique_id,
            "description": "Available task for agent pickup",
            "phase": "P10",
            "status": "TODO"
            # No agent_id means available
        }
        api_client.post("/api/tasks", json=task_data)

        # Get available tasks
        response = api_client.get("/api/tasks/available")
        assert response.status_code == 200

        available = response.json()
        assert isinstance(available, list)
        # All available tasks should have TODO status and no agent_id
        task_ids = [t["task_id"] for t in available]
        assert unique_id in task_ids  # Our created task should be available

    def test_claim_task_by_agent(self, api_client, unique_id):
        """Test agent claiming a task."""
        # Create an available task
        task_data = {
            "task_id": unique_id,
            "description": "Task to be claimed",
            "phase": "P10",
            "status": "TODO"
        }
        api_client.post("/api/tasks", json=task_data)

        # Claim the task as code-agent
        response = api_client.put(
            f"/api/tasks/{unique_id}/claim",
            params={"agent_id": "code-agent"}
        )
        assert response.status_code == 200

        claimed = response.json()
        assert claimed["agent_id"] == "code-agent"
        assert claimed["status"] == "IN_PROGRESS"
        assert "claimed_at" in claimed

    def test_claim_already_claimed_task_fails(self, api_client, unique_id):
        """Test that claiming an already-claimed task fails."""
        # Create and claim a task
        task_data = {
            "task_id": unique_id,
            "description": "Already claimed task",
            "phase": "P10",
            "status": "TODO"
        }
        api_client.post("/api/tasks", json=task_data)
        api_client.put(f"/api/tasks/{unique_id}/claim", params={"agent_id": "code-agent"})

        # Try to claim again
        response = api_client.put(
            f"/api/tasks/{unique_id}/claim",
            params={"agent_id": "review-agent"}
        )
        assert response.status_code == 409  # Conflict

    def test_complete_task(self, api_client, unique_id):
        """Test completing a claimed task."""
        # Create and claim a task
        task_data = {
            "task_id": unique_id,
            "description": "Task to complete",
            "phase": "P10",
            "status": "TODO"
        }
        api_client.post("/api/tasks", json=task_data)
        api_client.put(f"/api/tasks/{unique_id}/claim", params={"agent_id": "code-agent"})

        # Complete the task
        response = api_client.put(
            f"/api/tasks/{unique_id}/complete",
            params={"evidence": "Tests passed, code reviewed"}
        )
        assert response.status_code == 200

        completed = response.json()
        assert completed["status"] == "DONE"
        assert "completed_at" in completed
        assert completed["evidence"] == "Tests passed, code reviewed"

    def test_claimed_task_not_in_available(self, api_client, unique_id):
        """Test that claimed tasks don't appear in available list."""
        # Create and claim a task
        task_data = {
            "task_id": unique_id,
            "description": "Claimed task should not be available",
            "phase": "P10",
            "status": "TODO"
        }
        api_client.post("/api/tasks", json=task_data)
        api_client.put(f"/api/tasks/{unique_id}/claim", params={"agent_id": "code-agent"})

        # Get available tasks
        response = api_client.get("/api/tasks/available")
        assert response.status_code == 200

        available = response.json()
        task_ids = [t["task_id"] for t in available]
        assert unique_id not in task_ids  # Claimed task should not be available


class TestAgentsAPI:
    """E2E tests for Agents API."""

    def test_list_agents_via_api(self, api_client):
        """Test listing registered agents."""
        response = api_client.get("/api/agents")
        assert response.status_code == 200

        agents = response.json()
        assert isinstance(agents, list)
        assert len(agents) > 0  # Should have pre-configured agents

        # Verify agent structure
        agent = agents[0]
        assert "agent_id" in agent
        assert "name" in agent
        assert "agent_type" in agent
        assert "status" in agent
        assert "trust_score" in agent

    def test_get_specific_agent(self, api_client):
        """Test getting a specific agent by ID."""
        response = api_client.get("/api/agents/task-orchestrator")
        assert response.status_code == 200

        agent = response.json()
        assert agent["agent_id"] == "task-orchestrator"
        assert agent["name"] == "Task Orchestrator"

    def test_record_agent_task_execution(self, api_client):
        """Test recording an agent task execution."""
        # Get current state
        agent_before = api_client.get("/api/agents/code-agent").json()
        tasks_before = agent_before["tasks_executed"]

        # Record task
        response = api_client.put("/api/agents/code-agent/task")
        assert response.status_code == 200

        agent_after = response.json()
        assert agent_after["tasks_executed"] == tasks_before + 1
        assert agent_after["last_active"] is not None


class TestSessionsAPI:
    """E2E tests for Sessions API."""

    def test_create_session_via_api(self, api_client):
        """Test creating a new session."""
        # API expects JSON body, not params
        response = api_client.post("/api/sessions", json={
            "agent_id": "test-agent",
            "description": "Test session created by E2E test"
        })
        assert response.status_code == 201

        session = response.json()
        assert "session_id" in session
        assert session["status"] == "ACTIVE"
        assert session["agent_id"] == "test-agent"

    def test_list_sessions_via_api(self, api_client):
        """Test listing sessions."""
        response = api_client.get("/api/sessions")
        assert response.status_code == 200

        sessions = response.json()
        assert isinstance(sessions, list)

    def test_end_session_via_api(self, api_client):
        """Test ending a session."""
        # Create session (API expects JSON body)
        create_response = api_client.post("/api/sessions", json={
            "agent_id": "end-test-agent",
            "description": "Session to end in E2E test"
        })
        session_id = create_response.json()["session_id"]

        # End session
        response = api_client.put(f"/api/sessions/{session_id}/end")
        assert response.status_code == 200

        ended = response.json()
        assert ended["status"] == "COMPLETED"  # TypeDB uses COMPLETED
        assert ended["end_time"] is not None


class TestEvidenceAPI:
    """E2E tests for Evidence API."""

    def test_list_evidence_via_api(self, api_client):
        """Test listing evidence files."""
        response = api_client.get("/api/evidence")
        assert response.status_code == 200

        evidence = response.json()
        assert isinstance(evidence, list)
        # Evidence comes from evidence/ directory


class TestDecisionsAPI:
    """E2E tests for Decisions API."""

    @pytest.mark.skipif(not TYPEDB_AVAILABLE, reason="TypeDB not connected")
    def test_list_decisions_via_api(self, api_client):
        """Test listing strategic decisions."""
        response = api_client.get("/api/decisions")
        assert response.status_code == 200

        decisions = response.json()
        assert isinstance(decisions, list)


class TestCRUDWorkflows:
    """Integration tests for complete CRUD workflows."""

    def test_full_task_lifecycle(self, api_client, unique_id):
        """Test complete task lifecycle: Create -> Update -> Complete -> Delete."""
        # 1. Create
        create_response = api_client.post("/api/tasks", json={
            "task_id": unique_id,
            "description": "Full lifecycle test",
            "phase": "P10",
            "status": "TODO"
        })
        assert create_response.status_code == 201

        # 2. Assign to agent (API expects JSON body)
        update_response = api_client.put(f"/api/tasks/{unique_id}", json={
            "status": "IN_PROGRESS",
            "agent_id": "code-agent"
        })
        assert update_response.status_code == 200
        assert update_response.json()["agent_id"] == "code-agent"

        # 3. Complete (API expects JSON body)
        complete_response = api_client.put(f"/api/tasks/{unique_id}", json={"status": "DONE"})
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "DONE"
        assert complete_response.json()["completed_at"] is not None

        # 4. Delete
        delete_response = api_client.delete(f"/api/tasks/{unique_id}")
        assert delete_response.status_code == 204

    def test_agent_task_attribution(self, api_client, unique_id):
        """Test that task execution updates agent metrics."""
        # Get initial agent state
        agent_before = api_client.get("/api/agents/research-agent").json()
        tasks_before = agent_before["tasks_executed"]

        # Create and assign task to agent
        api_client.post("/api/tasks", json={
            "task_id": unique_id,
            "description": "Agent attribution test",
            "phase": "P10",
            "status": "TODO",
            "agent_id": "research-agent"
        })

        # Record task execution
        api_client.put("/api/agents/research-agent/task")

        # Verify agent metrics updated
        agent_after = api_client.get("/api/agents/research-agent").json()
        assert agent_after["tasks_executed"] == tasks_before + 1


class TestFilesAPI:
    """
    E2E tests for Files API - Session Evidence Viewing.

    Per RULE-028: Bug Fix vs Feature Validation
    Per GAP-DATA-003: Session evidence file viewing

    Created: 2024-12-28 after feature validation failure
    - Bug fix (async handler) was validated
    - Feature (file viewing) was NOT validated
    - Lesson: Always validate full user flow
    """

    def test_read_evidence_file_content(self, api_client):
        """
        Test reading evidence file content.

        This is the critical test that was MISSING when the bug fix was declared "complete".
        The bug fix stopped the crash, but this test validates the feature actually works.

        Validation Hierarchy (RULE-028):
        - Level 1: API returns 200 (not 404)
        - Level 2: Response contains file content
        - Level 3: Content is the actual file data
        """
        # Test with a known evidence file
        response = api_client.get(
            "/api/files/content",
            params={"path": "evidence/SESSION-DECISIONS-2024-12-24.md"}
        )

        # Level 1: Endpoint exists and returns success
        assert response.status_code == 200, (
            f"Files endpoint returned {response.status_code}. "
            "If 404, check: 1) API server restarted? 2) files_router included in api.py?"
        )

        # Level 2: Response has expected structure
        data = response.json()
        assert "path" in data, "Response missing 'path' field"
        assert "content" in data, "Response missing 'content' field"
        assert "size" in data, "Response missing 'size' field"

        # Level 3: Content is actual file data (not empty, not error message)
        assert len(data["content"]) > 100, "Content appears too short for evidence file"
        assert "DECISION-001" in data["content"], (
            "Content doesn't contain expected 'DECISION-001' text from evidence file"
        )

    def test_read_evidence_file_security_denied(self, api_client):
        """Test that unauthorized paths are denied."""
        # Try to read outside allowed directories
        response = api_client.get(
            "/api/files/content",
            params={"path": "../../../etc/passwd"}
        )
        assert response.status_code == 403, "Should deny path traversal attempts"

    def test_read_evidence_file_not_found(self, api_client):
        """Test 404 for non-existent files."""
        response = api_client.get(
            "/api/files/content",
            params={"path": "evidence/NON-EXISTENT-FILE.md"}
        )
        assert response.status_code == 404, "Should return 404 for missing files"

    def test_read_docs_file_content(self, api_client):
        """Test reading documentation files."""
        response = api_client.get(
            "/api/files/content",
            params={"path": "docs/RULES-DIRECTIVES.md"}
        )
        assert response.status_code == 200, "Should be able to read docs/ files"

        data = response.json()
        assert "RULE-" in data["content"], "Docs file should contain rule references"


class TestUISmokeTests:
    """
    UI Smoke Tests - Validate all views load correctly.

    Per GAP-UI-028: Tests pass but UI broken
    Per RULE-028: Validation Hierarchy (Level 1-3)

    These tests validate that all navigation views load and display expected content.
    This catches issues where API tests pass but UI has broken routes/components.

    Created: 2024-12-28 after exploratory testing revealed:
    - All 12 navigation views load correctly
    - Executive Report has data discrepancy (0 Rules when 25 exist)
    - Test data pollution in Tasks view (168 tasks including TEST-*)

    Prerequisites:
    - API server running on port 8082
    """

    def test_rules_view_loads_with_data(self, api_client):
        """
        Test Rules view loads and has rules data.

        Level 1: API returns 200
        Level 2: Response is non-empty list
        Level 3: Rules have expected structure
        """
        response = api_client.get("/api/rules")
        assert response.status_code == 200, "Rules API should return 200"

        rules = response.json()
        assert isinstance(rules, list), "Rules should be a list"
        assert len(rules) > 0, "Rules list should not be empty"

        # Validate structure
        rule = rules[0]
        assert "id" in rule, "Rule should have 'id' field"
        assert "name" in rule, "Rule should have 'name' field"
        assert "category" in rule, "Rule should have 'category' field"
        assert "priority" in rule, "Rule should have 'priority' field"

    def test_tasks_view_loads_with_data(self, api_client):
        """
        Test Tasks view loads and has tasks data.

        Level 1: API returns 200
        Level 2: Response is non-empty list
        Level 3: Tasks have expected structure
        """
        response = api_client.get("/api/tasks")
        assert response.status_code == 200, "Tasks API should return 200"

        tasks = response.json()
        assert isinstance(tasks, list), "Tasks should be a list"

        if tasks:
            task = tasks[0]
            assert "task_id" in task, "Task should have 'task_id' field"
            assert "status" in task, "Task should have 'status' field"

    def test_agents_view_loads_with_data(self, api_client):
        """
        Test Agents view loads and has agents data.

        Level 1: API returns 200
        Level 2: Response is non-empty list
        Level 3: Agents have expected structure with trust scores
        """
        response = api_client.get("/api/agents")
        assert response.status_code == 200, "Agents API should return 200"

        agents = response.json()
        assert isinstance(agents, list), "Agents should be a list"
        assert len(agents) > 0, "Agents list should not be empty"

        # Validate structure
        agent = agents[0]
        assert "agent_id" in agent, "Agent should have 'agent_id' field"
        assert "trust_score" in agent, "Agent should have 'trust_score' field"
        assert 0 <= agent["trust_score"] <= 1, "Trust score should be between 0 and 1"

    def test_sessions_view_loads_with_data(self, api_client):
        """
        Test Sessions view loads and has sessions data.

        Level 1: API returns 200
        Level 2: Response is list (may be empty)
        Level 3: Sessions have expected structure
        """
        response = api_client.get("/api/sessions")
        assert response.status_code == 200, "Sessions API should return 200"

        sessions = response.json()
        assert isinstance(sessions, list), "Sessions should be a list"

    def test_decisions_view_loads_with_data(self, api_client):
        """
        Test Decisions view loads and has decisions data.

        Level 1: API returns 200
        Level 2: Response is list (may be empty without TypeDB)
        """
        response = api_client.get("/api/decisions")
        # May be 200 or 500 if TypeDB not connected
        assert response.status_code in (200, 500), f"Decisions API returned {response.status_code}"

        if response.status_code == 200:
            decisions = response.json()
            assert isinstance(decisions, list), "Decisions should be a list"

    def test_evidence_view_loads_with_data(self, api_client):
        """
        Test Evidence view loads and has evidence data.

        Level 1: API returns 200
        Level 2: Response is list of evidence files
        """
        response = api_client.get("/api/evidence")
        assert response.status_code == 200, "Evidence API should return 200"

        evidence = response.json()
        assert isinstance(evidence, list), "Evidence should be a list"

    def test_health_endpoint_returns_stats(self, api_client):
        """
        Test Health endpoint returns system stats.

        This is used by UI header to show rule/decision counts.
        GAP: Executive Report shows 0 Rules when health shows 25+
        """
        response = api_client.get("/api/health")
        assert response.status_code in (200, 503), f"Health API returned {response.status_code}"

        data = response.json()
        assert "status" in data, "Health should have 'status' field"
        assert "rules_count" in data, "Health should have 'rules_count' field"
        assert "decisions_count" in data, "Health should have 'decisions_count' field"

        # Note: If rules_count is 0 but UI shows 25, there's a data sync issue
        # This test documents the expected behavior

    def test_executive_report_endpoint(self, api_client):
        """
        Test Executive Report endpoint generates report.

        GAP-UI-029: Executive Report shows 0 Rules/Agents in stats cards
        but has correct counts in health endpoint.
        """
        response = api_client.get("/api/reports/executive")
        assert response.status_code == 200, "Executive Report API should return 200"

        report = response.json()
        assert "sections" in report, "Report should have 'sections' field"
        assert "generated_at" in report, "Report should have 'generated_at' field"

    def test_available_tasks_for_backlog(self, api_client):
        """
        Test Available Tasks endpoint for Backlog view.

        Level 1: API returns 200
        Level 2: Response is list of available tasks
        """
        response = api_client.get("/api/tasks/available")
        assert response.status_code == 200, "Available Tasks API should return 200"

        tasks = response.json()
        assert isinstance(tasks, list), "Available Tasks should be a list"


class TestDataIntegrity:
    """
    Data Integrity Tests - Validate data consistency across views.

    Per GAP-UI-029: Executive Report data discrepancy
    """

    def test_rules_count_matches_health(self, api_client):
        """
        Test that rules count matches between /api/rules and /api/health.

        This catches data sync issues where one endpoint has stale data.
        """
        # Get rules list
        rules_response = api_client.get("/api/rules")
        if rules_response.status_code != 200:
            pytest.skip("Rules API not available")
        rules_count = len(rules_response.json())

        # Get health stats
        health_response = api_client.get("/api/health")
        if health_response.status_code not in (200, 503):
            pytest.skip("Health API not available")

        health_data = health_response.json()
        health_rules_count = health_data.get("rules_count", 0)

        # They should match
        assert rules_count == health_rules_count, (
            f"Rules count mismatch: /api/rules has {rules_count}, "
            f"/api/health reports {health_rules_count}"
        )

    def test_agents_count_matches_list(self, api_client):
        """
        Test that agents count is consistent.
        """
        # Get agents list
        agents_response = api_client.get("/api/agents")
        assert agents_response.status_code == 200, "Agents API should return 200"

        agents = agents_response.json()
        agents_count = len(agents)

        # Should have at least the seed agents
        assert agents_count >= 5, (
            f"Expected at least 5 seed agents, got {agents_count}"
        )


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
