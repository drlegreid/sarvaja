"""E2E-T2-003: Rule API Integration Tests (Tier 2).

Per TEST-E2E-01-v1 + EPIC-TESTING-E2E Phase 1.
Run: .venv/bin/python3 -m pytest tests/integration/test_e2e_rules_api.py -v
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


class TestRulesList:
    def test_list_returns_200(self, client, api_healthy):
        r = client.get("/rules?limit=5")
        assert r.status_code == 200

    def test_list_has_items(self, client, api_healthy):
        data = client.get("/rules?limit=5").json()
        assert "items" in data
        assert len(data["items"]) > 0

    def test_list_respects_limit(self, client, api_healthy):
        data = client.get("/rules?limit=3").json()
        assert len(data["items"]) <= 3

    def test_list_item_schema(self, client, api_healthy):
        data = client.get("/rules?limit=1").json()
        item = data["items"][0]
        assert "id" in item
        assert "name" in item
        assert "priority" in item
        assert "status" in item

    def test_list_filter_by_status(self, client, api_healthy):
        r = client.get("/rules?status=ACTIVE&limit=3")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["status"] == "ACTIVE"

    def test_list_filter_by_priority(self, client, api_healthy):
        r = client.get("/rules?priority=CRITICAL&limit=3")
        assert r.status_code == 200


class TestRuleGet:
    def test_get_known_rule(self, client, api_healthy):
        r = client.get("/rules/SESSION-EVID-01-v1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "SESSION-EVID-01-v1"
        assert data["status"] == "ACTIVE"

    def test_get_nonexistent_returns_404(self, client, api_healthy):
        r = client.get("/rules/NONEXISTENT-RULE-XYZ")
        assert r.status_code == 404

    def test_get_rule_has_directive(self, client, api_healthy):
        r = client.get("/rules/SESSION-EVID-01-v1")
        data = r.json()
        assert "directive" in data


class TestRuleDependencies:
    def test_dependencies_overview(self, client, api_healthy):
        r = client.get("/rules/dependencies/overview")
        assert r.status_code == 200

    def test_rule_dependencies(self, client, api_healthy):
        r = client.get("/rules/SESSION-EVID-01-v1/dependencies")
        assert r.status_code == 200

    def test_rule_tasks(self, client, api_healthy):
        r = client.get("/rules/TEST-E2E-01-v1/tasks")
        assert r.status_code == 200
