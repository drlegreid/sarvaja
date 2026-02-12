"""
Unit tests for Playwright API Fallback Checks.

Per DOC-SIZE-01-v1: Tests for routes/tests/playwright_api_fallback.py module.
Tests: run_api_fallback, _check_dashboard_reachable, _check_screen_api,
       _check_chat_api, check_api_data_integrity.
"""

from unittest.mock import patch, MagicMock

import pytest

_P = "governance.routes.tests.playwright_api_fallback"


# ── _check_dashboard_reachable ───────────────────────────────────


class TestCheckDashboardReachable:
    def test_pass(self):
        from governance.routes.tests.playwright_api_fallback import _check_dashboard_reachable
        resp = MagicMock()
        resp.status_code = 200
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = _check_dashboard_reachable("http://localhost:8081")
        assert result["status"] == "PASS"
        assert result["id"] == "PW-DASH-001"

    def test_fail_status_code(self):
        from governance.routes.tests.playwright_api_fallback import _check_dashboard_reachable
        resp = MagicMock()
        resp.status_code = 500
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = _check_dashboard_reachable("http://localhost:8081")
        assert result["status"] == "FAIL"

    def test_exception(self):
        from governance.routes.tests.playwright_api_fallback import _check_dashboard_reachable
        with patch(f"{_P}.httpx.get", side_effect=Exception("timeout")):
            result = _check_dashboard_reachable("http://localhost:8081")
        assert result["status"] == "FAIL"

    def test_redirect_pass(self):
        from governance.routes.tests.playwright_api_fallback import _check_dashboard_reachable
        resp = MagicMock()
        resp.status_code = 302
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = _check_dashboard_reachable("http://localhost:8081")
        assert result["status"] == "PASS"


# ── _check_screen_api ────────────────────────────────────────────


class TestCheckScreenApi:
    def test_rules_pass(self):
        from governance.routes.tests.playwright_api_fallback import _check_screen_api
        resp = MagicMock()
        resp.status_code = 200
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = _check_screen_api("http://localhost:8082", "rules", "Rules list")
        assert result["status"] == "PASS"
        assert result["id"] == "PW-SCREEN-RULES"

    def test_fail_status_code(self):
        from governance.routes.tests.playwright_api_fallback import _check_screen_api
        resp = MagicMock()
        resp.status_code = 500
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = _check_screen_api("http://localhost:8082", "tasks", "Tasks list")
        assert result["status"] == "FAIL"

    def test_exception(self):
        from governance.routes.tests.playwright_api_fallback import _check_screen_api
        with patch(f"{_P}.httpx.get", side_effect=Exception("connect error")):
            result = _check_screen_api("http://localhost:8082", "sessions", "Sessions")
        assert result["status"] == "ERROR"

    def test_unknown_nav_key(self):
        from governance.routes.tests.playwright_api_fallback import _check_screen_api
        resp = MagicMock()
        resp.status_code = 200
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = _check_screen_api("http://localhost:8082", "unknown", "Unknown")
        assert result["status"] == "PASS"  # falls back to /api/health


# ── _check_chat_api ──────────────────────────────────────────────


class TestCheckChatApi:
    def test_pass_with_response(self):
        from governance.routes.tests.playwright_api_fallback import _check_chat_api
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"response": "OK"}
        with patch(f"{_P}.httpx.post", return_value=resp):
            result = _check_chat_api("http://localhost:8082")
        assert result["status"] == "PASS"
        assert result["id"] == "PW-CHAT-001"

    def test_pass_with_message_key(self):
        from governance.routes.tests.playwright_api_fallback import _check_chat_api
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"message": "Health OK"}
        with patch(f"{_P}.httpx.post", return_value=resp):
            result = _check_chat_api("http://localhost:8082")
        assert result["status"] == "PASS"

    def test_fail_empty_response(self):
        from governance.routes.tests.playwright_api_fallback import _check_chat_api
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {}
        with patch(f"{_P}.httpx.post", return_value=resp):
            result = _check_chat_api("http://localhost:8082")
        assert result["status"] == "FAIL"

    def test_fail_non_200(self):
        from governance.routes.tests.playwright_api_fallback import _check_chat_api
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "Internal Server Error"
        with patch(f"{_P}.httpx.post", return_value=resp):
            result = _check_chat_api("http://localhost:8082")
        assert result["status"] == "FAIL"

    def test_error(self):
        from governance.routes.tests.playwright_api_fallback import _check_chat_api
        with patch(f"{_P}.httpx.post", side_effect=Exception("timeout")):
            result = _check_chat_api("http://localhost:8082")
        assert result["status"] == "ERROR"


# ── check_api_data_integrity ─────────────────────────────────────


class TestCheckApiDataIntegrity:
    def test_pass_all_ok(self):
        from governance.routes.tests.playwright_api_fallback import check_api_data_integrity
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [], "pagination": {}}
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = check_api_data_integrity("http://localhost:8082")
        assert result["status"] == "PASS"
        assert result["id"] == "PW-INTEGRITY-001"

    def test_fail_missing_pagination(self):
        from governance.routes.tests.playwright_api_fallback import check_api_data_integrity
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": []}
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = check_api_data_integrity("http://localhost:8082")
        assert result["status"] == "FAIL"
        assert any("pagination" in v for v in result["violations"])

    def test_fail_missing_items(self):
        from governance.routes.tests.playwright_api_fallback import check_api_data_integrity
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"pagination": {}}
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = check_api_data_integrity("http://localhost:8082")
        assert result["status"] == "FAIL"

    def test_fail_non_200(self):
        from governance.routes.tests.playwright_api_fallback import check_api_data_integrity
        resp = MagicMock()
        resp.status_code = 500
        with patch(f"{_P}.httpx.get", return_value=resp):
            result = check_api_data_integrity("http://localhost:8082")
        assert result["status"] == "FAIL"

    def test_error(self):
        from governance.routes.tests.playwright_api_fallback import check_api_data_integrity
        with patch(f"{_P}.httpx.get", side_effect=Exception("global error")):
            result = check_api_data_integrity("http://localhost:8082")
        assert result["status"] == "FAIL"


# ── run_api_fallback ─────────────────────────────────────────────


class TestRunApiFallback:
    def test_returns_summary(self):
        from governance.routes.tests.playwright_api_fallback import run_api_fallback
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [], "pagination": {}, "response": "ok"}
        with patch(f"{_P}.httpx.get", return_value=resp), \
             patch(f"{_P}.httpx.post", return_value=resp):
            result = run_api_fallback("http://localhost:8081", "http://localhost:8082")
        assert "checks" in result
        assert "summary" in result
        assert result["summary"]["total"] >= 8  # 1 dashboard + 6 screens + 1 chat + 1 integrity
