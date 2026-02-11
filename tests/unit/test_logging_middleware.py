"""Tests for governance logging middleware (L1 access, L2 events, L3 dashboard).

Verifies structured JSON output, field presence, and filtering behavior.

Created: 2026-02-11
"""
import json
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── L1: Access Log Middleware ──────────────────────────────────────────

class TestAccessLogMiddleware:
    """Tests for AccessLogMiddleware structured access logging."""

    @pytest.fixture
    def middleware(self):
        from governance.middleware.access_log import AccessLogMiddleware
        app = MagicMock()
        return AccessLogMiddleware(app)

    @pytest.mark.asyncio
    async def test_logs_request_as_json(self, middleware, caplog):
        """Access log entry should be valid JSON with required fields."""
        request = MagicMock()
        request.url.path = "/api/sessions"
        request.url.query = ""
        request.method = "GET"
        request.headers = {}

        response = MagicMock()
        response.status_code = 200
        response.headers = {"content-length": "512"}

        call_next = AsyncMock(return_value=response)

        with caplog.at_level(logging.INFO, logger="governance.access"):
            await middleware.dispatch(request, call_next)

        assert len(caplog.records) >= 1
        entry = json.loads(caplog.records[-1].message)
        assert entry["method"] == "GET"
        assert entry["path"] == "/api/sessions"
        assert entry["status"] == 200
        assert "ms" in entry
        assert entry["bytes"] == "512"

    @pytest.mark.asyncio
    async def test_skips_health_endpoint(self, middleware, caplog):
        """Health endpoint should not be logged."""
        request = MagicMock()
        request.url.path = "/api/health"
        request.method = "GET"

        response = MagicMock()
        response.status_code = 200

        call_next = AsyncMock(return_value=response)

        with caplog.at_level(logging.INFO, logger="governance.access"):
            result = await middleware.dispatch(request, call_next)

        assert result == response
        access_records = [r for r in caplog.records if r.name == "governance.access"]
        assert len(access_records) == 0

    @pytest.mark.asyncio
    async def test_skips_docs_endpoint(self, middleware, caplog):
        """Docs endpoint should not be logged."""
        request = MagicMock()
        request.url.path = "/api/docs"
        request.method = "GET"

        response = MagicMock()
        response.status_code = 200

        call_next = AsyncMock(return_value=response)

        with caplog.at_level(logging.INFO, logger="governance.access"):
            await middleware.dispatch(request, call_next)

        access_records = [r for r in caplog.records if r.name == "governance.access"]
        assert len(access_records) == 0

    @pytest.mark.asyncio
    async def test_logs_error_status(self, middleware, caplog):
        """5xx responses should still be logged."""
        request = MagicMock()
        request.url.path = "/api/tasks"
        request.url.query = ""
        request.method = "POST"
        request.headers = {}

        response = MagicMock()
        response.status_code = 500
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        with caplog.at_level(logging.INFO, logger="governance.access"):
            await middleware.dispatch(request, call_next)

        assert len(caplog.records) >= 1
        entry = json.loads(caplog.records[-1].message)
        assert entry["status"] == 500

    @pytest.mark.asyncio
    async def test_debug_mode_adds_query(self, middleware, caplog):
        """With LOG_LEVEL=DEBUG, query string should appear in log."""
        request = MagicMock()
        request.url.path = "/api/sessions"
        request.url.query = "status=ACTIVE&limit=10"
        request.method = "GET"
        request.headers = {"content-length": "0"}

        response = MagicMock()
        response.status_code = 200
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        with patch("governance.middleware.access_log._DEBUG", True):
            with caplog.at_level(logging.INFO, logger="governance.access"):
                await middleware.dispatch(request, call_next)

        entry = json.loads(caplog.records[-1].message)
        assert entry.get("query") == "status=ACTIVE&limit=10"

    @pytest.mark.asyncio
    async def test_duration_is_positive(self, middleware, caplog):
        """Duration should be a positive number."""
        request = MagicMock()
        request.url.path = "/api/rules"
        request.url.query = ""
        request.method = "GET"
        request.headers = {}

        response = MagicMock()
        response.status_code = 200
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        with caplog.at_level(logging.INFO, logger="governance.access"):
            await middleware.dispatch(request, call_next)

        entry = json.loads(caplog.records[-1].message)
        assert entry["ms"] >= 0


# ── L2: Event Log ─────────────────────────────────────────────────────

class TestEventLog:
    """Tests for business event logging."""

    def test_log_event_emits_json(self, caplog):
        """log_event should emit valid JSON with entity and action."""
        from governance.middleware.event_log import log_event

        with caplog.at_level(logging.INFO, logger="governance.events"):
            log_event("session", "create", session_id="SESSION-2026-02-11-TEST")

        assert len(caplog.records) >= 1
        entry = json.loads(caplog.records[-1].message)
        assert entry["entity"] == "session"
        assert entry["action"] == "create"
        assert entry["session_id"] == "SESSION-2026-02-11-TEST"
        assert "ts" in entry

    def test_log_event_includes_extra_fields(self, caplog):
        """Extra kwargs should appear in the log entry."""
        from governance.middleware.event_log import log_event

        with caplog.at_level(logging.INFO, logger="governance.events"):
            log_event("task", "update", task_id="TASK-001", old_status="OPEN", status="DONE")

        entry = json.loads(caplog.records[-1].message)
        assert entry["task_id"] == "TASK-001"
        assert entry["old_status"] == "OPEN"
        assert entry["status"] == "DONE"

    def test_log_event_for_rules(self, caplog):
        """Rule events should include rule-specific fields."""
        from governance.middleware.event_log import log_event

        with caplog.at_level(logging.INFO, logger="governance.events"):
            log_event("rule", "delete", rule_id="TEST-RULE-01", archive=True)

        entry = json.loads(caplog.records[-1].message)
        assert entry["entity"] == "rule"
        assert entry["action"] == "delete"
        assert entry["archive"] is True


# ── L3: Dashboard Action Log ──────────────────────────────────────────

class TestDashboardLog:
    """Tests for dashboard UI action logging."""

    def test_log_action_emits_json(self, caplog):
        """log_action should emit valid JSON with view and action."""
        from governance.middleware.dashboard_log import log_action

        with caplog.at_level(logging.INFO, logger="governance.dashboard"):
            log_action("sessions", "select", session_id="SESSION-2026-02-11-TEST")

        assert len(caplog.records) >= 1
        entry = json.loads(caplog.records[-1].message)
        assert entry["view"] == "sessions"
        assert entry["action"] == "select"
        assert entry["session_id"] == "SESSION-2026-02-11-TEST"

    def test_log_action_filter(self, caplog):
        """Filter actions should include filter values."""
        from governance.middleware.dashboard_log import log_action

        with caplog.at_level(logging.INFO, logger="governance.dashboard"):
            log_action("sessions", "filter", status="COMPLETED", agent="code-agent")

        entry = json.loads(caplog.records[-1].message)
        assert entry["status"] == "COMPLETED"
        assert entry["agent"] == "code-agent"

    def test_log_action_delete(self, caplog):
        """Delete actions should log correctly."""
        from governance.middleware.dashboard_log import log_action

        with caplog.at_level(logging.INFO, logger="governance.dashboard"):
            log_action("sessions", "delete", session_id="SESSION-X")

        entry = json.loads(caplog.records[-1].message)
        assert entry["action"] == "delete"
