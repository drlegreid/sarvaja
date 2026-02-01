"""
Playwright Dynamic UI Checks.

Phase 3 of regression cycle: browser-level verification using Playwright.
Checks that all dashboard screens load data and that agent chat works
(validates Anthropic API key integration).

API fallback checks are in playwright_api_fallback.py (DOC-SIZE-01-v1 split).

Per RULE-007: Playwright MCP is Tier 1.
Per TEST-COMP-02-v1: Full regression must include UI verification.

Created: 2026-02-01
Updated: 2026-02-01 - Split per DOC-SIZE-01-v1 (516→290 lines)
"""
import logging
import os
import time

logger = logging.getLogger(__name__)

# Dashboard screens to verify (nav key, expected data-testid, description)
DASHBOARD_SCREENS = [
    ("rules", "rules-table", "Rules list loads with data"),
    ("tasks", "tasks-table", "Tasks list loads with data"),
    ("sessions", "sessions-table", "Sessions list loads with data"),
    ("agents", "agents-dashboard", "Agents dashboard loads"),
    ("tests", "tests-dashboard", "Test runner dashboard loads"),
    ("infra", "infra-dashboard", "Infrastructure health loads"),
]


def _tally(result, passed, failed, errors):
    """Update tally counters from a check result."""
    s = result["status"]
    if s == "PASS":
        passed += 1
    elif s == "FAIL":
        failed += 1
    elif s == "ERROR":
        errors += 1
    return passed, failed, errors


def _try_playwright_import():
    """Try to import playwright; return None if unavailable."""
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        return None


def run_playwright_checks(
    dashboard_url: str = None,
    api_base_url: str = None,
) -> dict:
    """
    Run all dynamic UI checks.

    Uses Playwright browser when available, otherwise falls back to
    API-level checks via httpx.

    Returns dict with checks[] and summary (same shape as heuristic runner).
    """
    if not dashboard_url:
        dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:8081")
    if not api_base_url:
        api_base_url = os.getenv("GOVERNANCE_API_URL", "http://localhost:8082")

    sync_pw = _try_playwright_import()

    if sync_pw:
        return _run_with_playwright(sync_pw, dashboard_url, api_base_url)
    else:
        logger.info("Playwright not available, using API-level fallback")
        from governance.routes.tests.playwright_api_fallback import run_api_fallback
        return run_api_fallback(dashboard_url, api_base_url)


# =====================================================================
# Playwright browser checks
# =====================================================================

def _run_with_playwright(sync_playwright_cls, dashboard_url, api_base_url):
    """Run checks using real Playwright browser."""
    from governance.routes.tests.playwright_api_fallback import check_api_data_integrity

    results = []
    passed = failed = errors = skipped = 0

    try:
        with sync_playwright_cls() as pw:
            browser = pw.firefox.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            page = context.new_page()

            # PW-DASH-001: Dashboard loads
            r = _pw_check_dashboard_loads(page, dashboard_url)
            results.append(r)
            passed, failed, errors = _tally(r, passed, failed, errors)

            if r["status"] != "PASS":
                for nav_key, testid, desc in DASHBOARD_SCREENS:
                    results.append({
                        "id": f"PW-SCREEN-{nav_key.upper()}",
                        "domain": "UI-DYNAMIC",
                        "name": desc,
                        "status": "SKIP",
                        "message": "Dashboard did not load",
                        "violations": [],
                    })
                    skipped += 1
            else:
                for nav_key, testid, desc in DASHBOARD_SCREENS:
                    r = _pw_check_screen(page, dashboard_url, nav_key, testid, desc)
                    results.append(r)
                    passed, failed, errors = _tally(r, passed, failed, errors)

            # PW-CHAT-001: Agent chat works (Anthropic key integration)
            r = _pw_check_chat(page, dashboard_url)
            results.append(r)
            passed, failed, errors = _tally(r, passed, failed, errors)

            # PW-INTEGRITY-001: Data integrity across screens via API
            r = check_api_data_integrity(api_base_url)
            results.append(r)
            passed, failed, errors = _tally(r, passed, failed, errors)

            browser.close()

    except Exception as e:
        results.append({
            "id": "PW-BROWSER-ERROR",
            "domain": "UI-DYNAMIC",
            "name": "Browser launch",
            "status": "ERROR",
            "message": str(e),
            "violations": [],
        })
        errors += 1

    return {
        "checks": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
        },
    }


