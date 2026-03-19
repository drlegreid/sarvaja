"""
Unit tests for the Event-Driven Ingestion Scheduler.

Per P2-10: Validates periodic scanning, manual triggers, configuration,
and graceful start/stop of the IngestionScheduler.

Created: 2026-03-19
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from governance.services.ingestion_scheduler import (
    IngestionScheduler,
    ScanResult,
    run_discovery_scan,
    get_scheduler,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


# ---------------------------------------------------------------------------
# ScanResult tests
# ---------------------------------------------------------------------------


class TestScanResult:
    def test_default_values(self):
        r = ScanResult()
        assert r.projects_created == 0
        assert r.sessions_ingested == 0
        assert r.errors == []
        assert r.duration_ms == 0.0

    def test_to_dict(self):
        r = ScanResult(
            projects_created=2,
            sessions_ingested=5,
            errors=["err1"],
            duration_ms=123.456,
            timestamp="2026-03-19T00:00:00Z",
        )
        d = r.to_dict()
        assert d["projects_created"] == 2
        assert d["sessions_ingested"] == 5
        assert d["errors"] == ["err1"]
        assert d["duration_ms"] == 123.5
        assert d["timestamp"] == "2026-03-19T00:00:00Z"

    def test_to_dict_truncates_errors(self):
        r = ScanResult(errors=[f"err-{i}" for i in range(20)])
        d = r.to_dict()
        assert len(d["errors"]) == 10


# ---------------------------------------------------------------------------
# run_discovery_scan tests
# ---------------------------------------------------------------------------


class TestRunDiscoveryScan:
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_no_projects_returns_empty_result(self, mock_discover):
        mock_discover.return_value = []
        result = run_discovery_scan()
        assert result.projects_created == 0
        assert result.sessions_ingested == 0
        assert result.errors == []
        assert result.duration_ms > 0

    @patch("governance.services.ingestion_scheduler.discover_filesystem_projects")
    @patch("governance.services.ingestion_scheduler.ingest_all")
    @patch("governance.services.ingestion_scheduler.get_project")
    @patch("governance.services.ingestion_scheduler.create_project")
    @patch("governance.services.ingestion_scheduler.detect_project_type")
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_discovers_and_ingests(
        self, mock_discover, mock_detect, mock_create, mock_get, mock_ingest, mock_fs
    ):
        mock_discover.return_value = [
            {
                "project_id": "PROJ-TEST",
                "name": "test-proj",
                "path": "/tmp/test",
                "cc_directory": "/tmp/cc",
            }
        ]
        mock_get.return_value = None  # Project doesn't exist yet
        mock_detect.return_value = "python"
        mock_ingest.return_value = [{"session_id": "SESSION-1"}, {"session_id": "SESSION-2"}]
        mock_fs.return_value = []

        result = run_discovery_scan()
        assert result.projects_created == 1
        assert result.sessions_ingested == 2
        mock_create.assert_called_once()
        mock_ingest.assert_called_once()

    @patch("governance.services.ingestion_scheduler.discover_filesystem_projects")
    @patch("governance.services.ingestion_scheduler.ingest_all")
    @patch("governance.services.ingestion_scheduler.get_project")
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_skips_existing_project(self, mock_discover, mock_get, mock_ingest, mock_fs):
        mock_discover.return_value = [
            {
                "project_id": "PROJ-EXISTS",
                "name": "existing",
                "path": "/tmp/test",
                "cc_directory": "/tmp/cc",
            }
        ]
        mock_get.return_value = {"project_id": "PROJ-EXISTS"}
        mock_ingest.return_value = []
        mock_fs.return_value = []

        result = run_discovery_scan()
        assert result.projects_created == 0

    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_handles_scan_exception(self, mock_discover):
        mock_discover.side_effect = RuntimeError("connection failed")
        result = run_discovery_scan()
        assert len(result.errors) == 1
        assert "RuntimeError" in result.errors[0]

    @patch("governance.services.ingestion_scheduler.discover_filesystem_projects")
    @patch("governance.services.ingestion_scheduler.ingest_all")
    @patch("governance.services.ingestion_scheduler.get_project")
    @patch("governance.services.ingestion_scheduler.discover_cc_projects")
    def test_ingest_error_captured_not_fatal(self, mock_discover, mock_get, mock_ingest, mock_fs):
        mock_discover.return_value = [
            {
                "project_id": "PROJ-ERR",
                "name": "err",
                "path": "/tmp",
                "cc_directory": "/tmp/cc",
            }
        ]
        mock_get.return_value = {"project_id": "PROJ-ERR"}
        mock_ingest.side_effect = OSError("disk full")
        mock_fs.return_value = []

        result = run_discovery_scan()
        assert len(result.errors) == 1
        assert "OSError" in result.errors[0]
        assert result.sessions_ingested == 0


# ---------------------------------------------------------------------------
# IngestionScheduler tests
# ---------------------------------------------------------------------------


class TestIngestionScheduler:
    def test_default_interval(self):
        s = IngestionScheduler()
        assert s.interval == DEFAULT_SCAN_INTERVAL

    def test_custom_interval(self):
        s = IngestionScheduler(interval_seconds=600)
        assert s.interval == 600

    def test_interval_enforces_minimum(self):
        s = IngestionScheduler(interval_seconds=5)
        assert s.interval == MIN_SCAN_INTERVAL

    def test_not_running_initially(self):
        s = IngestionScheduler()
        assert not s.is_running

    def test_configure_updates_interval(self):
        s = IngestionScheduler(interval_seconds=300)
        s.configure(120)
        assert s.interval == 120

    def test_configure_enforces_minimum(self):
        s = IngestionScheduler()
        s.configure(10)
        assert s.interval == MIN_SCAN_INTERVAL

    def test_get_status_initial(self):
        s = IngestionScheduler()
        status = s.get_status()
        assert status["running"] is False
        assert status["scan_count"] == 0
        assert status["total_sessions_ingested"] == 0
        assert status["total_projects_created"] == 0
        assert status["started_at"] is None
        assert status["last_scan"] is None

    @pytest.mark.asyncio
    @patch("governance.services.ingestion_scheduler.run_discovery_scan")
    async def test_start_and_stop(self, mock_scan):
        mock_scan.return_value = ScanResult(timestamp="2026-03-19T00:00:00Z")

        s = IngestionScheduler(interval_seconds=MIN_SCAN_INTERVAL)
        s.start()

        assert s.is_running
        assert s._started_at is not None

        # Wait for the first scan to complete
        await asyncio.sleep(0.2)
        assert s._scan_count >= 1

        await s.stop()
        assert not s.is_running

    @pytest.mark.asyncio
    @patch("governance.services.ingestion_scheduler.run_discovery_scan")
    async def test_trigger_scan(self, mock_scan):
        mock_scan.return_value = ScanResult(
            sessions_ingested=3,
            timestamp="2026-03-19T00:00:00Z",
        )

        s = IngestionScheduler(interval_seconds=MIN_SCAN_INTERVAL)
        s.start()
        await asyncio.sleep(0.1)

        initial_count = s._scan_count
        result = await s.trigger_scan()

        assert result.sessions_ingested == 3
        assert s._scan_count == initial_count + 1
        assert s._total_sessions_ingested >= 3

        await s.stop()

    @pytest.mark.asyncio
    @patch("governance.services.ingestion_scheduler.run_discovery_scan")
    async def test_stats_accumulate(self, mock_scan):
        call_count = 0

        def make_result():
            nonlocal call_count
            call_count += 1
            return ScanResult(
                projects_created=1,
                sessions_ingested=2,
                timestamp=f"scan-{call_count}",
            )

        mock_scan.side_effect = lambda: make_result()

        s = IngestionScheduler(interval_seconds=MIN_SCAN_INTERVAL)
        s.start()
        await asyncio.sleep(0.1)

        # Trigger extra scans
        await s.trigger_scan()
        await s.trigger_scan()

        status = s.get_status()
        assert status["scan_count"] >= 3
        assert status["total_sessions_ingested"] >= 6
        assert status["total_projects_created"] >= 3
        assert status["last_scan"] is not None

        await s.stop()

    @pytest.mark.asyncio
    async def test_start_twice_is_noop(self):
        s = IngestionScheduler(interval_seconds=MIN_SCAN_INTERVAL)

        with patch("governance.services.ingestion_scheduler.run_discovery_scan") as mock_scan:
            mock_scan.return_value = ScanResult(timestamp="t")
            s.start()
            task1 = s._task
            s.start()
            assert s._task is task1  # Same task, not replaced

            await s.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_running_is_noop(self):
        s = IngestionScheduler()
        await s.stop()
        assert not s.is_running


# ---------------------------------------------------------------------------
# Singleton tests
# ---------------------------------------------------------------------------


class TestGetScheduler:
    def test_returns_same_instance(self):
        import governance.services.ingestion_scheduler as mod

        mod._scheduler = None  # Reset
        s1 = get_scheduler()
        s2 = get_scheduler()
        assert s1 is s2
        mod._scheduler = None  # Cleanup


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------


class TestIngestionRoutes:
    """Tests for the /api/ingestion/* endpoints."""

    def _get_client(self):
        from fastapi.testclient import TestClient
        from governance.routes.ingestion import router
        from fastapi import FastAPI

        test_app = FastAPI()
        test_app.include_router(router, prefix="/api")
        return TestClient(test_app)

    @patch("governance.services.ingestion_scheduler.get_scheduler")
    def test_get_scheduler_status(self, mock_get):
        mock_sched = MagicMock()
        mock_sched.get_status.return_value = {
            "running": True,
            "interval_seconds": 300,
            "scan_count": 5,
            "total_sessions_ingested": 10,
            "total_projects_created": 2,
            "started_at": "2026-03-19T00:00:00Z",
            "last_scan": None,
        }
        mock_get.return_value = mock_sched

        client = self._get_client()
        resp = client.get("/api/ingestion/scheduler")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is True
        assert data["scan_count"] == 5

    @patch("governance.services.ingestion_scheduler.get_scheduler")
    def test_configure_scheduler(self, mock_get):
        mock_sched = MagicMock()
        mock_sched.interval = 120
        mock_get.return_value = mock_sched

        client = self._get_client()
        resp = client.put("/api/ingestion/scheduler", json={"interval_seconds": 120})
        assert resp.status_code == 200
        mock_sched.configure.assert_called_once_with(120)

    @patch("governance.services.ingestion_scheduler.get_scheduler")
    def test_configure_rejects_too_small(self, mock_get):
        client = self._get_client()
        resp = client.put("/api/ingestion/scheduler", json={"interval_seconds": 5})
        assert resp.status_code == 422  # Pydantic validation

    @patch("governance.services.ingestion_scheduler.get_scheduler")
    def test_trigger_scan_when_not_running(self, mock_get):
        mock_sched = MagicMock()
        mock_sched.is_running = False
        mock_get.return_value = mock_sched

        client = self._get_client()
        resp = client.post("/api/ingestion/scan")
        assert resp.status_code == 503

    @patch("governance.services.ingestion_scheduler.get_scheduler")
    def test_trigger_scan_success(self, mock_get):
        mock_sched = MagicMock()
        mock_sched.is_running = True

        async def fake_trigger():
            return ScanResult(
                sessions_ingested=2,
                projects_created=1,
                timestamp="2026-03-19T00:00:00Z",
                duration_ms=150.0,
            )

        mock_sched.trigger_scan = fake_trigger
        mock_get.return_value = mock_sched

        client = self._get_client()
        resp = client.post("/api/ingestion/scan")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["result"]["sessions_ingested"] == 2
        assert data["result"]["projects_created"] == 1


# ---------------------------------------------------------------------------
# api_startup.py backward compatibility
# ---------------------------------------------------------------------------


class TestApiStartupSchedulerIntegration:
    """Verify api_startup.discover_cc_sessions() delegates to scheduler."""

    @pytest.mark.asyncio
    @patch("governance.services.ingestion_scheduler.get_scheduler")
    async def test_startup_starts_scheduler(self, mock_get):
        mock_sched = MagicMock()
        mock_get.return_value = mock_sched

        from governance.api_startup import discover_cc_sessions

        await discover_cc_sessions()
        mock_sched.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("governance.services.ingestion_scheduler.run_discovery_scan")
    @patch("governance.services.ingestion_scheduler.get_scheduler")
    async def test_startup_fallback_on_scheduler_failure(self, mock_get, mock_scan):
        mock_sched = MagicMock()
        mock_sched.start.side_effect = RuntimeError("loop not running")
        mock_get.return_value = mock_sched
        mock_scan.return_value = ScanResult(timestamp="t")

        from governance.api_startup import discover_cc_sessions

        # Should not raise — falls back to one-shot
        await discover_cc_sessions()
