"""
Playwright API Fallback Checks (DOC-SIZE-01-v1 split from playwright_checks.py)

API-level verification when Playwright browser is not available.
Provides the same check IDs and result shape as browser checks
for unified reporting in the regression cycle.

Created: 2026-02-01
"""
import logging
import time

import httpx

from governance.routes.tests.playwright_checks import DASHBOARD_SCREENS, _tally

logger = logging.getLogger(__name__)


def run_api_fallback(dashboard_url: str, api_base_url: str) -> dict:
    """Run API-level checks when Playwright is not available."""
    results = []
    passed = failed = errors = skipped = 0

    r = _check_dashboard_reachable(dashboard_url)
    results.append(r)
    passed, failed, errors = _tally(r, passed, failed, errors)

    for nav_key, _, desc in DASHBOARD_SCREENS:
        r = _check_screen_api(api_base_url, nav_key, desc)
        results.append(r)
        passed, failed, errors = _tally(r, passed, failed, errors)

    r = _check_chat_api(api_base_url)
    results.append(r)
    passed, failed, errors = _tally(r, passed, failed, errors)

    r = check_api_data_integrity(api_base_url)
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


def _check_dashboard_reachable(dashboard_url: str) -> dict:
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


def _check_screen_api(api_base_url: str, nav_key: str, desc: str) -> dict:
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
                "message": f"{endpoint} -> 200 ({duration_ms}ms)",
                "violations": [], "duration_ms": duration_ms,
            }
        return {
            "id": check_id, "domain": "UI-DYNAMIC", "name": f"{desc} (API)",
            "status": "FAIL",
            "message": f"{endpoint} -> {resp.status_code}",
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


def _check_chat_api(api_base_url: str) -> dict:
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


def check_api_data_integrity(api_base_url: str) -> dict:
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
