"""
Tasks Routes Module.

Per RULE-032: File Size Limit (< 300 lines)
Modularized from: governance/routes/tasks.py (475 lines)

Created: 2026-01-04 (GAP-FILE-020)

Submodules:
- crud.py: Basic CRUD operations (list, create, update, delete)
- workflow.py: Workflow operations (available, claim, complete)
- execution.py: Execution log (ORCH-007)
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .workflow import router as workflow_router
from .execution import router as execution_router

# Combined router for backward compatibility
router = APIRouter(tags=["Tasks"])
router.include_router(crud_router)
router.include_router(workflow_router)
router.include_router(execution_router)

__all__ = ['router', 'crud_router', 'workflow_router', 'execution_router']
