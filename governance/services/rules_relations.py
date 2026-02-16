"""Rule Relations Service - Dependency and linkage operations.

Per DOC-SIZE-01-v1: Split from rules.py to keep under 300 lines.
Handles rule-task links, rule-session links, dependencies, and document paths.

Created: 2026-02-11
"""
import logging
from typing import Optional, Dict, Any, List

from governance.client import get_client
from governance.rule_linker import normalize_rule_id

logger = logging.getLogger(__name__)

__all__ = [
    "get_rule_document_paths",
    "get_rule_linkage_counts",
    "get_rule_tasks",
    "get_rule_dependencies",
    "create_rule_dependency",
    "dependency_overview",
]


def _get_client_or_raise():
    """Get TypeDB client or raise ConnectionError."""
    client = get_client()
    if not client:
        raise ConnectionError("TypeDB not connected")
    return client


def _monitor(action: str, rule_id: str, source: str = "service", **extra):
    """Log rule monitoring event for MCP compliance."""
    try:
        from governance.mcp_tools.common import log_monitor_event
        log_monitor_event(
            event_type="rule_event",
            source=source,
            details={"rule_id": rule_id, "action": action, **extra},
            severity="INFO",
        )
    except Exception as e:
        # BUG-MONITOR-SILENT-001: Log instead of silently swallowing
        logger.warning(f"Monitor event failed for rule {rule_id}: {e}")


def get_rule_document_paths(client, rule_ids: List[str]) -> Dict[str, str]:
    """Batch query document paths for multiple rules."""
    if not rule_ids:
        return {}
    try:
        query = """
        match
          $r isa rule-entity, has rule-id $rid;
          $d isa document, has document-path $path;
          (referencing-document: $d, referenced-rule: $r) isa document-references-rule;
        select $rid, $path;
        """
        results = client.execute_query(query)
        return {r["rid"]: r["path"] for r in results if r.get("rid") and r.get("path")}
    except Exception as e:
        logger.warning(f"Failed to query rule document paths: {e}")
        return {}


def get_rule_linkage_counts(client, rule_ids: List[str]) -> Dict[str, Dict[str, int]]:
    """Batch query task and session counts linked to rules."""
    if not rule_ids:
        return {}
    counts: Dict[str, Dict[str, int]] = {}
    try:
        query = """
        match
          $r isa rule-entity, has rule-id $rid;
          $t isa task-entity;
          (linked-rule: $r, linking-task: $t) isa task-rule-link;
        select $rid;
        """
        results = client.execute_query(query)
        for r in results:
            rid = r.get("rid")
            if rid:
                counts.setdefault(rid, {"tasks": 0, "sessions": 0})
                counts[rid]["tasks"] += 1
    except Exception as e:
        logger.debug(f"Failed to query rule-task counts: {e}")
    try:
        query = """
        match
          $r isa rule-entity, has rule-id $rid;
          $s isa work-session;
          (linked-rule: $r, linking-session: $s) isa session-rule-link;
        select $rid;
        """
        results = client.execute_query(query)
        for r in results:
            rid = r.get("rid")
            if rid:
                counts.setdefault(rid, {"tasks": 0, "sessions": 0})
                counts[rid]["sessions"] += 1
    except Exception as e:
        logger.debug(f"Failed to query rule-session counts: {e}")
    return counts


def get_rule_tasks(rule_id: str, source: str = "rest") -> Dict[str, Any]:
    """Get tasks implementing a specific rule."""
    client = _get_client_or_raise()
    tasks = client.get_tasks_for_rule(rule_id)
    if not tasks:
        legacy_id = normalize_rule_id(rule_id)
        if legacy_id != rule_id:
            tasks = client.get_tasks_for_rule(legacy_id)
    # BUG-RULES-001: Guard against None from TypeDB before len()
    tasks = tasks or []
    return {"rule_id": rule_id, "implementing_tasks": tasks, "count": len(tasks)}


def get_rule_dependencies(rule_id: str, source: str = "rest") -> Dict[str, Any]:
    """Get rules that a rule depends on and is depended by."""
    from governance.services.rules import resolve_rule
    client = _get_client_or_raise()
    actual_id, _ = resolve_rule(client, rule_id)
    deps = client.get_rule_dependencies(actual_id)
    dependents = client.get_rules_depending_on(actual_id)
    return {"rule_id": actual_id, "depends_on": deps, "depended_by": dependents}


def create_rule_dependency(rule_id: str, dep_id: str, source: str = "rest") -> bool:
    """Create a dependency relation between two rules."""
    from governance.services.rules import resolve_rule
    client = _get_client_or_raise()
    actual_id, _ = resolve_rule(client, rule_id)
    dep_actual, _ = resolve_rule(client, dep_id)
    result = client.create_rule_dependency(actual_id, dep_actual)
    if result:
        _monitor("create_dependency", actual_id, source=source, dep_id=dep_actual)
    return bool(result)


def dependency_overview(source: str = "rest") -> Dict[str, Any]:
    """Global dependency overview: total stats, orphaned rules."""
    client = _get_client_or_raise()
    rules = client.get_all_rules()
    total_rules = len(rules)
    rule_ids = [r.id for r in rules]

    has_deps = set()
    has_dependents = set()
    total_dependencies = 0
    for rid in rule_ids:
        deps = client.get_rule_dependencies(rid)
        dependents = client.get_rules_depending_on(rid)
        if deps:
            has_deps.add(rid)
            total_dependencies += len(deps)
        if dependents:
            has_dependents.add(rid)

    orphan_rules = [rid for rid in rule_ids if rid not in has_deps and rid not in has_dependents]
    return {
        "total_rules": total_rules,
        "total_dependencies": total_dependencies,
        "orphan_rules": orphan_rules,
        "orphan_count": len(orphan_rules),
        "circular_count": 0,
    }
