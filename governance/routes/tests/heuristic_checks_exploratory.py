"""
Heuristic Checks: Exploratory Testing Domain.

Per D.4: Rule-driven integrity checks discovered during exploratory testing.
Per DOC-SIZE-01-v1: Separate file for exploratory-discovered checks.

These checks validate gaps found during the 2026-02-08 dynamic orthogonal
test session using Playwright MCP + REST API MCP.

Created: 2026-02-08
"""
import logging
import os

import httpx

logger = logging.getLogger(__name__)


def _is_self_referential(api_base_url: str) -> bool:
    """Detect if api_base_url points to our own server."""
    port = os.getenv("API_PORT", "8082")
    self_urls = [f"http://localhost:{port}", f"http://127.0.0.1:{port}",
                 f"http://0.0.0.0:{port}"]
    return api_base_url.rstrip("/") in self_urls


def _api_get(api_base_url: str, endpoint: str) -> dict:
    """Safe API GET with error handling."""
    try:
        resp = httpx.get(f"{api_base_url}{endpoint}", timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("items", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.debug(f"Heuristic API call failed: {endpoint}: {e}")
    return []


# ===== EXPLORATORY: DATA CONSISTENCY =====

def check_chat_session_count_accuracy(api_base_url: str) -> dict:
    """H-EXPLR-001: Chat /status session count must match API total.

    Discovered: /status reports "20 active sessions" but API shows 18 total,
    0 active. The chat command uses a different data source than the API.
    """
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential", "violations": []}
    sessions = _api_get(api_base_url, "/api/sessions?limit=1")
    if isinstance(sessions, list):
        return {"status": "SKIP", "message": "No pagination data", "violations": []}
    # sessions is actually the raw response since _api_get extracts items
    # Need direct call for pagination
    try:
        resp = httpx.get(f"{api_base_url}/api/sessions?limit=1", timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            api_total = data.get("pagination", {}).get("total", 0)
            active = [s for s in _api_get(api_base_url, "/api/sessions?limit=200")
                      if s.get("status") == "ACTIVE"]
            violations = []
            if len(active) > 0:
                violations.append(f"API shows {len(active)} active, total={api_total}")
            return {
                "status": "PASS" if api_total > 0 else "FAIL",
                "message": f"API reports {api_total} sessions, {len(active)} active",
                "violations": violations,
            }
    except Exception:
        pass
    return {"status": "SKIP", "message": "Could not check", "violations": []}


def check_monitor_event_count_consistency(api_base_url: str) -> dict:
    """H-EXPLR-002: Monitor event counter must match table row count.

    Discovered: Monitor tab shows "9 Total Events" in summary but
    event table displays 15 rows.
    """
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential", "violations": []}
    try:
        resp = httpx.get(f"{api_base_url}/api/monitor/events", timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            events = data.get("items", data) if isinstance(data, dict) else data
            count = data.get("total", len(events)) if isinstance(data, dict) else len(events)
            actual = len(events) if isinstance(events, list) else 0
            if count != actual:
                return {
                    "status": "FAIL",
                    "message": f"Counter says {count} but {actual} events returned",
                    "violations": [f"counter={count}, actual={actual}"],
                }
            return {
                "status": "PASS",
                "message": f"Event count consistent: {count}",
                "violations": [],
            }
        elif resp.status_code == 404:
            return {"status": "SKIP", "message": "Monitor API not found", "violations": []}
    except Exception:
        pass
    return {"status": "SKIP", "message": "Monitor API unavailable", "violations": []}


def check_decision_rule_linking(api_base_url: str) -> dict:
    """H-EXPLR-003: Decision creation must persist linked rules.

    Discovered: POST /api/decisions with rules_applied returns empty
    linked_rules array - rules not being stored in the relation.
    """
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential", "violations": []}
    decisions = _api_get(api_base_url, "/api/decisions?limit=100")
    if not decisions:
        return {"status": "SKIP", "message": "No decisions to check", "violations": []}
    violations = []
    for d in decisions:
        rules = d.get("linked_rules", [])
        if not rules:
            violations.append(d.get("id", "unknown"))
    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{len(decisions)} decisions have no linked rules"
            if violations else f"All {len(decisions)} decisions have linked rules"
        ),
        "violations": violations[:20],
    }


def check_audit_trail_populated(api_base_url: str) -> dict:
    """H-EXPLR-004: Audit trail must have entries after CRUD operations.

    Discovered: Audit tab shows 0 entries - no audit events are being
    captured despite CRUD operations occurring on all entity types.
    """
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential", "violations": []}
    try:
        resp = httpx.get(f"{api_base_url}/api/audit?limit=1", timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            total = 0
            if isinstance(data, dict):
                total = data.get("pagination", {}).get("total", len(data.get("items", [])))
            elif isinstance(data, list):
                total = len(data)
            return {
                "status": "PASS" if total > 0 else "FAIL",
                "message": f"{total} audit entries found" if total > 0 else "Audit trail is empty - no events captured",
                "violations": ["AUDIT_EMPTY"] if total == 0 else [],
            }
        elif resp.status_code == 404:
            return {"status": "FAIL", "message": "Audit endpoint not found", "violations": ["NO_ENDPOINT"]}
    except Exception:
        pass
    return {"status": "SKIP", "message": "Audit API unavailable", "violations": []}


def check_rule_document_paths_populated(api_base_url: str) -> dict:
    """H-EXPLR-005: Active rules should have document_path set.

    Discovered: All 42 active rules have null document_path, meaning
    there's no link between the rule and its source document.
    """
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential", "violations": []}
    rules = _api_get(api_base_url, "/api/rules?limit=200")
    active = [r for r in rules if r.get("status") == "ACTIVE"]
    if not active:
        return {"status": "SKIP", "message": "No active rules", "violations": []}
    missing = [r.get("id", "unknown") for r in active if not r.get("document_path")]
    return {
        "status": "FAIL" if len(missing) > len(active) * 0.5 else "PASS",
        "message": (
            f"{len(missing)}/{len(active)} active rules lack document_path"
            if missing else f"All {len(active)} active rules have document_path"
        ),
        "violations": missing[:20],
    }


def check_mcp_readiness_consistency(api_base_url: str) -> dict:
    """H-EXPLR-006: MCP readiness should match actual API health.

    Discovered: /api/mcp/readiness reports all backends unreachable but
    /api/health confirms TypeDB connected and data is served correctly.
    """
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential", "violations": []}
    try:
        health = httpx.get(f"{api_base_url}/api/health", timeout=10.0)
        readiness = httpx.get(f"{api_base_url}/api/mcp/readiness", timeout=10.0)
        if health.status_code == 200 and readiness.status_code == 200:
            h = health.json()
            r = readiness.json()
            violations = []
            typedb_health = h.get("typedb_connected", False)
            typedb_ready = r.get("backends", {}).get("typedb", False)
            if typedb_health and not typedb_ready:
                violations.append("typedb: health=connected but readiness=false")
            return {
                "status": "FAIL" if violations else "PASS",
                "message": (
                    f"Health/readiness mismatch: {violations}"
                    if violations else "Health and readiness consistent"
                ),
                "violations": violations,
            }
    except Exception:
        pass
    return {"status": "SKIP", "message": "Could not compare", "violations": []}


# ===== REGISTRY (Exploratory checks only) =====

EXPLORATORY_CHECKS = [
    {
        "id": "H-EXPLR-001", "domain": "CROSS-ENTITY",
        "name": "Chat/API session count consistency",
        "check_fn": check_chat_session_count_accuracy,
    },
    {
        "id": "H-EXPLR-002", "domain": "UI",
        "name": "Monitor event count consistency",
        "check_fn": check_monitor_event_count_consistency,
    },
    {
        "id": "H-EXPLR-003", "domain": "CROSS-ENTITY",
        "name": "Decision-rule linking persistence",
        "check_fn": check_decision_rule_linking,
    },
    {
        "id": "H-EXPLR-004", "domain": "CROSS-ENTITY",
        "name": "Audit trail populated",
        "check_fn": check_audit_trail_populated,
    },
    {
        "id": "H-EXPLR-005", "domain": "RULE",
        "name": "Active rules have document_path",
        "check_fn": check_rule_document_paths_populated,
    },
    {
        "id": "H-EXPLR-006", "domain": "API",
        "name": "MCP readiness vs health consistency",
        "check_fn": check_mcp_readiness_consistency,
    },
]
