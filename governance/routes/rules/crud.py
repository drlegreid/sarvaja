"""Rules CRUD Routes - Delegates to service layer for MCP compliance.

Per RULE-012: DSP Semantic Code Structure.
Per MCP enforcement: Uses governance.services.rules for all operations.
Per DOC-SIZE-01-v1: Modularized from rules.py.

Created: 2024-12-28
Updated: 2026-02-01 - Refactored to service layer delegation
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from governance.models import RuleCreate, RuleUpdate, RuleResponse, PaginatedRuleResponse, PaginationMeta
from governance.services import rules as rule_service

router = APIRouter(tags=["Rules"])
logger = logging.getLogger(__name__)


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
    """List governance rules with pagination, sorting, filtering, and search. Per GAP-UI-036."""
    try:
        result = rule_service.list_rules(
            status=status, category=category, priority=priority, search=search,
            sort_by=sort_by, order=order, offset=offset, limit=limit,
            source="rest-api",
        )
        items = [RuleResponse(**r) for r in result["items"]]
        return PaginatedRuleResponse(
            items=items,
            pagination=PaginationMeta(
                total=result["total"], offset=result["offset"],
                limit=result["limit"], has_more=result["has_more"],
                returned=len(items),
            ),
        )
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """Get a specific rule by ID. Per GAP-MCP-008: Accepts semantic IDs."""
    try:
        result = rule_service.get_rule(rule_id, source="rest-api")
        return RuleResponse(**result)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", response_model=RuleResponse, status_code=201)
async def create_rule(rule: RuleCreate):
    """Create a new governance rule."""
    try:
        result = rule_service.create_rule(
            rule_id=rule.rule_id, name=rule.name, category=rule.category,
            priority=rule.priority, directive=rule.directive, status=rule.status,
            source="rest-api",
        )
        return RuleResponse(**result)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, rule: RuleUpdate):
    """Update an existing rule. Per GAP-MCP-008: Accepts semantic IDs."""
    try:
        result = rule_service.update_rule(
            rule_id=rule_id, name=rule.name, category=rule.category,
            priority=rule.priority, directive=rule.directive, status=rule.status,
            source="rest-api",
        )
        return RuleResponse(**result)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}/tasks")
async def get_rule_tasks(rule_id: str):
    """Get tasks implementing a specific rule. Per UI-AUDIT-003."""
    try:
        return rule_service.get_rule_tasks(rule_id, source="rest-api")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str, archive: bool = Query(True, description="Archive before delete")):
    """Delete a rule (archives by default). Per GAP-MCP-008: Accepts semantic IDs."""
    try:
        result = rule_service.delete_rule(rule_id, archive=archive, source="rest-api")
        if not result:
            raise HTTPException(status_code=500, detail="Failed to delete rule")
        return None
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/dependencies/overview")
async def dependency_overview():
    """Global dependency overview. Per PLAN-UI-OVERHAUL-001 Task 4.3."""
    try:
        return rule_service.dependency_overview(source="rest-api")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}/dependencies")
async def get_rule_dependencies(rule_id: str):
    """Get rules that a rule depends on. Per GAP-IMPACT-001."""
    try:
        return rule_service.get_rule_dependencies(rule_id, source="rest-api")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/dependencies/{dep_id}", status_code=201)
async def create_rule_dependency(rule_id: str, dep_id: str):
    """Create a dependency relation between two rules. Per GAP-IMPACT-001."""
    try:
        result = rule_service.create_rule_dependency(rule_id, dep_id, source="rest-api")
        if result:
            return {"dependent": rule_id, "dependency": dep_id, "created": True}
        raise HTTPException(status_code=500, detail="Failed to create dependency")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="TypeDB not connected")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
