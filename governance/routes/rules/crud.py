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
from governance.models import RuleCreate, RuleUpdate, RuleResponse
from governance.rule_linker import (
    LEGACY_TO_SEMANTIC,
    normalize_rule_id
)
from governance.routes.rules.search import filter_rules_by_search

router = APIRouter(tags=["Rules"])
logger = logging.getLogger(__name__)


def get_semantic_id(legacy_id: str) -> Optional[str]:
    """Get semantic ID for a legacy rule ID. Per GAP-MCP-008."""
    return LEGACY_TO_SEMANTIC.get(legacy_id)


def get_rule_document_paths(client, rule_ids: List[str]) -> Dict[str, str]:
    """
    Batch query document paths for multiple rules.

    Per GAP-UI-AUDIT-001: Efficient batch query for rule-document linkage.

    Args:
        client: TypeDB client instance
        rule_ids: List of rule IDs to query

    Returns:
        Dict mapping rule_id -> document_path
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

        # Build mapping of rule_id -> document_path
        doc_paths = {}
        for r in results:
            rid = r.get("rid")
            path = r.get("path")
            if rid and path:
                doc_paths[rid] = path

        return doc_paths
    except Exception as e:
        logger.warning(f"Failed to query rule document paths: {e}")
        return {}


# =============================================================================
# RULES CRUD
# =============================================================================

@router.get("/rules", response_model=List[RuleResponse])
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
        rules = rules[offset:offset + limit]

        # Batch query document paths (GAP-UI-AUDIT-001)
        rule_ids = [r.id for r in rules]
        doc_paths = get_rule_document_paths(client, rule_ids)

        return [
            RuleResponse(
                id=r.id,
                semantic_id=get_semantic_id(r.id),
                name=r.name,
                category=r.category,
                priority=r.priority,
                status=r.status,
                directive=r.directive,
                created_date=r.created_date.isoformat() if r.created_date else None,
                document_path=doc_paths.get(r.id),
                applicability=r.applicability  # Per RD-RULE-APPLICABILITY
            )
            for r in rules
        ]
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
        # Try direct lookup first (rules stored with semantic IDs since 2026-01-17)
        rule = client.get_rule_by_id(rule_id)

        # If not found, try legacy format conversion
        if not rule:
            legacy_id = normalize_rule_id(rule_id)
            if legacy_id != rule_id:
                rule = client.get_rule_by_id(legacy_id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

        # Get document path for this rule (GAP-UI-AUDIT-001)
        doc_paths = get_rule_document_paths(client, [rule.id])
        doc_path = doc_paths.get(rule.id)

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
            applicability=rule.applicability  # Per RD-RULE-APPLICABILITY
        )
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

        # New rules won't have document linkage yet
        return RuleResponse(
            id=created.id,
            semantic_id=get_semantic_id(created.id),
            name=created.name,
            category=created.category,
            priority=created.priority,
            status=created.status,
            directive=created.directive,
            created_date=created.created_date.isoformat() if created.created_date else None,
            document_path=None,
            applicability=created.applicability  # Per RD-RULE-APPLICABILITY
        )
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
        # Try direct lookup first (rules stored with semantic IDs since 2026-01-17)
        actual_id = rule_id
        existing = client.get_rule_by_id(rule_id)
        if not existing:
            # Try legacy format conversion
            legacy_id = normalize_rule_id(rule_id)
            if legacy_id != rule_id:
                existing = client.get_rule_by_id(legacy_id)
                if existing:
                    actual_id = legacy_id
        if not existing:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

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

        # Get document path for updated rule (GAP-UI-AUDIT-001)
        doc_paths = get_rule_document_paths(client, [updated.id])
        doc_path = doc_paths.get(updated.id)

        return RuleResponse(
            id=updated.id,
            semantic_id=get_semantic_id(updated.id),
            name=updated.name,
            category=updated.category,
            priority=updated.priority,
            status=updated.status,
            directive=updated.directive,
            created_date=updated.created_date.isoformat() if updated.created_date else None,
            document_path=doc_path,
            applicability=updated.applicability  # Per RD-RULE-APPLICABILITY
        )
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
        # Try direct lookup first
        tasks = client.get_tasks_for_rule(rule_id)

        # If no results, try legacy format conversion
        if not tasks:
            legacy_id = normalize_rule_id(rule_id)
            if legacy_id != rule_id:
                tasks = client.get_tasks_for_rule(legacy_id)

        return {
            "rule_id": rule_id,
            "implementing_tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, archive: bool = Query(True, description="Archive before delete")):
    """Delete a rule (archives by default). Per GAP-MCP-008: Accepts semantic IDs."""
    client = get_client()
    if not client:
        raise HTTPException(status_code=503, detail="TypeDB not connected")

    try:
        # Try direct lookup first (rules stored with semantic IDs since 2026-01-17)
        actual_id = rule_id
        existing = client.get_rule_by_id(rule_id)
        if not existing:
            # Try legacy format conversion
            legacy_id = normalize_rule_id(rule_id)
            if legacy_id != rule_id:
                existing = client.get_rule_by_id(legacy_id)
                if existing:
                    actual_id = legacy_id
        if not existing:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

        deleted = client.delete_rule(actual_id, archive=archive)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete rule")

        return None
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