def _pw_check_dashboard_loads(page, dashboard_url) -> dict:
    """PW-DASH-001: Dashboard loads within 10s."""
    start = time.time()
    try:
        page.goto(dashboard_url, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        title = page.title()
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": "PW-DASH-001", "domain": "UI-DYNAMIC",
            "name": "Dashboard loads",
            "status": "PASS",
            "message": f"Dashboard loaded in {duration_ms}ms (title: {title})",
            "violations": [], "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": "PW-DASH-001", "domain": "UI-DYNAMIC",
            "name": "Dashboard loads",
            "status": "FAIL",
            "message": f"Dashboard failed to load: {e}",
            "violations": [str(e)], "duration_ms": duration_ms,
        }


def _pw_check_screen(page, dashboard_url, nav_key, testid, desc) -> dict:
    """PW-SCREEN-*: Navigate to screen and verify content renders."""
    check_id = f"PW-SCREEN-{nav_key.upper()}"
    start = time.time()
    try:
        nav_sel = f"[data-testid='nav-{nav_key}']"
        nav_el = page.query_selector(nav_sel)
        if nav_el:
            nav_el.click()
            page.wait_for_timeout(1500)
        else:
            page.evaluate(f"() => trigger('navigate', '{nav_key}')")
            page.wait_for_timeout(1500)

        target_sel = f"[data-testid='{testid}']"
        target = page.query_selector(target_sel)
        duration_ms = int((time.time() - start) * 1000)

        if target and target.is_visible():
            return {
                "id": check_id, "domain": "UI-DYNAMIC", "name": desc,
                "status": "PASS",
                "message": f"Screen '{nav_key}' loaded ({duration_ms}ms)",
                "violations": [], "duration_ms": duration_ms,
            }
        else:
            return {
                "id": check_id, "domain": "UI-DYNAMIC", "name": desc,
                "status": "FAIL",
                "message": f"Screen '{nav_key}': {testid} not visible",
                "violations": [f"Missing data-testid='{testid}'"],
                "duration_ms": duration_ms,
            }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": check_id, "domain": "UI-DYNAMIC", "name": desc,
            "status": "ERROR", "message": str(e),
            "violations": [], "duration_ms": duration_ms,
        }


def _pw_check_chat(page, dashboard_url) -> dict:
    """PW-CHAT-001: Agent chat works - validates Anthropic key integration."""
    start = time.time()
    try:
        nav = page.query_selector("[data-testid='nav-chat']")
        if nav:
            nav.click()
        else:
            page.evaluate("() => trigger('navigate', 'chat')")
        page.wait_for_timeout(1000)

        chat_input = page.query_selector(
            "[data-testid='chat-input'], textarea, input[type='text']"
        )
        if not chat_input:
            duration_ms = int((time.time() - start) * 1000)
            return {
                "id": "PW-CHAT-001", "domain": "UI-DYNAMIC",
                "name": "Agent chat works (Anthropic key)",
                "status": "FAIL",
                "message": "Chat input not found on page",
                "violations": ["No chat input element"], "duration_ms": duration_ms,
            }

        chat_input.fill("/health")
        send_btn = page.query_selector(
            "[data-testid='chat-send'], button:has-text('Send')"
        )
        if send_btn:
            send_btn.click()
        else:
            chat_input.press("Enter")

        page.wait_for_timeout(5000)

        messages = page.query_selector_all(
            "[data-testid='chat-message'], .chat-message, .v-card"
        )
        duration_ms = int((time.time() - start) * 1000)

        if len(messages) >= 2:
            return {
                "id": "PW-CHAT-001", "domain": "UI-DYNAMIC",
                "name": "Agent chat works (Anthropic key)",
                "status": "PASS",
                "message": f"Chat responded with {len(messages)} messages ({duration_ms}ms)",
                "violations": [], "duration_ms": duration_ms,
            }
        else:
            return {
                "id": "PW-CHAT-001", "domain": "UI-DYNAMIC",
                "name": "Agent chat works (Anthropic key)",
                "status": "FAIL",
                "message": f"Chat did not produce response (found {len(messages)} messages)",
                "violations": ["No chat response received"],
                "duration_ms": duration_ms,
            }

    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": "PW-CHAT-001", "domain": "UI-DYNAMIC",
            "name": "Agent chat works (Anthropic key)",
            "status": "ERROR", "message": str(e),
            "violations": [], "duration_ms": duration_ms,
        }
