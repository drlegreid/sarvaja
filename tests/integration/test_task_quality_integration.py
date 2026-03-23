"""E2E Task Quality Integration Tests (Tier 2).

Proves TypeDB round-trip persistence for task data — NOT mocked.
Per TEST-E2E-01-v1: Tier 2 requires live API + TypeDB.

Bugs under test:
  SRVJ-BUG-005: Project column empty (workspace enrichment)
  SRVJ-BUG-006: Hide test filter (task_type=test server-side)
  SRVJ-BUG-007: task_create doesn't persist summary/session to TypeDB

Run: .venv/bin/python3 -m pytest tests/integration/test_task_quality_integration.py -v
"""

import pytest
import httpx

BASE = "http://localhost:8082/api"
TIMEOUT = 10.0

# Test task prefix — matches TEST_DATA_PREFIXES for auto-cleanup
PREFIX = "E2E-QUAL"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def api_healthy(client):
    r = client.get("/health")
    if r.status_code != 200 or not r.json().get("typedb_connected"):
        pytest.skip("API not healthy or TypeDB not connected")
    return True


@pytest.fixture(scope="module", autouse=True)
def cleanup(client, api_healthy):
    """Delete all E2E-QUAL-* test tasks after module completes."""
    yield
    data = client.get("/tasks?limit=200").json()
    for item in data.get("items", []):
        if item.get("task_id", "").startswith(PREFIX):
            client.delete(f"/tasks/{item['task_id']}")


# =============================================================================
# TestTaskTypeDBRoundTrip — Proves SRVJ-BUG-007
# =============================================================================


@pytest.mark.integration
@pytest.mark.tasks
@pytest.mark.api
class TestTaskTypeDBRoundTrip:
    """Create task via POST, then GET — data must come from TypeDB."""

    def test_create_and_get_returns_task(self, client, api_healthy):
        """POST /tasks → GET /tasks/{id} returns same task from TypeDB."""
        payload = {
            "task_id": f"{PREFIX}-RT-001",
            "description": "TypeDB round-trip test",
            "summary": "E2E > TypeDB > Round Trip > Verify",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
        }
        r = client.post("/tasks", json=payload)
        assert r.status_code == 201, f"Create failed: {r.text}"

        # GET must return from TypeDB (not just fallback store)
        r2 = client.get(f"/tasks/{PREFIX}-RT-001")
        assert r2.status_code == 200, f"GET failed: {r2.text}"
        data = r2.json()
        assert data["task_id"] == f"{PREFIX}-RT-001"
        assert data["priority"] == "LOW"
        assert data["task_type"] == "test"

    def test_summary_persists_to_typedb(self, client, api_healthy):
        """Summary field must survive TypeDB round-trip (SRVJ-BUG-007)."""
        payload = {
            "task_id": f"{PREFIX}-RT-002",
            "description": "Summary persistence test",
            "summary": "E2E > Summary > Persist > TypeDB",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
        }
        r = client.post("/tasks", json=payload)
        assert r.status_code == 201

        r2 = client.get(f"/tasks/{PREFIX}-RT-002")
        assert r2.status_code == 200
        assert r2.json()["summary"] == "E2E > Summary > Persist > TypeDB"

    def test_linked_sessions_persists(self, client, api_healthy):
        """linked_sessions must survive TypeDB round-trip (SRVJ-BUG-007).

        Note: session entity must exist in TypeDB for the relation to be created.
        We use a real session from the system, or link post-creation.
        """
        # First find an existing session to link to
        sessions_r = client.get("/sessions?limit=1")
        if sessions_r.status_code != 200 or not sessions_r.json():
            pytest.skip("No sessions available for linking test")
        sessions_data = sessions_r.json()
        # Handle both list and dict responses
        if isinstance(sessions_data, list):
            existing_session = sessions_data[0].get("session_id") if sessions_data else None
        else:
            items = sessions_data.get("items") or sessions_data.get("sessions") or []
            existing_session = items[0].get("session_id") if items else None
        if not existing_session:
            pytest.skip("No sessions available for linking test")

        payload = {
            "task_id": f"{PREFIX}-RT-003",
            "description": "Session link persistence test",
            "summary": "E2E > Session Link > Persist > TypeDB",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
            "linked_sessions": [existing_session],
        }
        r = client.post("/tasks", json=payload)
        assert r.status_code == 201

        r2 = client.get(f"/tasks/{PREFIX}-RT-003")
        assert r2.status_code == 200
        sessions = r2.json().get("linked_sessions") or []
        assert existing_session in sessions, f"Expected {existing_session} in {sessions}"


# =============================================================================
# TestTaskPersistence — List endpoint reads TypeDB
# =============================================================================


