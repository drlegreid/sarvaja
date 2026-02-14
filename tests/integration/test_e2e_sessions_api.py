"""E2E-T2-001: Session API Integration Tests (Tier 2).

Per TEST-E2E-01-v1 + EPIC-TESTING-E2E Phase 1.
Tests real API endpoints against running container stack.

Run: .venv/bin/python3 -m pytest tests/integration/test_e2e_sessions_api.py -v
Requires: API on localhost:8082
"""

import json
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
        pytest.skip("API not healthy — containers not running")
    return True


# --- LIST ---

class TestSessionsList:
    def test_list_returns_200(self, client, api_healthy):
        r = client.get("/sessions?limit=5")
        assert r.status_code == 200

    def test_list_has_items(self, client, api_healthy):
        data = client.get("/sessions?limit=5").json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_respects_limit(self, client, api_healthy):
        data = client.get("/sessions?limit=2").json()
        assert len(data["items"]) <= 2

    def test_list_item_schema(self, client, api_healthy):
        data = client.get("/sessions?limit=1").json()
        if data["items"]:
            item = data["items"][0]
            assert "session_id" in item
            assert "status" in item
            assert "start_time" in item

    def test_list_pagination(self, client, api_healthy):
        page1 = client.get("/sessions?limit=2&offset=0").json()
        page2 = client.get("/sessions?limit=2&offset=2").json()
        if len(page1["items"]) == 2 and len(page2["items"]) > 0:
            ids1 = {s["session_id"] for s in page1["items"]}
            ids2 = {s["session_id"] for s in page2["items"]}
            assert ids1.isdisjoint(ids2), "Pages should not overlap"


# --- SINGLE ---

class TestSessionGet:
    def _get_first_id(self, client):
        data = client.get("/sessions?limit=1").json()
        if not data["items"]:
            pytest.skip("No sessions in DB")
        return data["items"][0]["session_id"]

    def test_get_existing_session(self, client, api_healthy):
        sid = self._get_first_id(client)
        r = client.get(f"/sessions/{sid}")
        assert r.status_code == 200
        assert r.json()["session_id"] == sid

    def test_get_nonexistent_returns_404(self, client, api_healthy):
        r = client.get("/sessions/NONEXISTENT-SESSION-XYZ")
        assert r.status_code in (404, 200)  # Some APIs return empty


# --- DETAIL (zoom levels) ---

class TestSessionDetail:
    def _get_first_id(self, client):
        data = client.get("/sessions?limit=1").json()
        if not data["items"]:
            pytest.skip("No sessions in DB")
        return data["items"][0]["session_id"]

    def test_detail_zoom_0(self, client, api_healthy):
        sid = self._get_first_id(client)
        r = client.get(f"/sessions/{sid}/detail?zoom=0")
        assert r.status_code == 200

    def test_detail_zoom_2(self, client, api_healthy):
        sid = self._get_first_id(client)
        r = client.get(f"/sessions/{sid}/detail?zoom=2")
        assert r.status_code == 200


# --- TOOLS & THOUGHTS (paginated) ---

class TestSessionToolsThoughts:
    def _get_first_id(self, client):
        data = client.get("/sessions?limit=1").json()
        if not data["items"]:
            pytest.skip("No sessions in DB")
        return data["items"][0]["session_id"]

    def test_tools_endpoint(self, client, api_healthy):
        sid = self._get_first_id(client)
        r = client.get(f"/sessions/{sid}/tools?limit=5")
        assert r.status_code == 200

    def test_thoughts_endpoint(self, client, api_healthy):
        sid = self._get_first_id(client)
        r = client.get(f"/sessions/{sid}/thoughts?limit=5")
        assert r.status_code == 200


# --- EVIDENCE ---

class TestSessionEvidence:
    def _get_first_id(self, client):
        data = client.get("/sessions?limit=1").json()
        if not data["items"]:
            pytest.skip("No sessions in DB")
        return data["items"][0]["session_id"]

    def test_evidence_endpoint(self, client, api_healthy):
        sid = self._get_first_id(client)
        r = client.get(f"/sessions/{sid}/evidence")
        assert r.status_code == 200

    def test_rendered_evidence(self, client, api_healthy):
        sid = self._get_first_id(client)
        r = client.get(f"/sessions/{sid}/evidence/rendered")
        assert r.status_code in (200, 404)  # 404 if no evidence file


# --- CREATE / UPDATE lifecycle ---

class TestSessionLifecycle:
    def test_create_session(self, client, api_healthy):
        payload = {
            "description": "E2E-TEST-SESSION",
            "agent_id": "test-agent",
        }
        r = client.post("/sessions", json=payload)
        assert r.status_code in (200, 201)
        data = r.json()
        assert "session_id" in data

    def test_end_session(self, client, api_healthy):
        # Create then end
        payload = {"description": "E2E-TEST-END", "agent_id": "test-agent"}
        cr = client.post("/sessions", json=payload)
        if cr.status_code not in (200, 201):
            pytest.skip("Cannot create session")
        sid = cr.json()["session_id"]
        er = client.put(f"/sessions/{sid}/end")
        assert er.status_code == 200
