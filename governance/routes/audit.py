"""
Audit Trail Routes.

Per RD-DEBUG-AUDIT Phase 4: Query interface for audit trail.

Provides:
- GET /api/audit - List audit entries with filters
- GET /api/audit/summary - Get audit statistics
- GET /api/audit/{entity_id} - Get audit trail for specific entity
"""

from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from governance.stores import (
    query_audit_trail,
    get_audit_summary,
)


router = APIRouter()


class AuditEntryResponse(BaseModel):
    """Response model for audit entry."""
    audit_id: str
    correlation_id: str
    timestamp: str
    actor_id: str
    action_type: str
    entity_type: str
    entity_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    applied_rules: List[str] = []
    metadata: Dict[str, Any] = {}


class AuditSummaryResponse(BaseModel):
    """Response model for audit summary."""
    total_entries: int
    by_action_type: Dict[str, int]
    by_entity_type: Dict[str, int]
    by_actor: Dict[str, int]
    retention_days: int


@router.get("/audit", response_model=List[AuditEntryResponse])
async def list_audit_entries(
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    date_from: Optional[str] = Query(None, description="Include entries on/after (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Include entries on/before (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Skip first N results")
):
    """
    List audit trail entries with optional filters.

    Per RD-DEBUG-AUDIT: Audit trail queryable by entity_id.
    Per GAP-AUDIT-RANGE-001: date_from/date_to timestamp range filter.
    """
    entries = query_audit_trail(
        entity_id=entity_id,
        entity_type=entity_type,
        correlation_id=correlation_id,
        action_type=action_type,
        actor_id=actor_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    return entries


@router.get("/audit/summary", response_model=AuditSummaryResponse)
async def audit_summary():
    """
    Get audit trail summary statistics.

    Shows counts by action type, entity type, and actor.
    """
    return get_audit_summary()


@router.get("/audit/{entity_id}", response_model=List[AuditEntryResponse])
async def get_entity_audit_trail(
    entity_id: str,
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Skip first N results")
):
    """
    Get full audit trail for a specific entity.

    Per RD-DEBUG-AUDIT: "why was this decision made?" queries.
    """
    entries = query_audit_trail(
        entity_id=entity_id,
        limit=limit,
        offset=offset
    )
    return entries
