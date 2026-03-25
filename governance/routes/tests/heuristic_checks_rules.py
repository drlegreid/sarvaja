"""Heuristic Checks: Rule Domain (H-RULE-002, H-RULE-005, H-RULE-006).

Per EPIC-RULES-V3-P3: Missing H-RULE checks for MANDATORY enforcement,
circular dependency detection, and unique ID validation.
Per DOC-SIZE-01-v1: Split file — rule-domain checks only.
Per DRY: Reuses _api_get and _is_self_referential from heuristic_checks_cross.

Created: 2026-03-25
"""
import logging

from governance.routes.tests.heuristic_checks_cross import _api_get, _is_self_referential

logger = logging.getLogger(__name__)


def check_mandatory_enforcement(api_base_url: str) -> dict:
    """H-RULE-002: Every MANDATORY-applicability rule has ≥1 implementing task."""
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential: use REST MCP", "violations": []}
    rules = _api_get(api_base_url, "/api/rules?limit=200")
    if not rules or not isinstance(rules, list):
        return {"status": "SKIP", "message": "No rules data available", "violations": []}
    mandatory = [r for r in rules if r.get("applicability") == "MANDATORY"]
    if not mandatory:
        return {"status": "SKIP", "message": "No MANDATORY rules found", "violations": []}
    violations = [
        r.get("rule_id", "unknown")
        for r in mandatory
        if (r.get("linked_tasks_count") or 0) == 0
    ]
    return {
        "status": "FAIL" if violations else "PASS",
        "message": (
            f"{len(violations)}/{len(mandatory)} MANDATORY rules have no implementing task"
            if violations
            else f"All {len(mandatory)} MANDATORY rules have implementing tasks"
        ),
        "violations": violations[:20],
    }


def check_rule_circular_deps(api_base_url: str) -> dict:
    """H-RULE-005: No circular dependencies in the rule dependency graph."""
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential: use REST MCP", "violations": []}
    data = _api_get(api_base_url, "/api/rules/dependencies/overview")
    if not data or not isinstance(data, dict):
        return {"status": "SKIP", "message": "Dependency overview unavailable", "violations": []}
    circular_count = data.get("circular_count", 0)
    cycles = data.get("cycles", [])
    if circular_count > 0:
        violations = [" \u2192 ".join(c) for c in cycles]
        return {
            "status": "FAIL",
            "message": f"{circular_count} circular dependencies detected",
            "violations": violations[:20],
        }
    return {"status": "PASS", "message": "No circular dependencies", "violations": []}


def check_rule_unique_ids(api_base_url: str) -> dict:
    """H-RULE-006: Every rule-id in TypeDB is unique (no duplicates)."""
    if _is_self_referential(api_base_url):
        return {"status": "SKIP", "message": "Self-referential: use REST MCP", "violations": []}
    rules = _api_get(api_base_url, "/api/rules?limit=200")
    if not rules or not isinstance(rules, list):
        return {"status": "SKIP", "message": "No rules data available", "violations": []}
    seen = set()
    duplicates = []
    for r in rules:
        rid = r.get("rule_id", "unknown")
        if rid in seen:
            duplicates.append(rid)
        else:
            seen.add(rid)
    return {
        "status": "FAIL" if duplicates else "PASS",
        "message": (
            f"{len(duplicates)} duplicate rule IDs found"
            if duplicates
            else f"All {len(rules)} rule IDs are unique"
        ),
        "violations": duplicates[:20],
    }


# ===== REGISTRY (Rule-domain checks) =====

RULE_HEURISTIC_CHECKS = [
    {"id": "H-RULE-002", "domain": "RULE", "name": "MANDATORY enforcement", "check_fn": check_mandatory_enforcement},
    {"id": "H-RULE-005", "domain": "RULE", "name": "Circular dependency detection", "check_fn": check_rule_circular_deps},
    {"id": "H-RULE-006", "domain": "RULE", "name": "Unique rule IDs", "check_fn": check_rule_unique_ids},
]
