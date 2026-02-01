"""Rule Service Layer - Single code path for all rule operations.

Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.

Created: 2026-02-01
"""
import logging
from typing import Optional, Dict, Any, List

from governance.client import get_client
from governance.rule_linker import LEGACY_TO_SEMANTIC, normalize_rule_id
from governance.stores.audit import record_audit

logger = logging.getLogger(__name__)


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
    except Exception:
        pass


def _get_client_or_raise():
    """Get TypeDB client or raise ConnectionError."""
    client = get_client()
    if not client:
        raise ConnectionError("TypeDB not connected")
    return client


def get_semantic_id(legacy_id: str) -> Optional[str]:
    """Get semantic ID for a legacy rule ID."""
    return LEGACY_TO_SEMANTIC.get(legacy_id)


def resolve_rule(client, rule_id: str):
    """Resolve a rule by ID, trying semantic then legacy format.

    Returns:
        (actual_id, rule) tuple.

    Raises:
        KeyError: If rule not found.
    """
    rule = client.get_rule_by_id(rule_id)
    if rule:
        return rule_id, rule
    legacy_id = normalize_rule_id(rule_id)
    if legacy_id != rule_id:
        rule = client.get_rule_by_id(legacy_id)
        if rule:
            return legacy_id, rule
    raise KeyError(f"Rule {rule_id} not found")


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


def rule_to_response_dict(rule, doc_path: Optional[str] = None,
                          linkage_counts: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """Convert a TypeDB Rule entity to response dict."""
    lc = linkage_counts or {}
    return {
        "id": rule.id,
        "semantic_id": get_semantic_id(rule.id),
        "name": rule.name,
        "category": rule.category,
        "priority": rule.priority,
        "status": rule.status,
        "directive": rule.directive,
        "created_date": rule.created_date.isoformat() if rule.created_date else None,
        "document_path": doc_path,
        "applicability": rule.applicability,
        "linked_tasks_count": lc.get("tasks", 0),
        "linked_sessions_count": lc.get("sessions", 0),
    }


def list_rules(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "id",
    order: str = "asc",
    offset: int = 0,
    limit: int = 50,
    source: str = "rest",
) -> Dict[str, Any]:
    """List rules with pagination, sorting, filtering, and search.

    Returns:
        Dict with 'items' (list of rule response dicts) and pagination metadata.
    """
    client = _get_client_or_raise()

    if category:
        rules = client.get_rules_by_category(category)
    elif status == "ACTIVE":
        rules = client.get_active_rules()
    else:
        rules = client.get_all_rules()

    if status and status != "ACTIVE":
        rules = [r for r in rules if r.status == status]
    if priority:
        rules = [r for r in rules if r.priority == priority]
    if search:
        from governance.routes.rules.search import filter_rules_by_search
        rules = filter_rules_by_search(rules, search)

    valid_sort_fields = ["id", "name", "priority", "status", "category"]
    sort_field = sort_by if sort_by in valid_sort_fields else "id"
    rules.sort(key=lambda r: getattr(r, sort_field) or "", reverse=order.lower() == "desc")

    total = len(rules)
    paginated = rules[offset: offset + limit]

    rule_ids = [r.id for r in paginated]
    doc_paths = get_rule_document_paths(client, rule_ids)
    linkage_counts = get_rule_linkage_counts(client, rule_ids)

    items = [rule_to_response_dict(r, doc_paths.get(r.id), linkage_counts.get(r.id))
             for r in paginated]

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total,
    }


def get_rule(rule_id: str, source: str = "rest") -> Dict[str, Any]:
    """Get a rule by ID.

    Returns:
        Rule response dict.

    Raises:
        KeyError: If not found.
    """
    client = _get_client_or_raise()
    _, rule = resolve_rule(client, rule_id)
    doc_paths = get_rule_document_paths(client, [rule.id])
    return rule_to_response_dict(rule, doc_paths.get(rule.id))


def create_rule(
    rule_id: str,
    name: str = "",
    category: str = "",
    priority: str = "MEDIUM",
    directive: str = "",
    status: str = "ACTIVE",
    source: str = "rest",
) -> Dict[str, Any]:
    """Create a new rule.

    Returns:
        Rule response dict.

    Raises:
        ValueError: If rule already exists.
    """
    client = _get_client_or_raise()

    existing = client.get_rule_by_id(rule_id)
    if existing:
        raise ValueError(f"Rule {rule_id} already exists")

    created = client.create_rule(
        rule_id=rule_id, name=name, category=category,
        priority=priority, directive=directive, status=status,
    )
    if not created:
        raise RuntimeError("Failed to create rule")

    record_audit("CREATE", "rule", rule_id,
                 metadata={"name": name, "category": category, "priority": priority, "source": source})
    _monitor("create", rule_id, source=source, category=category)
    return rule_to_response_dict(created)


def update_rule(
    rule_id: str,
    name: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    directive: Optional[str] = None,
    status: Optional[str] = None,
    source: str = "rest",
) -> Dict[str, Any]:
    """Update a rule.

    Returns:
        Updated rule response dict.

    Raises:
        KeyError: If not found.
    """
    client = _get_client_or_raise()
    actual_id, _ = resolve_rule(client, rule_id)

    updated = client.update_rule(
        rule_id=actual_id, name=name, category=category,
        priority=priority, directive=directive, status=status,
    )
    if not updated:
        raise RuntimeError("Failed to update rule")

    record_audit("UPDATE", "rule", actual_id,
                 metadata={"name": name, "status": status, "priority": priority, "source": source})
    _monitor("update", actual_id, source=source, status=status)
    doc_paths = get_rule_document_paths(client, [updated.id])
    return rule_to_response_dict(updated, doc_paths.get(updated.id))


def delete_rule(rule_id: str, archive: bool = True, source: str = "rest") -> bool:
    """Delete a rule.

    Returns:
        True if deleted.

    Raises:
        KeyError: If not found.
    """
    client = _get_client_or_raise()
    actual_id, _ = resolve_rule(client, rule_id)

    deleted = client.delete_rule(actual_id, archive=archive)
    if not deleted:
        return False

    record_audit("DELETE", "rule", actual_id,
                 metadata={"archive": archive, "source": source})
    _monitor("delete", actual_id, source=source, archive=archive)
    return True


def get_rule_tasks(rule_id: str, source: str = "rest") -> Dict[str, Any]:
    """Get tasks implementing a specific rule."""
    client = _get_client_or_raise()
    tasks = client.get_tasks_for_rule(rule_id)
    if not tasks:
        legacy_id = normalize_rule_id(rule_id)
        if legacy_id != rule_id:
            tasks = client.get_tasks_for_rule(legacy_id)
    return {"rule_id": rule_id, "implementing_tasks": tasks, "count": len(tasks)}


def get_rule_dependencies(rule_id: str, source: str = "rest") -> Dict[str, Any]:
    """Get rules that a rule depends on and is depended by."""
    client = _get_client_or_raise()
    actual_id, _ = resolve_rule(client, rule_id)
    deps = client.get_rule_dependencies(actual_id)
    dependents = client.get_rules_depending_on(actual_id)
    return {"rule_id": actual_id, "depends_on": deps, "depended_by": dependents}


def create_rule_dependency(rule_id: str, dep_id: str, source: str = "rest") -> bool:
    """Create a dependency relation between two rules."""
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
