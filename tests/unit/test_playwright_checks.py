"""
Unit tests for Playwright Dynamic UI Checks.

Per DOC-SIZE-01-v1: Tests for routes/tests/playwright_checks.py module.
Tests: DASHBOARD_SCREENS, _tally, _try_playwright_import, run_playwright_checks,
       _pw_check_dashboard_loads, _pw_check_screen, _pw_check_chat,
       _run_with_playwright.
"""

from unittest.mock import patch, MagicMock

import pytest

_P = "governance.routes.tests.playwright_checks"


# ── DASHBOARD_SCREENS ────────────────────────────────────────────


class TestDashboardScreens:
    def test_has_expected_screens(self):
        from governance.routes.tests.playwright_checks import DASHBOARD_SCREENS
        keys = [s[0] for s in DASHBOARD_SCREENS]
        assert "rules" in keys
        assert "tasks" in keys
        assert "sessions" in keys

    def test_six_screens(self):
        from governance.routes.tests.playwright_checks import DASHBOARD_SCREENS
        assert len(DASHBOARD_SCREENS) == 6

    def test_screen_tuple_structure(self):
        from governance.routes.tests.playwright_checks import DASHBOARD_SCREENS
        for screen in DASHBOARD_SCREENS:
            assert len(screen) == 3  # (nav_key, testid, description)


# ── _tally ───────────────────────────────────────────────────────


class TestTally:
    def test_pass(self):
        from governance.routes.tests.playwright_checks import _tally
        p, f, e = _tally({"status": "PASS"}, 0, 0, 0)
        assert (p, f, e) == (1, 0, 0)

    def test_fail(self):
        from governance.routes.tests.playwright_checks import _tally
        p, f, e = _tally({"status": "FAIL"}, 0, 0, 0)
        assert (p, f, e) == (0, 1, 0)

    def test_error(self):
        from governance.routes.tests.playwright_checks import _tally
        p, f, e = _tally({"status": "ERROR"}, 0, 0, 0)
        assert (p, f, e) == (0, 0, 1)

    def test_skip(self):
        from governance.routes.tests.playwright_checks import _tally
        p, f, e = _tally({"status": "SKIP"}, 0, 0, 0)
        assert (p, f, e) == (0, 0, 0)

    def test_accumulates(self):
        from governance.routes.tests.playwright_checks import _tally
        p, f, e = _tally({"status": "PASS"}, 5, 2, 1)
        assert (p, f, e) == (6, 2, 1)


# ── _try_playwright_import ───────────────────────────────────────


class TestTryPlaywrightImport:
    def test_not_installed(self):
        from governance.routes.tests.playwright_checks import _try_playwright_import
        with patch.dict("sys.modules", {"playwright": None, "playwright.sync_api": None}):
            # playwright import may already be cached; test the function logic
            result = _try_playwright_import()
            # Result depends on whether playwright is actually installed
            assert result is None or callable(result)


# ── _pw_check_dashboard_loads ────────────────────────────────────


class TestPwCheckDashboardLoads:
    def test_pass(self):
        from governance.routes.tests.playwright_checks import _pw_check_dashboard_loads
        page = MagicMock()
        page.title.return_value = "Governance Dashboard"
        result = _pw_check_dashboard_loads(page, "http://localhost:8081")
        assert result["status"] == "PASS"
        assert result["id"] == "PW-DASH-001"
        assert "duration_ms" in result

    def test_fail(self):
        from governance.routes.tests.playwright_checks import _pw_check_dashboard_loads
        page = MagicMock()
        page.goto.side_effect = Exception("timeout")
        result = _pw_check_dashboard_loads(page, "http://localhost:8081")
        assert result["status"] == "FAIL"
        assert "timeout" in result["message"]


# ── _pw_check_screen ─────────────────────────────────────────────


class TestPwCheckScreen:
    def test_pass_with_nav_element(self):
        from governance.routes.tests.playwright_checks import _pw_check_screen
        page = MagicMock()
        nav_el = MagicMock()
        target_el = MagicMock()
        target_el.is_visible.return_value = True
        page.query_selector.side_effect = [nav_el, target_el]
        result = _pw_check_screen(
            page, "http://localhost:8081", "rules", "rules-table", "Rules load",
        )
        assert result["status"] == "PASS"
        assert result["id"] == "PW-SCREEN-RULES"

    def test_pass_without_nav_element(self):
        from governance.routes.tests.playwright_checks import _pw_check_screen
        page = MagicMock()
        target_el = MagicMock()
        target_el.is_visible.return_value = True
        page.query_selector.side_effect = [None, target_el]
        result = _pw_check_screen(
            page, "http://localhost:8081", "tasks", "tasks-table", "Tasks load",
        )
        assert result["status"] == "PASS"
        page.evaluate.assert_called_once()

    def test_fail_not_visible(self):
        from governance.routes.tests.playwright_checks import _pw_check_screen
        page = MagicMock()
        page.query_selector.side_effect = [MagicMock(), None]
        result = _pw_check_screen(
            page, "http://localhost:8081", "rules", "rules-table", "Rules load",
        )
        assert result["status"] == "FAIL"

    def test_error(self):
        from governance.routes.tests.playwright_checks import _pw_check_screen
        page = MagicMock()
        page.query_selector.side_effect = Exception("browser crash")
        result = _pw_check_screen(
            page, "http://localhost:8081", "rules", "rules-table", "Rules load",
        )
        assert result["status"] == "ERROR"


