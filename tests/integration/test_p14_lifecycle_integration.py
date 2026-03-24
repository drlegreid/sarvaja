"""
Integration tests for P14: Task Lifecycle States against live API.

Tier 2: Exercises full stack — REST API → service layer → TypeDB.
Requires: API running on localhost:8082, TypeDB on localhost:1729.

Per TEST-E2E-01-v1: Integration tier proves real API returns correct data.
"""

import pytest
import httpx
import uuid

API_BASE = "http://localhost:8082"
WORKSPACE_ID = "WS-9147535A"
PLAN_DOC = ".claude/plans/radiant-iron-compass.md"


def _unique_id(prefix: str = "SRVJ-INTTEST") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


def _create_task(client, task_id, **overrides):
    """Create a test task with sensible defaults."""
    payload = {
        "task_id": task_id,
        "summary": "P14 > Integration > Lifecycle > Test",
        "description": "Integration test task for P14",
        "phase": "P14",
        "status": "TODO",
        "task_type": "test",
        "priority": "LOW",
        **overrides,
    }
    resp = client.post("/api/tasks", json=payload)
    assert resp.status_code in (200, 201), f"Create failed: {resp.status_code} {resp.text}"
    return resp.json()


@pytest.fixture
def api_client():
    """httpx client with timeout."""
    with httpx.Client(base_url=API_BASE, timeout=15.0) as client:
        yield client


@pytest.fixture
def test_task(api_client):
    """Create a test task and clean up after."""
    task_id = _unique_id()
    _create_task(api_client, task_id, workspace_id=WORKSPACE_ID)
    yield task_id
    api_client.delete(f"/api/tasks/{task_id}")


class TestTaskLifecycleIntegration:
    """Full lifecycle: TODO → IN_PROGRESS → DONE with preloaded documents."""

    def test_create_and_cancel(self, api_client, test_task):
        """Create task, set to IN_PROGRESS, then CANCEL — verify CANCELED in TypeDB."""
        task_id = test_task

        # Move to IN_PROGRESS
        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

        # Cancel it
        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "status": "CANCELED",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELED"

        # Verify via GET
        resp = api_client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELED"

    def test_done_gate_with_linked_document(self, api_client, test_task):
        """DONE gate passes when linked_documents exist via link_document."""
        task_id = test_task

        # Move to IN_PROGRESS
        api_client.put(f"/api/tasks/{task_id}", json={
            "status": "IN_PROGRESS",
            "agent_id": "code-agent",
        })

        # Link a document (POST /tasks/{id}/documents with body)
        resp = api_client.post(
            f"/api/tasks/{task_id}/documents",
            json={"document_path": PLAN_DOC},
        )
        assert resp.status_code in (200, 201), f"Link doc failed: {resp.status_code} {resp.text}"

        # Link a session
        session_id = f"SESSION-P14-INTTEST-{uuid.uuid4().hex[:6]}"
        resp = api_client.post(
            f"/api/tasks/{task_id}/sessions/{session_id}",
        )
        assert resp.status_code in (200, 201, 204), f"Link session failed: {resp.status_code}"

        # Now try DONE — should pass because linked_documents & sessions exist
        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "status": "DONE",
            "summary": "P14 > Integration > Lifecycle > Verified",
            "agent_id": "code-agent",
            "linked_documents": [PLAN_DOC],
            "linked_sessions": [session_id],
        })
        assert resp.status_code == 200, f"DONE gate failed: {resp.text}"
        assert resp.json()["status"] == "DONE"

    def test_done_gate_fails_without_documents(self, api_client):
        """DONE gate must reject transition without linked_documents."""
        task_id = _unique_id()
        _create_task(api_client, task_id,
                     status="IN_PROGRESS", agent_id="code-agent")

        # Try DONE without linked_documents — should fail
        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "status": "DONE",
            "summary": "Trying to complete without docs",
            "agent_id": "code-agent",
            "linked_sessions": ["SES-FAKE"],
        })
        assert resp.status_code in (400, 422, 500), f"Expected rejection, got {resp.status_code}"

        # Cleanup
        api_client.delete(f"/api/tasks/{task_id}")

    def test_canceled_status_accepted_by_typedb(self, api_client):
        """TypeDB must accept CANCELED as a valid status."""
        task_id = _unique_id()
        _create_task(api_client, task_id)

        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "status": "CANCELED",
        })
        assert resp.status_code == 200, f"CANCELED rejected: {resp.text}"

        # Read back from TypeDB (fresh GET)
        resp = api_client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELED"

        # Cleanup
        api_client.delete(f"/api/tasks/{task_id}")
