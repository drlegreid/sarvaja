"""
Playwright Dynamic UI Checks.

Phase 3 of regression cycle: browser-level verification using Playwright.
Checks that all dashboard screens load data and that agent chat works
(validates Anthropic API key integration).

Uses Python playwright library when available, falls back to httpx for
API-level verification. Structured identically to heuristic checks for
unified reporting.

Per RULE-007: Playwright MCP is Tier 1.
Per TEST-COMP-02-v1: Full regression must include UI verification.

Created: 2026-02-01
"""
import logging
import os
import time

import httpx

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
        return _run_api_fallback(dashboard_url, api_base_url)


# =====================================================================
# Playwright browser checks
# =====================================================================

def _run_with_playwright(sync_playwright_cls, dashboard_url, api_base_url):
    """Run checks using real Playwright browser."""
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
                # Dashboard didn't load — skip screen checks
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
                # PW-SCREEN-*: Each screen loads data
                for nav_key, testid, desc in DASHBOARD_SCREENS:
                    r = _pw_check_screen(page, dashboard_url, nav_key, testid, desc)
                    results.append(r)
                    passed, failed, errors = _tally(r, passed, failed, errors)

            # PW-CHAT-001: Agent chat works (Anthropic key integration)
            r = _pw_check_chat(page, dashboard_url)
            results.append(r)
            passed, failed, errors = _tally(r, passed, failed, errors)

            # PW-INTEGRITY-001: Data integrity across screens via API
            r = _check_api_data_integrity(api_base_url)
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
            "id": "PW-DASH-001",
            "domain": "UI-DYNAMIC",
            "name": "Dashboard loads",
            "status": "PASS",
            "message": f"Dashboard loaded in {duration_ms}ms (title: {title})",
            "violations": [],
            "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": "PW-DASH-001",
            "domain": "UI-DYNAMIC",
            "name": "Dashboard loads",
            "status": "FAIL",
            "message": f"Dashboard failed to load: {e}",
            "violations": [str(e)],
            "duration_ms": duration_ms,
        }


def _pw_check_screen(page, dashboard_url, nav_key, testid, desc) -> dict:
    """PW-SCREEN-*: Navigate to screen and verify content renders."""
    check_id = f"PW-SCREEN-{nav_key.upper()}"
    start = time.time()
    try:
        # Click navigation tab
        nav_sel = f"[data-testid='nav-{nav_key}']"
        nav_el = page.query_selector(nav_sel)
        if nav_el:
            nav_el.click()
            page.wait_for_timeout(1500)
        else:
            # Fallback: try direct navigation trigger
            page.evaluate(f"() => trigger('navigate', '{nav_key}')")
            page.wait_for_timeout(1500)

        # Check if target testid is visible
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
        # Navigate to chat
        nav = page.query_selector("[data-testid='nav-chat']")
        if nav:
            nav.click()
        else:
            page.evaluate("() => trigger('navigate', 'chat')")
        page.wait_for_timeout(1000)

        # Find chat input
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

        # Type test message
        chat_input.fill("/health")
        # Submit
        send_btn = page.query_selector(
            "[data-testid='chat-send'], button:has-text('Send')"
        )
        if send_btn:
            send_btn.click()
        else:
            chat_input.press("Enter")

        # Wait for response
        page.wait_for_timeout(5000)

        # Check for response message
        messages = page.query_selector_all(
            "[data-testid='chat-message'], .chat-message, .v-card"
        )
        duration_ms = int((time.time() - start) * 1000)

        if len(messages) >= 2:  # At least prompt + response
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


# =====================================================================
# API-level fallback (when Playwright not installed)
# =====================================================================

def _run_api_fallback(dashboard_url, api_base_url):
    """Run API-level checks when Playwright is not available."""
    results = []
    passed = failed = errors = skipped = 0

    # Dashboard reachable
    r = _check_dashboard_reachable(dashboard_url)
    results.append(r)
    passed, failed, errors = _tally(r, passed, failed, errors)

    # API screens data
    for nav_key, _, desc in DASHBOARD_SCREENS:
        r = _check_screen_api(api_base_url, nav_key, desc)
        results.append(r)
        passed, failed, errors = _tally(r, passed, failed, errors)

    # Chat API
    r = _check_chat_api(api_base_url)
    results.append(r)
    passed, failed, errors = _tally(r, passed, failed, errors)

    # Cross-screen data integrity
    r = _check_api_data_integrity(api_base_url)
    results.append(r)
    passed, failed, errors = _tally(r, passed, failed, errors)

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


def _check_dashboard_reachable(dashboard_url) -> dict:
    """PW-DASH-001 (fallback): Dashboard HTTP reachable."""
    start = time.time()
    try:
        resp = httpx.get(dashboard_url, timeout=10.0, follow_redirects=True)
        duration_ms = int((time.time() - start) * 1000)
        if resp.status_code < 400:
            return {
                "id": "PW-DASH-001", "domain": "UI-DYNAMIC",
                "name": "Dashboard reachable (API fallback)",
                "status": "PASS",
                "message": f"HTTP {resp.status_code} in {duration_ms}ms",
                "violations": [], "duration_ms": duration_ms,
            }
        return {
            "id": "PW-DASH-001", "domain": "UI-DYNAMIC",
            "name": "Dashboard reachable (API fallback)",
            "status": "FAIL",
            "message": f"HTTP {resp.status_code}",
            "violations": [f"Status {resp.status_code}"], "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": "PW-DASH-001", "domain": "UI-DYNAMIC",
            "name": "Dashboard reachable (API fallback)",
            "status": "FAIL", "message": str(e),
            "violations": [str(e)], "duration_ms": duration_ms,
        }