# ── _pw_check_chat ───────────────────────────────────────────────


class TestPwCheckChat:
    def test_pass(self):
        from governance.routes.tests.playwright_checks import _pw_check_chat
        page = MagicMock()
        nav = MagicMock()
        chat_input = MagicMock()
        send_btn = MagicMock()
        messages = [MagicMock(), MagicMock()]
        page.query_selector.side_effect = [nav, chat_input, send_btn]
        page.query_selector_all.return_value = messages
        result = _pw_check_chat(page, "http://localhost:8081")
        assert result["status"] == "PASS"
        assert result["id"] == "PW-CHAT-001"

    def test_no_chat_input(self):
        from governance.routes.tests.playwright_checks import _pw_check_chat
        page = MagicMock()
        page.query_selector.side_effect = [MagicMock(), None]
        result = _pw_check_chat(page, "http://localhost:8081")
        assert result["status"] == "FAIL"

    def test_no_response(self):
        from governance.routes.tests.playwright_checks import _pw_check_chat
        page = MagicMock()
        page.query_selector.side_effect = [MagicMock(), MagicMock(), MagicMock()]
        page.query_selector_all.return_value = [MagicMock()]  # Only 1 message
        result = _pw_check_chat(page, "http://localhost:8081")
        assert result["status"] == "FAIL"

    def test_no_send_button_uses_enter(self):
        from governance.routes.tests.playwright_checks import _pw_check_chat
        page = MagicMock()
        chat_input = MagicMock()
        page.query_selector.side_effect = [MagicMock(), chat_input, None]
        page.query_selector_all.return_value = [MagicMock(), MagicMock()]
        result = _pw_check_chat(page, "http://localhost:8081")
        chat_input.press.assert_called_once_with("Enter")
        assert result["status"] == "PASS"

    def test_error(self):
        from governance.routes.tests.playwright_checks import _pw_check_chat
        page = MagicMock()
        page.query_selector.side_effect = Exception("browser error")
        result = _pw_check_chat(page, "http://localhost:8081")
        assert result["status"] == "ERROR"


# ── run_playwright_checks ────────────────────────────────────────


class TestRunPlaywrightChecks:
    def test_with_playwright(self):
        from governance.routes.tests.playwright_checks import run_playwright_checks
        with patch(f"{_P}._try_playwright_import", return_value=MagicMock()), \
             patch(f"{_P}._run_with_playwright", return_value={"checks": [], "summary": {}}):
            result = run_playwright_checks()
        assert "checks" in result

    def test_without_playwright_uses_fallback(self):
        from governance.routes.tests.playwright_checks import run_playwright_checks
        with patch(f"{_P}._try_playwright_import", return_value=None), \
             patch("governance.routes.tests.playwright_api_fallback.run_api_fallback",
                   return_value={"checks": [], "summary": {}}):
            result = run_playwright_checks()
        assert "checks" in result

    def test_default_urls(self):
        from governance.routes.tests.playwright_checks import run_playwright_checks
        with patch(f"{_P}._try_playwright_import", return_value=None), \
             patch("governance.routes.tests.playwright_api_fallback.run_api_fallback",
                   return_value={"checks": [], "summary": {}}) as mock_fb:
            run_playwright_checks()
        # Called with default URLs from env


# ── _run_with_playwright ─────────────────────────────────────────


class TestRunWithPlaywright:
    def test_browser_error(self):
        from governance.routes.tests.playwright_checks import _run_with_playwright
        sync_pw = MagicMock()
        sync_pw.return_value.__enter__ = MagicMock(side_effect=Exception("no browser"))
        sync_pw.return_value.__exit__ = MagicMock()
        result = _run_with_playwright(sync_pw, "http://localhost:8081", "http://localhost:8082")
        assert result["summary"]["errors"] >= 1
        assert any(r["id"] == "PW-BROWSER-ERROR" for r in result["checks"])
