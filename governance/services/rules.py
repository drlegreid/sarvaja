"""Rule Service Layer - Single code path for all rule operations.

Per MCP enforcement: REST routes and MCP tools both call these functions.
This ensures consistent audit, monitoring, and validation regardless of entry point.

Per DOC-SIZE-01-v1: Relation/dependency functions split to rules_relations.py.

Created: 2026-02-01
"""
import logging
from typing import Optional, Dict, Any, List, Tuple

from governance.client import get_client
from governance.rule_linker import LEGACY_TO_SEMANTIC, normalize_rule_id
from governance.stores.audit import record_audit
from governance.middleware.event_log import log_event
from governance.services.rules_relations import (  # noqa: F401
    get_rule_document_paths,
    get_rule_linkage_counts,
    get_rule_tasks,
    get_rule_dependencies,
    create_rule_dependency,
    dependency_overview,
)

logger = logging.getLogger(__name__)

__all__ = [
    "get_semantic_id",
    "resolve_rule",
    "rule_to_response_dict",
    "list_rules",
    "get_rule",
    "create_rule",
    "update_rule",
    "delete_rule",
    # Re-exports from rules_relations
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


def get_semantic_id(legacy_id: str) -> Optional[str]:
    """Get semantic ID for a legacy rule ID."""
    return LEGACY_TO_SEMANTIC.get(legacy_id)


def resolve_rule(client, rule_id: str) -> Tuple[str, Any]:
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
    log_event("rule", "create", rule_id=rule_id, category=category, priority=priority, source=source)
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
    log_event("rule", "update", rule_id=actual_id, status=status, source=source)
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
    log_event("rule", "delete", rule_id=actual_id, archive=archive, source=source)
    return True


