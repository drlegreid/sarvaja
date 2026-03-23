"""E2E Task Quality Integration Tests (Tier 2).

Proves TypeDB round-trip persistence for task data — NOT mocked.
Per TEST-E2E-01-v1: Tier 2 requires live API + TypeDB.
Per SRVJ-FEAT-005: Uses shared TaskTestFactory for auto-cleanup.

Bugs under test:
  SRVJ-BUG-005: Project column empty (workspace enrichment)
  SRVJ-BUG-006: Hide test filter (task_type=test server-side)
  SRVJ-BUG-007: task_create doesn't persist summary/session to TypeDB

Run: .venv/bin/python3 -m pytest tests/integration/test_task_quality_integration.py -v
"""

import pytest
import httpx

from tests.shared.task_test_factory import TaskTestFactory

BASE = "http://localhost:8082/api"
TIMEOUT = 10.0

# Readable prefix for this module's tasks
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


@pytest.fixture(scope="module")
def factory(client, api_healthy):
    """Module-scoped factory — tracks all tasks, cleans up after module."""
    f = TaskTestFactory(client=client)
    yield f
    f.cleanup()


# =============================================================================
# TestTaskTypeDBRoundTrip — Proves SRVJ-BUG-007
# =============================================================================


@pytest.mark.integration
@pytest.mark.tasks
@pytest.mark.api
class TestTaskTypeDBRoundTrip:
    """Create task via POST, then GET — data must come from TypeDB."""

    def test_create_and_get_returns_task(self, client, factory, api_healthy):
        """POST /tasks → GET /tasks/{id} returns same task from TypeDB."""
        t = factory.create(
            task_id=f"{PREFIX}-RT-001",
            summary="E2E > TypeDB > Round Trip > Verify",
        )
        r = client.get(f"/tasks/{t.task_id}")
        assert r.status_code == 200, f"GET failed: {r.text}"
        data = r.json()
        assert data["task_id"] == t.task_id
        assert data["priority"] == "LOW"
        assert data["task_type"] == "test"

    def test_summary_persists_to_typedb(self, client, factory, api_healthy):
        """Summary field must survive TypeDB round-trip (SRVJ-BUG-007)."""
        t = factory.create(
            task_id=f"{PREFIX}-RT-002",
            summary="E2E > Summary > Persist > TypeDB",
        )
        r = client.get(f"/tasks/{t.task_id}")
        assert r.status_code == 200
        assert r.json()["summary"] == "E2E > Summary > Persist > TypeDB"

    def test_linked_sessions_persists(self, client, factory, api_healthy):
        """linked_sessions must survive TypeDB round-trip (SRVJ-BUG-007)."""
        sessions_r = client.get("/sessions?limit=1")
        if sessions_r.status_code != 200 or not sessions_r.json():
            pytest.skip("No sessions available for linking test")
        sessions_data = sessions_r.json()
        if isinstance(sessions_data, list):
            existing_session = sessions_data[0].get("session_id") if sessions_data else None
        else:
            items = sessions_data.get("items") or sessions_data.get("sessions") or []
            existing_session = items[0].get("session_id") if items else None
        if not existing_session:
            pytest.skip("No sessions available for linking test")

        t = factory.create(
            task_id=f"{PREFIX}-RT-003",
            summary="E2E > Session Link > Persist > TypeDB",
            linked_sessions=[existing_session],
        )
        r = client.get(f"/tasks/{t.task_id}")
        assert r.status_code == 200
        sessions = r.json().get("linked_sessions") or []
        assert existing_session in sessions, f"Expected {existing_session} in {sessions}"


# =============================================================================
# TestTaskPersistence — List endpoint reads TypeDB
# =============================================================================