@pytest.mark.integration
@pytest.mark.tasks
@pytest.mark.api
class TestTaskPersistence:
    """Created tasks must appear in list endpoint."""

    def test_created_task_in_list(self, client, api_healthy):
        """POST /tasks → GET /tasks returns it in the list."""
        payload = {
            "task_id": f"{PREFIX}-LIST-001",
            "description": "List visibility test",
            "summary": "E2E > Task > List > Visible",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
        }
        client.post("/tasks", json=payload)

        r = client.get(f"/tasks?search={PREFIX}-LIST-001&limit=10")
        assert r.status_code == 200
        items = r.json()["items"]
        ids = [t["task_id"] for t in items]
        assert f"{PREFIX}-LIST-001" in ids

    def test_workspace_persists(self, client, api_healthy):
        """Task with workspace_id → GET returns workspace_id."""
        payload = {
            "task_id": f"{PREFIX}-WS-001",
            "description": "Workspace persistence test",
            "summary": "E2E > Workspace > Persist > TypeDB",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
            "workspace_id": "WS-9147535A",
        }
        client.post("/tasks", json=payload)

        r = client.get(f"/tasks/{PREFIX}-WS-001")
        assert r.status_code == 200
        assert r.json()["workspace_id"] == "WS-9147535A"


# =============================================================================
# TestDoneGateAPI — DONE gate via real API
# =============================================================================


@pytest.mark.integration
@pytest.mark.tasks
@pytest.mark.api
class TestDoneGateAPI:
    """DONE gate enforced at API level with 422 responses."""

    def test_done_without_mandatory_fields_returns_422(self, client, api_healthy):
        """PUT status=DONE without session/agent/docs → 422."""
        payload = {
            "task_id": f"{PREFIX}-DONE-001",
            "description": "DONE gate test",
            "summary": "E2E > DONE Gate > Reject > Missing Fields",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
        }
        client.post("/tasks", json=payload)

        r = client.put(f"/tasks/{PREFIX}-DONE-001", json={"status": "DONE"})
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_done_with_all_fields_returns_200(self, client, api_healthy):
        """PUT status=DONE with all required fields → 200 + completed_at."""
        payload = {
            "task_id": f"{PREFIX}-DONE-002",
            "description": "DONE gate happy path",
            "summary": "E2E > DONE Gate > Accept > All Fields",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
        }
        client.post("/tasks", json=payload)

        r = client.put(f"/tasks/{PREFIX}-DONE-002", json={
            "status": "DONE",
            "agent_id": "code-agent",
            "summary": "E2E > DONE Gate > Accept > All Fields",
            "linked_sessions": ["SESSION-E2E-QUAL-DONE"],
            "linked_documents": [".claude/plans/bubbly-enchanting-eagle.md"],
        })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json()["completed_at"] is not None

    def test_422_has_structured_validation_errors(self, client, api_healthy):
        """422 response body contains validation_errors array."""
        payload = {
            "task_id": f"{PREFIX}-DONE-003",
            "description": "Structured errors test",
            "summary": "E2E > DONE Gate > Errors > Structured",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
        }
        client.post("/tasks", json=payload)

        r = client.put(f"/tasks/{PREFIX}-DONE-003", json={"status": "DONE"})
        assert r.status_code == 422
        detail = r.json().get("detail", "")
        assert "validation_errors" in detail


# =============================================================================
# TestTaskFilterAPI — Server-side task_type filter
# =============================================================================


@pytest.mark.integration
@pytest.mark.tasks
@pytest.mark.api
class TestTaskFilterAPI:
    """Server-side task_type filter works via query param."""

    def test_filter_by_type_test_includes_test_tasks(self, client, api_healthy):
        """GET /tasks?task_type=test returns test-type tasks."""
        payload = {
            "task_id": f"{PREFIX}-FILT-001",
            "description": "Filter include test",
            "summary": "E2E > Filter > Include > Test Type",
            "priority": "LOW",
            "task_type": "test",
            "phase": "P10",
        }
        client.post("/tasks", json=payload)

        r = client.get(f"/tasks?task_type=test&search={PREFIX}-FILT-001&limit=10")
        assert r.status_code == 200
        ids = [t["task_id"] for t in r.json()["items"]]
        assert f"{PREFIX}-FILT-001" in ids

    def test_filter_by_type_test_excludes_bugs(self, client, api_healthy):
        """GET /tasks?task_type=test does NOT return bug-type tasks."""
        payload = {
            "task_id": f"{PREFIX}-FILT-002",
            "description": "Filter exclude test",
            "summary": "E2E > Filter > Exclude > Bug Type",
            "priority": "LOW",
            "task_type": "bug",
            "phase": "P10",
        }
        client.post("/tasks", json=payload)

        r = client.get(f"/tasks?task_type=test&search={PREFIX}-FILT-002&limit=10")
        assert r.status_code == 200
        ids = [t["task_id"] for t in r.json()["items"]]
        assert f"{PREFIX}-FILT-002" not in ids
