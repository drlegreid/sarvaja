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

# ── Relation name constants (DRY — single source of truth) ──────────────────
IMPLEMENTS_RULE_RELATION = "implements-rule"
IMPLEMENTS_RULE_ROLES = ("implementing-task", "implemented-rule")

SESSION_APPLIED_RULE_RELATION = "session-applied-rule"
SESSION_APPLIED_RULE_ROLES = ("applying-session", "applied-rule")

__all__ = [
    "get_rule_document_paths",
    "get_rule_linkage_counts",
    "get_rule_tasks",
    "get_rule_dependencies",
    "create_rule_dependency",
    "dependency_overview",
    "link_session_to_rule",
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
        # BUG-473-RRL-1: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"Monitor event failed for rule {rule_id}: {type(e).__name__}", exc_info=True)


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
        # BUG-473-RRL-2: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"Failed to query rule document paths: {type(e).__name__}", exc_info=True)
        return {}


def get_rule_linkage_counts(client, rule_ids: List[str]) -> Dict[str, Dict[str, int]]:
    """Batch query task and session counts linked to rules."""
    if not rule_ids:
        return {}
    counts: Dict[str, Dict[str, int]] = {}
    try:
        task_role, rule_role = IMPLEMENTS_RULE_ROLES
        query = f"""
        match
          $r isa rule-entity, has rule-id $rid;
          $t isa task;
          ({rule_role}: $r, {task_role}: $t) isa {IMPLEMENTS_RULE_RELATION};
        select $rid;
        """
        results = client.execute_query(query)
        for r in results:
            rid = r.get("rid")
            if rid:
                counts.setdefault(rid, {"tasks": 0, "sessions": 0})
                counts[rid]["tasks"] += 1
    except Exception as e:
        # BUG-477-RRL-1: Sanitize debug/info logger
        logger.debug(f"Failed to query rule-task counts: {type(e).__name__}")
    try:
        session_role, rule_role = SESSION_APPLIED_RULE_ROLES
        query = f"""
        match
          $r isa rule-entity, has rule-id $rid;
          $s isa work-session;
          ({session_role}: $s, {rule_role}: $r) isa {SESSION_APPLIED_RULE_RELATION};
        select $rid;
        """
        results = client.execute_query(query)
        for r in results:
            rid = r.get("rid")
            if rid:
                counts.setdefault(rid, {"tasks": 0, "sessions": 0})
                counts[rid]["sessions"] += 1
    except Exception as e:
        # BUG-477-RRL-2: Sanitize debug/info logger
        logger.debug(f"Failed to query rule-session counts: {type(e).__name__}")
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


def link_session_to_rule(session_id: str, rule_id: str, source: str = "auto") -> bool:
    """Link a session to a rule via session-applied-rule relation (idempotent).

    Per EPIC-GOV-RULES-V3 P5: Service layer for session-rule auto-linking.

    Args:
        session_id: Session ID
        rule_id: Rule ID
        source: Caller context for monitoring

    Returns:
        True if link created or already exists, False on failure
    """
    client = get_client()
    if not client:
        logger.warning("TypeDB not connected — cannot link session to rule")
        return False
    try:
        result = client.create_session_rule_link(session_id, rule_id)
        if result:
            _monitor("link_session_rule", rule_id, source=source, session_id=session_id)
        return bool(result)
    except Exception as e:
        logger.warning(f"link_session_to_rule failed for {session_id}->{rule_id}: {type(e).__name__}", exc_info=True)
        return False


def dependency_overview(source: str = "rest") -> Dict[str, Any]:
    """Global dependency overview: total stats, orphaned rules, real circular count."""
    from governance.services.dependency_graph import DependencyGraph

    client = _get_client_or_raise()
    rules = client.get_all_rules()
    total_rules = len(rules)
    rule_ids = [r.id for r in rules]

    # Build adjacency list from batch query
    raw_graph = client.get_all_dependencies()
    adj: Dict[str, set] = {rid: set(deps) for rid, deps in raw_graph.items()}

    # Compute stats from adjacency
    has_deps = set(adj.keys())
    has_dependents: set = set()
    total_dependencies = 0
    for deps in adj.values():
        total_dependencies += len(deps)
        has_dependents.update(deps)

    orphan_rules = [rid for rid in rule_ids if rid not in has_deps and rid not in has_dependents]

    # Real DFS cycle detection (replaces hardcoded 0)
    graph = DependencyGraph(adj)
    cycles = graph.detect_cycles()

    return {
        "total_rules": total_rules,
        "total_dependencies": total_dependencies,
        "orphan_rules": orphan_rules,
        "orphan_count": len(orphan_rules),
        "circular_count": len(cycles),
        "cycles": [[str(n) for n in c] for c in cycles],
    }
