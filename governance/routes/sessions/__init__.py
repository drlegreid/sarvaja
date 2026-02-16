"""
Sessions Routes Package.

Per DOC-SIZE-01-v1: Files under 300 lines.
Split from: governance/routes/sessions.py (403 lines)

Created: 2026-01-17
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .relations import router as relations_router
from .detail import router as detail_router
from .transcript import router as transcript_router

# Compose all routers
router = APIRouter()
router.include_router(crud_router)
router.include_router(relations_router)
router.include_router(detail_router)
router.include_router(transcript_router)

# Re-export for backward compatibility
__all__ = ["router"]
