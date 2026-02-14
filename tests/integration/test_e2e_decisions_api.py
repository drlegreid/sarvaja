"""E2E-T2-005: Decision API Integration Tests (Tier 2).

Per TEST-E2E-01-v1 + EPIC-TESTING-E2E Phase 1.
Run: .venv/bin/python3 -m pytest tests/integration/test_e2e_decisions_api.py -v
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


class TestDecisionsList:
    def test_list_returns_200(self, client, api_healthy):
        r = client.get("/decisions?limit=5")
        assert r.status_code == 200

    def test_list_has_items(self, client, api_healthy):
        data = client.get("/decisions?limit=5").json()
        assert "items" in data

    def test_decision_schema(self, client, api_healthy):
        data = client.get("/decisions?limit=1").json()
        if data["items"]:
            d = data["items"][0]
            assert "id" in d
            assert "name" in d
            assert "context" in d
            assert "rationale" in d


class TestDecisionGet:
    def _get_first_id(self, client):
        data = client.get("/decisions?limit=1").json()
        if not data["items"]:
            pytest.skip("No decisions in DB")
        return data["items"][0]["id"]

    def test_get_existing_decision(self, client, api_healthy):
        did = self._get_first_id(client)
        r = client.get(f"/decisions/{did}")
        assert r.status_code == 200
        assert r.json()["id"] == did


class TestDecisionLifecycle:
    def test_create_decision(self, client, api_healthy):
        payload = {
            "decision_id": "E2E-DECISION-001",
            "name": "E2E Test Decision",
            "context": "Integration test",
            "rationale": "Automated verification",
        }
        r = client.post("/decisions", json=payload)
        assert r.status_code in (200, 201)

    def test_delete_decision(self, client, api_healthy):
        r = client.delete("/decisions/E2E-DECISION-001")
        assert r.status_code in (200, 204)