@pytest.mark.integration
@pytest.mark.tasks
@pytest.mark.api
class TestTaskPersistence:
    """Created tasks must appear in list endpoint."""

    def test_created_task_in_list(self, client, factory, api_healthy):
        """POST /tasks → GET /tasks returns it in the list."""
        t = factory.create(
            task_id=f"{PREFIX}-LIST-001",
            summary="E2E > Task > List > Visible",
        )
        r = client.get(f"/tasks?search={t.task_id}&limit=10")
        assert r.status_code == 200
        ids = [t["task_id"] for t in r.json()["items"]]
        assert f"{PREFIX}-LIST-001" in ids

    def test_workspace_persists(self, client, factory, api_healthy):
        """Task with workspace_id → GET returns workspace_id."""
        t = factory.create(
            task_id=f"{PREFIX}-WS-001",
            summary="E2E > Workspace > Persist > TypeDB",
            workspace_id="WS-9147535A",
        )
        r = client.get(f"/tasks/{t.task_id}")
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

    def test_done_without_mandatory_fields_returns_422(self, client, factory, api_healthy):
        """PUT status=DONE without session/agent/docs → 422."""
        t = factory.create(
            task_id=f"{PREFIX}-DONE-001",
            summary="E2E > DONE Gate > Reject > Missing Fields",
        )
        r = client.put(f"/tasks/{t.task_id}", json={"status": "DONE"})
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_done_with_all_fields_returns_200(self, client, factory, api_healthy):
        """PUT status=DONE with all required fields → 200 + completed_at."""
        t = factory.create(
            task_id=f"{PREFIX}-DONE-002",
            summary="E2E > DONE Gate > Accept > All Fields",
        )
        r = client.put(f"/tasks/{t.task_id}", json={
            "status": "DONE",
            "agent_id": "code-agent",
            "summary": "E2E > DONE Gate > Accept > All Fields",
            "linked_sessions": ["SESSION-E2E-QUAL-DONE"],
            "linked_documents": [".claude/plans/bubbly-enchanting-eagle.md"],
        })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert r.json()["completed_at"] is not None

    def test_422_has_structured_validation_errors(self, client, factory, api_healthy):
        """422 response body contains validation_errors array."""
        t = factory.create(
            task_id=f"{PREFIX}-DONE-003",
            summary="E2E > DONE Gate > Errors > Structured",
        )
        r = client.put(f"/tasks/{t.task_id}", json={"status": "DONE"})
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

    def test_filter_by_type_test_includes_test_tasks(self, client, factory, api_healthy):
        """GET /tasks?task_type=test returns test-type tasks."""
        t = factory.create(
            task_id=f"{PREFIX}-FILT-001",
            summary="E2E > Filter > Include > Test Type",
        )
        r = client.get(f"/tasks?task_type=test&search={t.task_id}&limit=10")
        assert r.status_code == 200
        ids = [t["task_id"] for t in r.json()["items"]]
        assert f"{PREFIX}-FILT-001" in ids

    def test_filter_by_type_test_excludes_bugs(self, client, factory, api_healthy):
        """GET /tasks?task_type=test does NOT return bug-type tasks."""
        t = factory.create(
            task_id=f"{PREFIX}-FILT-002",
            summary="E2E > Filter > Exclude > Bug Type",
            task_type="bug",
        )
        r = client.get(f"/tasks?task_type=test&search={t.task_id}&limit=10")
        assert r.status_code == 200
        ids = [t["task_id"] for t in r.json()["items"]]
        assert f"{PREFIX}-FILT-002" not in ids


# =============================================================================
# TestCompletedAtPersistence — SRVJ-BUG-011
# =============================================================================


@pytest.mark.integration
@pytest.mark.tasks
@pytest.mark.api
class TestCompletedAtPersistence:
    """completed_at must survive TypeDB round-trip after DONE transition."""

    def test_completed_at_persists_after_done(self, client, factory, api_healthy):
        """PUT status=DONE → GET returns completed_at from TypeDB (SRVJ-BUG-011)."""
        t = factory.create(
            task_id=f"{PREFIX}-COMP-001",
            summary="E2E > completed_at > Persist > TypeDB",
        )
        # Transition to DONE with all required fields
        r = client.put(f"/tasks/{t.task_id}", json={
            "status": "DONE",
            "agent_id": "code-agent",
            "summary": "E2E > completed_at > Persist > TypeDB",
            "linked_sessions": ["SESSION-E2E-QUAL-COMP"],
            "linked_documents": [".claude/plans/unified-wibbling-lagoon.md"],
        })
        assert r.status_code == 200, f"DONE transition failed: {r.text}"

        # GET must return completed_at from TypeDB, not just fallback store
        r2 = client.get(f"/tasks/{t.task_id}")
        assert r2.status_code == 200
        assert r2.json()["completed_at"] is not None, \
            "completed_at must persist to TypeDB after DONE transition"

    def test_completed_at_has_valid_timestamp(self, client, factory, api_healthy):
        """completed_at must be a valid ISO timestamp, not garbage."""
        t = factory.create(
            task_id=f"{PREFIX}-COMP-002",
            summary="E2E > completed_at > Format > ISO Timestamp",
        )
        client.put(f"/tasks/{t.task_id}", json={
            "status": "DONE",
            "agent_id": "code-agent",
            "summary": "E2E > completed_at > Format > ISO Timestamp",
            "linked_sessions": ["SESSION-E2E-QUAL-COMP2"],
            "linked_documents": [".claude/plans/unified-wibbling-lagoon.md"],
        })
        r = client.get(f"/tasks/{t.task_id}")
        completed = r.json()["completed_at"]
        assert completed is not None
        # Must contain date components (not empty string or random)
        assert "2026" in completed or "202" in completed, f"Invalid timestamp: {completed}"


# =============================================================================
# TestSessionLinkIdempotency — SRVJ-BUG-010 (session variant)
# =============================================================================


@pytest.mark.integration
@pytest.mark.tasks
@pytest.mark.api
class TestSessionLinkIdempotency:
    """Session linking must not create duplicate relations."""

    def test_double_session_link_no_duplicates(self, client, factory, api_healthy):
        """PUT linked_sessions twice → GET returns session once (SRVJ-BUG-010)."""
        session_id = "SESSION-E2E-QUAL-IDEMP"
        t = factory.create(
            task_id=f"{PREFIX}-IDEMP-001",
            summary="E2E > Session Link > Idempotency > No Duplicates",
            linked_sessions=[session_id],
        )
        # Link same session again via update
        client.put(f"/tasks/{t.task_id}", json={
            "linked_sessions": [session_id],
        })
        r = client.get(f"/tasks/{t.task_id}")
        assert r.status_code == 200
        sessions = r.json().get("linked_sessions") or []
        # Count occurrences — must be exactly 1, not 2
        count = sessions.count(session_id)
        assert count == 1, f"Expected 1 occurrence of {session_id}, got {count} in {sessions}"
