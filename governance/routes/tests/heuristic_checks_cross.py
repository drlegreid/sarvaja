"""
Heuristic Checks: Cross-Entity, API, and UI Domains.

Per D.4: Rule-driven integrity checks.
Per DOC-SIZE-01-v1: Split from heuristic_checks.py to stay under 300 lines.
Per RULES-EXPLORATORY-TESTING.md: Use REST MCP for API checks; server-side skips self-referential calls.

Created: 2026-02-01
"""
import logging
import os
import httpx

logger = logging.getLogger(__name__)


def _is_self_referential(api_base_url: str) -> bool:
    """Detect if api_base_url points to our own server (causes timeout loops)."""
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


# ===== CROSS-ENTITY DOMAIN =====

def check_service_layer_coverage(api_base_url: str) -> dict:
    """H-CROSS-001: All service layers must be SERVICE_LAYER."""
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential: use REST MCP from host", "violations": []}
    data = _api_get(api_base_url, "/api/mcp/readiness")
    if not data:
        return {"status": "SKIP", "message": "Readiness endpoint unavailable", "violations": []}
    sl = data.get("service_layer", {})
    violations = [domain for domain, status in sl.items() if status != "SERVICE_LAYER"]
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} domains not using service layer: {violations}" if violations else "All domains use service layer",
        "violations": violations,
    }


# ===== API DOMAIN =====

def check_api_endpoint_health(api_base_url: str) -> dict:
    """H-API-001: All core endpoints return 2xx on GET."""
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential: use REST MCP from host", "violations": []}
    endpoints = [
        "/api/tasks", "/api/sessions", "/api/rules",
        "/api/agents", "/api/health", "/api/mcp/readiness",
    ]
    violations = []
    for ep in endpoints:
        try:
            resp = httpx.get(f"{api_base_url}{ep}", timeout=10.0)
            if resp.status_code >= 400:
                violations.append(f"{ep} -> {resp.status_code}")
        except Exception as e:
            violations.append(f"{ep} -> {e}")
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} endpoints unhealthy" if violations else f"All {len(endpoints)} endpoints healthy",
        "violations": violations,
    }


def check_pagination_contract(api_base_url: str) -> dict:
    """H-API-002: Paginated endpoints return consistent structure."""
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential: use REST MCP from host", "violations": []}
    endpoints = ["/api/tasks", "/api/sessions", "/api/rules", "/api/agents"]
    required_fields = {"total", "offset", "limit", "has_more", "returned"}
    violations = []
    for ep in endpoints:
        try:
            resp = httpx.get(f"{api_base_url}{ep}?limit=1", timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                if "pagination" not in data:
                    violations.append(f"{ep}: missing pagination key")
                elif not required_fields.issubset(set(data["pagination"].keys())):
                    missing = required_fields - set(data["pagination"].keys())
                    violations.append(f"{ep}: missing {missing}")
                if "items" not in data:
                    violations.append(f"{ep}: missing items key")
        except Exception as e:
            violations.append(f"{ep}: {e}")
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} pagination violations" if violations else "All endpoints have consistent pagination",
        "violations": violations,
    }


def check_decisions_link_rules(api_base_url: str) -> dict:
    """H-CROSS-003: Decisions must link to at least one rule."""
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential: use REST MCP", "violations": []}
    decisions = _api_get(api_base_url, "/api/decisions?limit=100")
    if not decisions:
        return {"status": "SKIP", "message": "No decisions found", "violations": []}
    violations = []
    for d in decisions:
        rules = d.get("rules_applied", d.get("rule_ids", []))
        if not rules:
            violations.append(d.get("decision_id", d.get("id", "unknown")))
    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{len(decisions)} decisions not linked to any rule"
            if violations else f"All {len(decisions)} decisions link to rules"
        ),
        "violations": violations[:20],
    }


def check_rule_document_paths(api_base_url: str) -> dict:
    """H-RULE-001: Every ACTIVE rule must have a document_path."""
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential: use REST MCP", "violations": []}
    rules = _api_get(api_base_url, "/api/rules?limit=200")
    active = [r for r in rules if r.get("status") == "ACTIVE"]
    if not active:
        return {"status": "SKIP", "message": "No active rules found", "violations": []}
    violations = [
        r.get("rule_id", "unknown")
        for r in active
        if not r.get("document_path")
    ]
    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{len(active)} active rules lack document_path"
            if violations else f"All {len(active)} active rules have document_path"
        ),
        "violations": violations[:20],
    }


# ===== UI DOMAIN =====

def check_testid_coverage(api_base_url: str) -> dict:
    """H-UI-003: View files should have data-testid on key components."""
    import glob
    import os
    views_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                             "agent", "governance_ui", "views")
    views_dir = os.path.normpath(views_dir)
    violations = []
    for filepath in glob.glob(os.path.join(views_dir, "**", "*.py"), recursive=True):
        if "__pycache__" in filepath:
            continue
        try:
            with open(filepath) as f:
                content = f.read()
            has_components = "VCard(" in content or "VDialog(" in content
            has_testid = "data-testid" in content or "data_testid" in content
            if has_components and not has_testid:
                violations.append(os.path.basename(filepath))
        except Exception:
            pass
    return {
        "status": "FAIL" if violations else "PASS",
        "message": f"{len(violations)} view files lack data-testid" if violations else "Key views have data-testid attributes",
        "violations": violations[:20],
    }


# ===== REGISTRY (Cross-Entity/API/UI checks only) =====

CROSS_API_UI_CHECKS = [
    {"id": "H-CROSS-001", "domain": "CROSS-ENTITY", "name": "Service layer coverage", "check_fn": check_service_layer_coverage},
    {"id": "H-CROSS-003", "domain": "CROSS-ENTITY", "name": "Decisions link to rules", "check_fn": check_decisions_link_rules},
    {"id": "H-RULE-001", "domain": "RULE", "name": "Active rules have document_path", "check_fn": check_rule_document_paths},
    {"id": "H-API-001", "domain": "API", "name": "Endpoint health", "check_fn": check_api_endpoint_health},
    {"id": "H-API-002", "domain": "API", "name": "Pagination contract", "check_fn": check_pagination_contract},
    {"id": "H-UI-003", "domain": "UI", "name": "data-testid coverage", "check_fn": check_testid_coverage},
]
