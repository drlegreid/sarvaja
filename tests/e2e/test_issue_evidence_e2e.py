"""
E2E Tests: EPIC-ISSUE-EVIDENCE — FEAT-009, P18, P19
====================================================
Per TEST-E2E-01-v1: Gherkin-first, then executed as integration tests.
Spec: docs/backlog/specs/E2E-T3-ISSUE-EVIDENCE.gherkin.md

Tier 2: API-level CRUD verification (httpx → :8082)
Tier 3: Playwright UI interaction with state change verification
"""

import json
import uuid
import pytest
import httpx

from tests.e2e.conftest import API_URL, cleanup_test_entities

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api():
    """API client for Tier 2 tests."""
    client = httpx.Client(base_url=API_URL, timeout=30.0)
    yield client
    client.close()


@pytest.fixture
def unique_id():
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# FEAT-009: Active Session Detection
# ---------------------------------------------------------------------------

class TestFeat009ActiveSessionDetection:
    """FEAT-009: session_list MCP returns CC sessions."""

    def test_sessions_api_returns_active(self, api):
        """GET /api/sessions?status=ACTIVE returns results."""
        resp = api.get("/api/sessions", params={"status": "ACTIVE", "limit": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] > 0, "Expected at least 1 ACTIVE session"
        for item in data["items"]:
            assert item["status"] == "ACTIVE"


# ---------------------------------------------------------------------------
# P18: Multi-Session Timeline Merge
# ---------------------------------------------------------------------------

class TestP18TaskTimeline:
    """P18: GET /api/tasks/{id}/timeline endpoint."""

    def _find_task_with_sessions(self, api) -> str:
        """Find a real task that has linked_sessions."""
        resp = api.get("/api/tasks", params={"limit": 50})
        assert resp.status_code == 200
        for task in resp.json()["items"]:
            if task.get("linked_sessions"):
                return task["task_id"]
        pytest.skip("No tasks with linked_sessions found")

    def test_timeline_returns_entries(self, api):
        """Timeline endpoint returns chronological entries."""
        task_id = self._find_task_with_sessions(api)
        resp = api.get(f"/api/tasks/{task_id}/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "total" in data
        assert "session_ids" in data
        assert len(data["session_ids"]) > 0
        # Verify entry structure
        for entry in data["entries"]:
            assert "timestamp" in entry
            assert "entry_type" in entry
            assert "session_id" in entry
            assert "title" in entry
            assert "icon" in entry
            assert "color" in entry

    def test_timeline_pagination(self, api):
        """Timeline pagination returns correct metadata."""
        task_id = self._find_task_with_sessions(api)
        resp = api.get(
            f"/api/tasks/{task_id}/timeline",
            params={"page": 1, "per_page": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert len(data["entries"]) <= 2
        assert isinstance(data["has_more"], bool)

    def test_timeline_entry_type_filter(self, api):
        """Filter entries by type."""
        task_id = self._find_task_with_sessions(api)
        resp = api.get(
            f"/api/tasks/{task_id}/timeline",
            params={"entry_types": "thought"},
        )
        assert resp.status_code == 200
        for entry in resp.json()["entries"]:
            assert entry["entry_type"] == "thought"

    def test_timeline_404_unknown_task(self, api):
        """Unknown task returns 404."""
        resp = api.get("/api/tasks/NONEXISTENT-TASK-XYZ/timeline")
        assert resp.status_code == 404

    def test_timeline_chronological_order(self, api):
        """Entries are sorted by timestamp ascending."""
        task_id = self._find_task_with_sessions(api)
        resp = api.get(f"/api/tasks/{task_id}/timeline")
        assert resp.status_code == 200
        entries = resp.json()["entries"]
        timestamps = [e["timestamp"] for e in entries if e["timestamp"]]
        assert timestamps == sorted(timestamps), "Entries not in chronological order"


# ---------------------------------------------------------------------------
# P19: Resolution Comments
# ---------------------------------------------------------------------------

class TestP19ResolutionComments:
    """P19: Task comments CRUD via REST API."""

    def _find_done_task(self, api) -> str:
        """Find a DONE task for comment testing."""
        resp = api.get("/api/tasks", params={"status": "DONE", "limit": 5})
        assert resp.status_code == 200
        items = resp.json()["items"]
        if not items:
            pytest.skip("No DONE tasks found")
        return items[0]["task_id"]

    def test_comments_crud_lifecycle(self, api):
        """Full lifecycle: create → list → verify → delete → verify gone."""
        task_id = self._find_done_task(api)

        # Create
        resp = api.post(
            f"/api/tasks/{task_id}/comments",
            json={"body": "E2E lifecycle test comment", "author": "e2e-test"},
        )
        assert resp.status_code == 201
        comment = resp.json()
        comment_id = comment["comment_id"]
        assert comment_id.startswith("CMT-")
        assert comment["body"] == "E2E lifecycle test comment"
        assert comment["author"] == "e2e-test"
        assert "created_at" in comment

        # List — should contain our comment
        resp = api.get(f"/api/tasks/{task_id}/comments")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        found = [c for c in data["comments"] if c["comment_id"] == comment_id]
        assert len(found) == 1

        # Delete
        resp = api.delete(f"/api/tasks/{task_id}/comments/{comment_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Verify gone
        resp = api.get(f"/api/tasks/{task_id}/comments")
        found = [c for c in resp.json()["comments"] if c["comment_id"] == comment_id]
        assert len(found) == 0

    def test_comments_empty_list(self, api, unique_id):
        """Task with no comments returns empty list."""
        resp = api.get(f"/api/tasks/{unique_id}/comments")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["comments"] == []

    def test_comments_delete_nonexistent_404(self, api):
        """Delete non-existent comment returns 404."""
        task_id = self._find_done_task(api)
        resp = api.delete(f"/api/tasks/{task_id}/comments/CMT-nonexist")
        assert resp.status_code == 404

    def test_comments_chronological_order(self, api):
        """Multiple comments are returned oldest-first."""
        task_id = self._find_done_task(api)
        ids = []
        for i in range(3):
            resp = api.post(
                f"/api/tasks/{task_id}/comments",
                json={"body": f"Order test {i}", "author": "e2e-test"},
            )
            assert resp.status_code == 201
            ids.append(resp.json()["comment_id"])

        resp = api.get(f"/api/tasks/{task_id}/comments")
        comments = resp.json()["comments"]
        timestamps = [c["created_at"] for c in comments]
        assert timestamps == sorted(timestamps), "Comments not chronological"

        # Cleanup
        for cid in ids:
            api.delete(f"/api/tasks/{task_id}/comments/{cid}")

    def test_comment_body_validation(self, api):
        """Empty body is rejected with 422."""
        task_id = self._find_done_task(api)
        resp = api.post(
            f"/api/tasks/{task_id}/comments",
            json={"body": "", "author": "e2e-test"},
        )
        assert resp.status_code == 422
