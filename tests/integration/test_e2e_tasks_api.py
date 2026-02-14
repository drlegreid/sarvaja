"""E2E-T2-002: Task API Integration Tests (Tier 2).

Per TEST-E2E-01-v1 + EPIC-TESTING-E2E Phase 1.
Run: .venv/bin/python3 -m pytest tests/integration/test_e2e_tasks_api.py -v
"""

import pytest
import httpx

BASE = "http://localhost:8082/api"
TIMEOUT = 10.0


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def api_healthy(client):
    r = client.get("/health")
    if r.status_code != 200 or not r.json().get("typedb_connected"):
        pytest.skip("API not healthy")
    return True


class TestTasksList:
    def test_list_returns_200(self, client, api_healthy):
        r = client.get("/tasks?limit=5")
        assert r.status_code == 200

    def test_list_has_items(self, client, api_healthy):
        data = client.get("/tasks?limit=5").json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_respects_limit(self, client, api_healthy):
        data = client.get("/tasks?limit=2").json()
        assert len(data["items"]) <= 2

    def test_list_item_schema(self, client, api_healthy):
        data = client.get("/tasks?limit=1").json()
        if data["items"]:
            item = data["items"][0]
            assert "task_id" in item
            assert "status" in item

    def test_list_filter_by_status(self, client, api_healthy):
        r = client.get("/tasks?status=DONE&limit=3")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["status"] == "DONE"


class TestTaskGet:
    def _get_first_id(self, client):
        data = client.get("/tasks?limit=1").json()
        if not data["items"]:
            pytest.skip("No tasks in DB")
        return data["items"][0]["task_id"]

    def test_get_existing_task(self, client, api_healthy):
        tid = self._get_first_id(client)
        r = client.get(f"/tasks/{tid}")
        assert r.status_code == 200
        assert r.json()["task_id"] == tid

    def test_get_nonexistent_returns_404(self, client, api_healthy):
        r = client.get("/tasks/NONEXISTENT-TASK-XYZ")
        assert r.status_code == 404


class TestTaskLifecycle:
    def test_create_task(self, client, api_healthy):
        payload = {
            "task_id": "E2E-TEST-TASK-001",
            "description": "Integration test task",
            "priority": "LOW",
            "phase": "SESSION",
        }
        r = client.post("/tasks", json=payload)
        assert r.status_code in (200, 201)
        data = r.json()
        assert "task_id" in data

    def test_update_task(self, client, api_healthy):
        payload = {
            "task_id": "E2E-TEST-TASK-UPD",
            "description": "Task to update",
            "priority": "LOW",
            "phase": "SESSION",
        }
        client.post("/tasks", json=payload)
        r = client.put("/tasks/E2E-TEST-TASK-UPD", json={"status": "IN_PROGRESS"})
        assert r.status_code == 200

    def test_delete_task(self, client, api_healthy):
        payload = {
            "task_id": "E2E-TEST-TASK-DEL",
            "description": "Task to delete",
            "priority": "LOW",
            "phase": "SESSION",
        }
        client.post("/tasks", json=payload)
        r = client.delete("/tasks/E2E-TEST-TASK-DEL")
        assert r.status_code in (200, 204)


class TestTaskDetails:
    def _get_first_id(self, client):
        data = client.get("/tasks?limit=1").json()
        if not data["items"]:
            pytest.skip("No tasks in DB")
        return data["items"][0]["task_id"]

    def test_get_task_details(self, client, api_healthy):
        tid = self._get_first_id(client)
        r = client.get(f"/tasks/{tid}/details")
        assert r.status_code == 200

    def test_get_execution_events(self, client, api_healthy):
        tid = self._get_first_id(client)
        r = client.get(f"/tasks/{tid}/execution")
        assert r.status_code == 200


class TestTaskWorkflow:
    def test_available_tasks(self, client, api_healthy):
        r = client.get("/tasks/available")
        assert r.status_code == 200


# Cleanup created test tasks
@pytest.fixture(scope="module", autouse=True)
def cleanup(client, api_healthy):
    yield
    for tid in ["E2E-TEST-TASK-001", "E2E-TEST-TASK-UPD"]:
        client.delete(f"/tasks/{tid}")
