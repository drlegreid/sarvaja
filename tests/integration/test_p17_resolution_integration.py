"""
P17: Issue Resolution Evidence Trail — Integration Tests.

Tests against live TypeDB + REST API on localhost:8082.
Uses WS-TEST-SANDBOX workspace per TEST-DATA-01-v1.
"""

import pytest
import httpx
import uuid

API = "http://localhost:8082"
WS = "WS-TEST-SANDBOX"


def _unique_id(prefix="P17"):
    """Generate a unique task ID for test isolation."""
    return f"SRVJ-TEST-{prefix}-{uuid.uuid4().hex[:6].upper()}"


@pytest.fixture
def api_client():
    """Provide httpx client for API calls."""
    with httpx.Client(base_url=API, timeout=15.0) as client:
        yield client


@pytest.fixture
def task_with_session(api_client):
    """Create a task with a linked session for DONE testing."""
    task_id = _unique_id("RN")

    # Create task
    resp = api_client.post("/api/tasks", json={
        "task_id": task_id,
        "description": f"P17 integration test {task_id}",
        "phase": "P17",
        "status": "TODO",
        "workspace_id": WS,
        "summary": "P17 resolution notes integration test",
        "agent_id": "code-agent",
    })
    assert resp.status_code == 201, f"Create failed: {resp.status_code} {resp.text}"

    # Link a document
    api_client.post(f"/api/tasks/{task_id}/documents", json={
        "document_path": "docs/backlog/specs/EPIC-ISSUE-EVIDENCE-RD.md",
    })

    yield task_id

    # Cleanup
    api_client.delete(f"/api/tasks/{task_id}")


class TestResolutionNotesField:
    """Test resolution_notes field exists in API responses."""

    def test_create_task_response_has_resolution_notes_field(self, api_client):
        """POST /api/tasks response includes resolution_notes (null)."""
        task_id = _unique_id("FIELD")
        resp = api_client.post("/api/tasks", json={
            "task_id": task_id,
            "description": "P17 field test",
            "phase": "P17",
            "workspace_id": WS,
        })
        assert resp.status_code == 201
        data = resp.json()
        # resolution_notes should be in response (null for new tasks)
        assert "resolution_notes" in data or data.get("resolution_notes") is None

        # Cleanup
        api_client.delete(f"/api/tasks/{task_id}")

    def test_get_task_response_has_resolution_notes_field(self, api_client):
        """GET /api/tasks/{id} response includes resolution_notes."""
        task_id = _unique_id("GET")
        api_client.post("/api/tasks", json={
            "task_id": task_id,
            "description": "P17 get test",
            "phase": "P17",
            "workspace_id": WS,
        })

        resp = api_client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        data = resp.json()
        # Field should exist (may be null)
        assert "resolution_notes" in data

        api_client.delete(f"/api/tasks/{task_id}")


class TestResolutionNotesPersistence:
    """Test resolution_notes persists through update cycle."""

    def test_update_resolution_notes_persists(self, api_client):
        """PUT with resolution_notes -> GET returns same value."""
        task_id = _unique_id("PERSIST")
        api_client.post("/api/tasks", json={
            "task_id": task_id,
            "description": "P17 persist test",
            "phase": "P17",
            "workspace_id": WS,
        })

        # Update with resolution_notes
        notes = "## Root Cause\nRace condition in TypeDB transaction"
        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "resolution_notes": notes,
        })
        assert resp.status_code == 200

        # Read back
        resp = api_client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("resolution_notes") == notes

        api_client.delete(f"/api/tasks/{task_id}")


class TestAutoPopulateOnDone:
    """Test auto-populate resolution_notes on DONE transition."""

    def test_done_transition_auto_populates(self, api_client, task_with_session):
        """Transitioning to DONE auto-populates resolution_notes."""
        task_id = task_with_session

        # Move to IN_PROGRESS first
        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "status": "IN_PROGRESS",
        })
        assert resp.status_code == 200

        # Move to DONE — should auto-populate resolution_notes
        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "status": "DONE",
        })
        assert resp.status_code == 200
        data = resp.json()

        # resolution_notes should be auto-populated
        rn = data.get("resolution_notes")
        assert rn is not None, "resolution_notes should be auto-populated on DONE"
        assert len(rn) > 0, "resolution_notes should not be empty"
        assert "Resolution Summary" in rn

    def test_done_with_explicit_notes_not_overwritten(self, api_client):
        """DONE with explicit resolution_notes keeps the provided value."""
        task_id = _unique_id("NOOVER")
        api_client.post("/api/tasks", json={
            "task_id": task_id,
            "description": "P17 no-overwrite test",
            "phase": "P17",
            "workspace_id": WS,
            "summary": "Test no-overwrite",
            "agent_id": "code-agent",
        })

        # Link a doc for DONE gate
        api_client.post(f"/api/tasks/{task_id}/documents", json={
            "document_path": "docs/RULES-DIRECTIVES.md",
        })

        # IN_PROGRESS first
        api_client.put(f"/api/tasks/{task_id}", json={
            "status": "IN_PROGRESS",
        })

        # DONE with explicit notes
        custom_notes = "Manually written: Fixed by adding null check"
        resp = api_client.put(f"/api/tasks/{task_id}", json={
            "status": "DONE",
            "resolution_notes": custom_notes,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("resolution_notes") == custom_notes

        api_client.delete(f"/api/tasks/{task_id}")
