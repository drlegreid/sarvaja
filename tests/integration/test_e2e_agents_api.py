"""E2E-T2-004: Agent API Integration Tests (Tier 2).

Per TEST-E2E-01-v1 + EPIC-TESTING-E2E Phase 1.
Run: .venv/bin/python3 -m pytest tests/integration/test_e2e_agents_api.py -v
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


class TestAgentsList:
    def test_list_returns_200(self, client, api_healthy):
        r = client.get("/agents?limit=5")
        assert r.status_code == 200

    def test_list_has_items(self, client, api_healthy):
        data = client.get("/agents?limit=5").json()
        assert "items" in data
        assert len(data["items"]) > 0

    def test_agent_schema(self, client, api_healthy):
        data = client.get("/agents?limit=1").json()
        agent = data["items"][0]
        assert "agent_id" in agent
        assert "name" in agent
        assert "status" in agent
        assert "trust_score" in agent


class TestAgentGet:
    def _get_first_id(self, client):
        data = client.get("/agents?limit=1").json()
        if not data["items"]:
            pytest.skip("No agents in DB")
        return data["items"][0]["agent_id"]

    def test_get_existing_agent(self, client, api_healthy):
        aid = self._get_first_id(client)
        r = client.get(f"/agents/{aid}")
        assert r.status_code == 200
        assert r.json()["agent_id"] == aid

    def test_agent_has_trust_score(self, client, api_healthy):
        aid = self._get_first_id(client)
        data = client.get(f"/agents/{aid}").json()
        assert isinstance(data["trust_score"], (int, float))
        assert 0 <= data["trust_score"] <= 1.0

    def test_agent_has_sessions(self, client, api_healthy):
        aid = self._get_first_id(client)
        r = client.get(f"/agents/{aid}/sessions")
        assert r.status_code == 200


class TestAgentObservability:
    def test_status_summary(self, client, api_healthy):
        r = client.get("/agents/status/summary")
        assert r.status_code == 200

    def test_stuck_agents(self, client, api_healthy):
        r = client.get("/agents/status/stuck")
        assert r.status_code == 200

    def test_stale_locks(self, client, api_healthy):
        r = client.get("/agents/status/locks")
        assert r.status_code == 200
