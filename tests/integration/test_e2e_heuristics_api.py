"""E2E-T2-006: Heuristic/CVP + Misc API Integration Tests (Tier 2).

Per TEST-E2E-01-v1 + EPIC-TESTING-E2E Phase 1.
Run: .venv/bin/python3 -m pytest tests/integration/test_e2e_heuristics_api.py -v
"""

import pytest
import httpx

BASE = "http://localhost:8082/api"
TIMEOUT = 15.0


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


# --- Health ---

class TestHealth:
    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "typedb_connected" in data
        assert "rules_count" in data

    def test_mcp_readiness(self, client, api_healthy):
        r = client.get("/mcp/readiness")
        assert r.status_code == 200


# --- CVP ---

class TestCVP:
    def test_cvp_status(self, client, api_healthy):
        r = client.get("/tests/cvp/status")
        assert r.status_code == 200

    def test_test_results_list(self, client, api_healthy):
        r = client.get("/tests/results")
        assert r.status_code == 200


# --- Evidence ---

class TestEvidence:
    def test_evidence_list(self, client, api_healthy):
        r = client.get("/evidence")
        assert r.status_code == 200

    def test_evidence_search(self, client, api_healthy):
        r = client.get("/evidence/search?query=session")
        assert r.status_code == 200


# --- Reports ---

class TestReports:
    def test_executive_report(self, client, api_healthy):
        r = client.get("/reports/executive")
        assert r.status_code == 200


# --- Metrics ---

class TestMetrics:
    def test_metrics_summary(self, client, api_healthy):
        r = client.get("/metrics/summary")
        assert r.status_code == 200


# --- Files ---

class TestFiles:
    def test_file_content_allowed(self, client, api_healthy):
        r = client.get("/files/content?path=docs/RULES-DIRECTIVES.md")
        assert r.status_code == 200

    def test_file_content_denied(self, client, api_healthy):
        r = client.get("/files/content?path=/etc/passwd")
        assert r.status_code == 403


# --- Audit ---

class TestAudit:
    def test_audit_list(self, client, api_healthy):
        r = client.get("/audit")
        assert r.status_code == 200

    def test_audit_summary(self, client, api_healthy):
        r = client.get("/audit/summary")
        assert r.status_code == 200


# --- Projects ---

class TestProjects:
    def test_projects_list(self, client, api_healthy):
        r = client.get("/projects")
        assert r.status_code == 200


# --- Infrastructure ---

class TestInfra:
    def test_containers_endpoint(self, client, api_healthy):
        r = client.get("/infra/containers")
        assert r.status_code == 200

    def test_logs_endpoint(self, client, api_healthy):
        r = client.get("/infra/logs")
        assert r.status_code == 200