def _check_screen_api(api_base_url, nav_key, desc) -> dict:
    """API-level check that screen data endpoint returns data."""
    check_id = f"PW-SCREEN-{nav_key.upper()}"
    endpoint_map = {
        "rules": "/api/rules?limit=5",
        "tasks": "/api/tasks?limit=5",
        "sessions": "/api/sessions?limit=5",
        "agents": "/api/agents?limit=5",
        "tests": "/api/tests/categories",
        "infra": "/api/health",
    }
    endpoint = endpoint_map.get(nav_key, "/api/health")
    start = time.time()
    try:
        resp = httpx.get(f"{api_base_url}{endpoint}", timeout=10.0)
        duration_ms = int((time.time() - start) * 1000)
        if resp.status_code == 200:
            return {
                "id": check_id, "domain": "UI-DYNAMIC", "name": f"{desc} (API)",
                "status": "PASS",
                "message": f"{endpoint} → 200 ({duration_ms}ms)",
                "violations": [], "duration_ms": duration_ms,
            }
        return {
            "id": check_id, "domain": "UI-DYNAMIC", "name": f"{desc} (API)",
            "status": "FAIL",
            "message": f"{endpoint} → {resp.status_code}",
            "violations": [f"{endpoint}: HTTP {resp.status_code}"],
            "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": check_id, "domain": "UI-DYNAMIC", "name": f"{desc} (API)",
            "status": "ERROR", "message": str(e),
            "violations": [], "duration_ms": duration_ms,
        }


def _check_chat_api(api_base_url) -> dict:
    """PW-CHAT-001 (API fallback): Send chat message and verify response."""
    start = time.time()
    try:
        resp = httpx.post(
            f"{api_base_url}/api/chat/message",
            json={"message": "/health", "agent_id": "regression-test"},
            timeout=30.0,
        )
        duration_ms = int((time.time() - start) * 1000)
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("response", data.get("message", ""))
            if reply:
                return {
                    "id": "PW-CHAT-001", "domain": "UI-DYNAMIC",
                    "name": "Agent chat works (Anthropic key, API fallback)",
                    "status": "PASS",
                    "message": f"Chat responded ({duration_ms}ms): {reply[:80]}",
                    "violations": [], "duration_ms": duration_ms,
                }
            return {
                "id": "PW-CHAT-001", "domain": "UI-DYNAMIC",
                "name": "Agent chat works (Anthropic key, API fallback)",
                "status": "FAIL",
                "message": "Chat returned 200 but empty response",
                "violations": ["Empty response body"],
                "duration_ms": duration_ms,
            }
        return {
            "id": "PW-CHAT-001", "domain": "UI-DYNAMIC",
            "name": "Agent chat works (Anthropic key, API fallback)",
            "status": "FAIL",
            "message": f"Chat API returned {resp.status_code}",
            "violations": [f"HTTP {resp.status_code}: {resp.text[:200]}"],
            "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": "PW-CHAT-001", "domain": "UI-DYNAMIC",
            "name": "Agent chat works (Anthropic key, API fallback)",
            "status": "ERROR", "message": str(e),
            "violations": [], "duration_ms": duration_ms,
        }


# =====================================================================
# Cross-screen data integrity (works with both modes)
# =====================================================================

def _check_api_data_integrity(api_base_url) -> dict:
    """PW-INTEGRITY-001: Cross-screen data consistency via API."""
    start = time.time()
    violations = []
    try:
        endpoints = {
            "rules": "/api/rules?limit=1",
            "tasks": "/api/tasks?limit=1",
            "sessions": "/api/sessions?limit=1",
            "agents": "/api/agents?limit=1",
        }
        for name, ep in endpoints.items():
            try:
                resp = httpx.get(f"{api_base_url}{ep}", timeout=10.0)
                if resp.status_code != 200:
                    violations.append(f"{name}: HTTP {resp.status_code}")
                    continue
                data = resp.json()
                # Verify pagination contract
                if "pagination" not in data:
                    violations.append(f"{name}: missing pagination")
                if "items" not in data:
                    violations.append(f"{name}: missing items")
            except Exception as e:
                violations.append(f"{name}: {e}")

        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": "PW-INTEGRITY-001", "domain": "UI-DYNAMIC",
            "name": "Cross-screen data integrity",
            "status": "FAIL" if violations else "PASS",
            "message": (
                f"{len(violations)} data integrity issues"
                if violations
                else f"All screens return consistent data ({duration_ms}ms)"
            ),
            "violations": violations,
            "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return {
            "id": "PW-INTEGRITY-001", "domain": "UI-DYNAMIC",
            "name": "Cross-screen data integrity",
            "status": "ERROR", "message": str(e),
            "violations": [], "duration_ms": duration_ms,
        }


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
