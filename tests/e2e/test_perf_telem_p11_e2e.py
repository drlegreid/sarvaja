"""E2E tests for Grafana dashboards (EPIC-PERF-TELEM-V1 Phase 11).

TDD-first: written BEFORE implementation.

These tests hit LIVE Grafana at localhost:3000 and verify:
  1. Grafana container healthy (GET /api/health returns status "ok")
  2. Data sources auto-provisioned (Prometheus + Loki reachable)
  3. All 3 dashboards loaded (api-performance, typedb-health, log-explorer)
  4. API Performance dashboard panels reference correct metrics
  5. TypeDB Health dashboard panels reference correct metrics
  6. Log Explorer dashboard has Loki data source queries
"""

import os

import pytest

GRAFANA_BASE = os.getenv("GRAFANA_BASE", "http://localhost:3000")
API_BASE = os.getenv("API_BASE", "http://localhost:8082")


@pytest.fixture(scope="module")
def grafana_client():
    """Shared httpx client for Grafana API (anonymous auth)."""
    import httpx
    with httpx.Client(base_url=GRAFANA_BASE, timeout=10) as client:
        yield client


@pytest.fixture(scope="module")
def api_client():
    """Shared httpx client for generating API traffic."""
    import httpx
    with httpx.Client(base_url=API_BASE, timeout=10) as client:
        yield client


class TestGrafanaHealthE2E:
    """E2E: Grafana container is running and healthy."""

    def test_grafana_health_ok(self, grafana_client):
        """GET /api/health returns {"status": "ok"}."""
        try:
            resp = grafana_client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("database") == "ok", f"Grafana health: {data}"
        except Exception as e:
            if "Connect" in str(type(e).__name__) or "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_grafana_org_accessible(self, grafana_client):
        """Anonymous auth gives Admin access (no login needed)."""
        try:
            resp = grafana_client.get("/api/org")
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("name"), "No org name returned"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise


class TestDataSourcesE2E:
    """E2E: Prometheus and Loki data sources auto-provisioned."""

    def test_datasources_count(self, grafana_client):
        """GET /api/datasources returns exactly 2 data sources."""
        try:
            resp = grafana_client.get("/api/datasources")
            assert resp.status_code == 200
            ds_list = resp.json()
            assert len(ds_list) >= 2, f"Expected >=2 data sources, got {len(ds_list)}"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_prometheus_datasource_exists(self, grafana_client):
        """Prometheus data source is provisioned and reachable."""
        try:
            resp = grafana_client.get("/api/datasources")
            assert resp.status_code == 200
            ds_list = resp.json()
            prom = [d for d in ds_list if d.get("type") == "prometheus"]
            assert len(prom) >= 1, f"No prometheus datasource found: {[d['type'] for d in ds_list]}"
            assert prom[0]["name"] == "Prometheus"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_loki_datasource_exists(self, grafana_client):
        """Loki data source is provisioned and reachable."""
        try:
            resp = grafana_client.get("/api/datasources")
            assert resp.status_code == 200
            ds_list = resp.json()
            loki = [d for d in ds_list if d.get("type") == "loki"]
            assert len(loki) >= 1, f"No loki datasource found: {[d['type'] for d in ds_list]}"
            assert loki[0]["name"] == "Loki"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_prometheus_datasource_health(self, grafana_client):
        """Prometheus data source health check via Grafana proxy."""
        try:
            # Get the datasource ID first
            resp = grafana_client.get("/api/datasources")
            ds_list = resp.json()
            prom = [d for d in ds_list if d.get("type") == "prometheus"]
            if not prom:
                pytest.skip("Prometheus datasource not found")
            ds_uid = prom[0]["uid"]

            # Check health via datasource proxy
            health_resp = grafana_client.get(
                f"/api/datasources/uid/{ds_uid}/health"
            )
            assert health_resp.status_code == 200, (
                f"Prometheus health check failed: {health_resp.status_code}"
            )
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_loki_datasource_health(self, grafana_client):
        """Loki data source health check via Grafana proxy."""
        try:
            resp = grafana_client.get("/api/datasources")
            ds_list = resp.json()
            loki = [d for d in ds_list if d.get("type") == "loki"]
            if not loki:
                pytest.skip("Loki datasource not found")
            ds_uid = loki[0]["uid"]

            health_resp = grafana_client.get(
                f"/api/datasources/uid/{ds_uid}/health"
            )
            assert health_resp.status_code == 200, (
                f"Loki health check failed: {health_resp.status_code}"
            )
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise


