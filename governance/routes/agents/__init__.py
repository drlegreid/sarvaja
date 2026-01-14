"""
Agents Routes Package.

Per DOC-SIZE-01-v1: Files under 300 lines.
Split from: governance/routes/agents.py (537 lines)

Created: 2026-01-14
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .observability import router as obs_router
from .visibility import router as vis_router

# Compose all routers
router = APIRouter()
router.include_router(crud_router)
router.include_router(obs_router)
router.include_router(vis_router)

# Re-export for backward compatibility
__all__ = ["router"]
