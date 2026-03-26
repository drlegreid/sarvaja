"""
Rules Routes Package.

Per DOC-SIZE-01-v1: Files under 300 lines.
Split from: governance/routes/rules.py (410 lines)

Created: 2026-01-17
"""

from fastapi import APIRouter

from .crud import router as rules_router
from .decisions import router as decisions_router
from .compliance import router as compliance_router
from .sync import router as sync_router

# Compose all routers — sync and compliance BEFORE crud so
# /rules/sync/verify and /rules/conflicts are matched before /rules/{rule_id}
router = APIRouter()
router.include_router(sync_router)
router.include_router(compliance_router)
router.include_router(decisions_router)
router.include_router(rules_router)

# Re-export for backward compatibility
__all__ = ["router"]