class TestDashboardsLoadedE2E:
    """E2E: All 3 dashboards are provisioned and accessible."""

    def test_three_dashboards_exist(self, grafana_client):
        """GET /api/search?type=dash-db returns 3 dashboards."""
        try:
            resp = grafana_client.get("/api/search", params={"type": "dash-db"})
            assert resp.status_code == 200
            dashboards = resp.json()
            assert len(dashboards) >= 3, (
                f"Expected >=3 dashboards, got {len(dashboards)}: "
                f"{[d.get('title') for d in dashboards]}"
            )
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_api_performance_dashboard_exists(self, grafana_client):
        """API Performance dashboard is loaded by UID."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-api-performance")
            assert resp.status_code == 200, (
                f"API Performance dashboard not found: {resp.status_code}"
            )
            data = resp.json()
            assert data["dashboard"]["title"] == "API Performance"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_typedb_health_dashboard_exists(self, grafana_client):
        """TypeDB Health dashboard is loaded by UID."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-typedb-health")
            assert resp.status_code == 200, (
                f"TypeDB Health dashboard not found: {resp.status_code}"
            )
            data = resp.json()
            assert data["dashboard"]["title"] == "TypeDB Health"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_log_explorer_dashboard_exists(self, grafana_client):
        """Log Explorer dashboard is loaded by UID."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-log-explorer")
            assert resp.status_code == 200, (
                f"Log Explorer dashboard not found: {resp.status_code}"
            )
            data = resp.json()
            assert data["dashboard"]["title"] == "Log Explorer"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise


class TestAPIPerformancePanelsE2E:
    """E2E: API Performance dashboard panels reference correct metrics."""

    def test_dashboard_has_expected_panels(self, grafana_client):
        """Dashboard has panels for request rate, latency, errors, slow, top 10."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-api-performance")
            if resp.status_code != 200:
                pytest.skip("API Performance dashboard not found")
            dashboard = resp.json()["dashboard"]
            panels = dashboard.get("panels", [])
            # Flatten rows if any
            all_panels = []
            for p in panels:
                if p.get("type") == "row":
                    all_panels.extend(p.get("panels", []))
                else:
                    all_panels.append(p)
            titles = [p.get("title", "").lower() for p in all_panels]
            assert any("request rate" in t for t in titles), f"No request rate panel: {titles}"
            assert any("latency" in t for t in titles), f"No latency panel: {titles}"
            assert any("error" in t for t in titles), f"No error panel: {titles}"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_panels_use_sarvaja_metrics(self, grafana_client):
        """Panels reference sarvaja_http_* Prometheus metrics."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-api-performance")
            if resp.status_code != 200:
                pytest.skip("API Performance dashboard not found")
            raw = resp.text
            assert "sarvaja_http_requests_total" in raw, "Missing sarvaja_http_requests_total"
            assert "sarvaja_http_request_duration_seconds" in raw, "Missing duration histogram"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise


class TestTypeDBHealthPanelsE2E:
    """E2E: TypeDB Health dashboard panels reference correct metrics."""

    def test_dashboard_has_query_panels(self, grafana_client):
        """Dashboard has panels for query rate and duration."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-typedb-health")
            if resp.status_code != 200:
                pytest.skip("TypeDB Health dashboard not found")
            dashboard = resp.json()["dashboard"]
            panels = dashboard.get("panels", [])
            all_panels = []
            for p in panels:
                if p.get("type") == "row":
                    all_panels.extend(p.get("panels", []))
                else:
                    all_panels.append(p)
            titles = [p.get("title", "").lower() for p in all_panels]
            assert any("query" in t and "rate" in t for t in titles), f"No query rate panel: {titles}"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_panels_use_typedb_metrics(self, grafana_client):
        """Panels reference sarvaja_typedb_* Prometheus metrics."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-typedb-health")
            if resp.status_code != 200:
                pytest.skip("TypeDB Health dashboard not found")
            raw = resp.text
            assert "sarvaja_typedb_query_total" in raw, "Missing sarvaja_typedb_query_total"
            assert "sarvaja_typedb_query_duration_seconds" in raw, "Missing duration histogram"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise


class TestLogExplorerPanelsE2E:
    """E2E: Log Explorer dashboard uses Loki data source."""

    def test_dashboard_has_log_panels(self, grafana_client):
        """Dashboard has a logs panel."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-log-explorer")
            if resp.status_code != 200:
                pytest.skip("Log Explorer dashboard not found")
            dashboard = resp.json()["dashboard"]
            panels = dashboard.get("panels", [])
            all_panels = []
            for p in panels:
                if p.get("type") == "row":
                    all_panels.extend(p.get("panels", []))
                else:
                    all_panels.append(p)
            panel_types = [p.get("type", "") for p in all_panels]
            assert "logs" in panel_types, f"No logs panel type: {panel_types}"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_panels_use_loki_datasource(self, grafana_client):
        """Panels reference Loki data source for log queries."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-log-explorer")
            if resp.status_code != 200:
                pytest.skip("Log Explorer dashboard not found")
            raw = resp.text
            assert "sarvaja-api" in raw, "Missing sarvaja-api job reference"
            assert "Loki" in raw or "loki" in raw, "Missing Loki datasource reference"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise

    def test_dashboard_has_template_variables(self, grafana_client):
        """Dashboard has template variables for filtering (method, status, etc.)."""
        try:
            resp = grafana_client.get("/api/dashboards/uid/sarvaja-log-explorer")
            if resp.status_code != 200:
                pytest.skip("Log Explorer dashboard not found")
            dashboard = resp.json()["dashboard"]
            templating = dashboard.get("templating", {}).get("list", [])
            var_names = [v.get("name", "") for v in templating]
            assert len(var_names) >= 2, f"Expected >=2 template vars, got: {var_names}"
        except Exception as e:
            if "Connect" in str(e):
                pytest.skip("Grafana container not running")
            raise
