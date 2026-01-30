"""
Rules CRUD Routes.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-002: Extracted from api.py.
Per GAP-MCP-008: Semantic rule ID support.
Per DOC-SIZE-01-v1: Modularized from rules.py.
Per GAP-UI-AUDIT-001: Rule-document linkage for dashboard.

Created: 2024-12-28
Updated: 2026-01-17 - Modularized to package
Updated: 2026-01-21 - Added document_path to rule responses
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional

from governance.client import get_client
from governance.models import RuleCreate, RuleUpdate, RuleResponse, PaginatedRuleResponse, PaginationMeta
from governance.rule_linker import (
    LEGACY_TO_SEMANTIC,
    normalize_rule_id
)
from governance.routes.rules.search import filter_rules_by_search
from governance.stores.audit import record_audit

router = APIRouter(tags=["Rules"])
logger = logging.getLogger(__name__)


def get_semantic_id(legacy_id: str) -> Optional[str]:
    """Get semantic ID for a legacy rule ID. Per GAP-MCP-008."""
    return LEGACY_TO_SEMANTIC.get(legacy_id)


def get_rule_document_paths(client, rule_ids: List[str]) -> Dict[str, str]:
    """
    Batch query document paths for multiple rules.
    Per GAP-UI-AUDIT-001: Efficient batch query for rule-document linkage.
    """
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
    """
    Batch query task and session counts linked to rules.
    Per PLAN-UI-OVERHAUL-001 Task 1.1: Grid with Tasks/Sessions count columns.
    """
    if not rule_ids:
        return {}
    counts: Dict[str, Dict[str, int]] = {}
    try:
        # Count tasks linked to rules via task-rule-link
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
        # Count sessions linked to rules via session-rule-link
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


def _rule_to_response(rule, doc_path: Optional[str] = None,
                      linkage_counts: Optional[Dict[str, int]] = None) -> RuleResponse:
    """Convert a TypeDB Rule entity to RuleResponse. DRY helper."""
    lc = linkage_counts or {}
    return RuleResponse(
        id=rule.id,
        semantic_id=get_semantic_id(rule.id),
        name=rule.name,
        category=rule.category,
        priority=rule.priority,
        status=rule.status,
        directive=rule.directive,
        created_date=rule.created_date.isoformat() if rule.created_date else None,
        document_path=doc_path,
        applicability=rule.applicability,
        linked_tasks_count=lc.get("tasks", 0),
        linked_sessions_count=lc.get("sessions", 0),
    )


def _resolve_rule(client, rule_id: str):
    """
    Resolve a rule by ID, trying semantic then legacy format.
    Per GAP-MCP-008: Accepts both legacy and semantic IDs.
    Returns (actual_id, rule) or raises HTTPException(404).
    """
    rule = client.get_rule_by_id(rule_id)
    if rule:
        return rule_id, rule
    legacy_id = normalize_rule_id(rule_id)
    if legacy_id != rule_id:
        rule = client.get_rule_by_id(legacy_id)
        if rule:
            return legacy_id, rule
    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


# =============================================================================
# RULES CRUD
# =============================================================================

@router.get("/rules", response_model=PaginatedRuleResponse)
async def list_rules(
    offset: int = Query(0, ge=0, description="Skip first N results"),
    limit: int = Query(50, ge=1, le=200, description="Max results (1-200)"),
    sort_by: str = Query("id", description="Sort by: id, name, priority, status, category"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in id, name, directive")
):
    """
    List governance rules with pagination, sorting, filtering, and search.

    Per GAP-UI-036: Pagination support.
    Per GAP-UI-SEARCH-001: Server-side search support.
    """
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        if category:
            rules = client.get_rules_by_category(category)
        elif status == "ACTIVE":
            rules = client.get_active_rules()
        else:
            rules = client.get_all_rules()

        # Filter by status if provided and not already filtered
        if status and status != "ACTIVE":
            rules = [r for r in rules if r.status == status]

        # Filter by priority
        if priority:
            rules = [r for r in rules if r.priority == priority]

        # Apply search filter (GAP-UI-SEARCH-001)
        if search:
            rules = filter_rules_by_search(rules, search)

        # Apply sorting
        valid_sort_fields = ["id", "name", "priority", "status", "category"]
        sort_field = sort_by if sort_by in valid_sort_fields else "id"
        reverse = order.lower() == "desc"
        rules.sort(key=lambda r: getattr(r, sort_field) or "", reverse=reverse)

        # Apply pagination
        total = len(rules)
        paginated = rules[offset:offset + limit]

        # Batch query document paths (GAP-UI-AUDIT-001)
        rule_ids = [r.id for r in paginated]
        doc_paths = get_rule_document_paths(client, rule_ids)
        # Batch query linkage counts (PLAN-UI-OVERHAUL-001 Task 1.1)
        linkage_counts = get_rule_linkage_counts(client, rule_ids)

        items = [_rule_to_response(r, doc_paths.get(r.id), linkage_counts.get(r.id))
                 for r in paginated]
        return PaginatedRuleResponse(
            items=items,
            pagination=PaginationMeta(
                total=total,
                offset=offset,
                limit=limit,
                has_more=(offset + limit) < total,
                returned=len(items),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """
    Get a specific rule by ID.

    Per GAP-MCP-008: Accepts both legacy (RULE-XXX) and semantic
    (DOMAIN-SUB-NN-vN) ID formats.
    Per GAP-EXPLOR-API-001: Rules are now stored with semantic IDs.
    """
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        _, rule = _resolve_rule(client, rule_id)
        doc_paths = get_rule_document_paths(client, [rule.id])
        return _rule_to_response(rule, doc_paths.get(rule.id))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule(rule: RuleCreate):
    """Create a new governance rule."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # Check if rule already exists
        existing = client.get_rule_by_id(rule.rule_id)
        if existing:
            raise HTTPException(status_code=409, detail=f"Rule {rule.rule_id} already exists")

        created = client.create_rule(
            rule_id=rule.rule_id,
            name=rule.name,
            category=rule.category,
            priority=rule.priority,
            directive=rule.directive,
            status=rule.status
        )

        if not created:
            raise HTTPException(status_code=500, detail="Failed to create rule")

        record_audit("CREATE", "rule", rule.rule_id,
                     metadata={"name": rule.name, "category": rule.category, "priority": rule.priority})
        return _rule_to_response(created)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, rule: RuleUpdate):
    """Update an existing rule. Per GAP-MCP-008: Accepts semantic IDs."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        actual_id, _ = _resolve_rule(client, rule_id)

        updated = client.update_rule(
            rule_id=actual_id,
            name=rule.name,
            category=rule.category,
            priority=rule.priority,
            directive=rule.directive,
            status=rule.status
        )
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update rule")

        record_audit("UPDATE", "rule", actual_id,
                     metadata={"name": rule.name, "status": rule.status, "priority": rule.priority})
        doc_paths = get_rule_document_paths(client, [updated.id])
        return _rule_to_response(updated, doc_paths.get(updated.id))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}/tasks")
async def get_rule_tasks(rule_id: str):
    """
    Get tasks implementing a specific rule.

    Per UI-AUDIT-003: Rule↔task traceability for dashboard.
    Per GAP-UI-AUDIT-001: Rules view should show implementing tasks.
    Per GAP-MCP-008: Accepts both legacy (RULE-XXX) and semantic IDs.
    """
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        tasks = client.get_tasks_for_rule(rule_id)
        if not tasks:
            legacy_id = normalize_rule_id(rule_id)
            if legacy_id != rule_id:
                tasks = client.get_tasks_for_rule(legacy_id)

        return {"rule_id": rule_id, "implementing_tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, archive: bool = Query(True, description="Archive before delete")):
    """Delete a rule (archives by default). Per GAP-MCP-008: Accepts semantic IDs."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        actual_id, _ = _resolve_rule(client, rule_id)
        deleted = client.delete_rule(actual_id, archive=archive)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete rule")

        record_audit("DELETE", "rule", actual_id, metadata={"archive": archive})
        return None
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/dependencies/overview")
async def dependency_overview():
    """
    Global dependency overview: total stats, orphaned rules, circular deps.

    Per PLAN-UI-OVERHAUL-001 Task 4.3: Global overview before rule selection.
    """
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    try:
        rules = client.get_all_rules()
        total_rules = len(rules)
        rule_ids = [r.id for r in rules]

        # Gather dependency info per rule
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

        # Orphans: rules with no deps AND no dependents
        orphan_rules = [rid for rid in rule_ids if rid not in has_deps and rid not in has_dependents]

        return {
            "total_rules": total_rules,
            "total_dependencies": total_dependencies,
            "orphan_rules": orphan_rules,
            "orphan_count": len(orphan_rules),
            "circular_count": 0,  # TODO: implement cycle detection
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}/dependencies")
async def get_rule_dependencies(rule_id: str):
    """Get rules that a rule depends on. Per GAP-IMPACT-001."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    try:
        actual_id, _ = _resolve_rule(client, rule_id)
        deps = client.get_rule_dependencies(actual_id)
        dependents = client.get_rules_depending_on(actual_id)
        return {"rule_id": actual_id, "depends_on": deps, "depended_by": dependents}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/dependencies/{dep_id}", status_code=201)
async def create_rule_dependency(rule_id: str, dep_id: str):
    """Create a dependency relation between two rules. Per GAP-IMPACT-001."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    try:
        actual_id, _ = _resolve_rule(client, rule_id)
        dep_actual, _ = _resolve_rule(client, dep_id)
        if client.create_rule_dependency(actual_id, dep_actual):
            return {"dependent": actual_id, "dependency": dep_actual, "created": True}
        raise HTTPException(status_code=500, detail="Failed to create dependency")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
