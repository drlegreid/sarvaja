"""
Tasks Routes Module.

Per RULE-032: File Size Limit (< 300 lines)
Modularized from: governance/routes/tasks.py (475 lines)

Created: 2026-01-04 (GAP-FILE-020)
Updated: 2026-01-17 - Added verification.py (WORKFLOW-SEQ-01-v1)

Submodules:
- crud.py: Basic CRUD operations (list, create, update, delete)
- workflow.py: Workflow operations (available, claim, complete, promote-resolution)
- execution.py: Execution log (ORCH-007)
- verification.py: Verification subtasks (WORKFLOW-SEQ-01-v1)
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .workflow import router as workflow_router
from .execution import router as execution_router
from .verification import router as verification_router

# Combined router for backward compatibility
router = APIRouter(tags=["Tasks"])
router.include_router(crud_router)
router.include_router(workflow_router)
router.include_router(execution_router)
router.include_router(verification_router)

__all__ = ['router', 'crud_router', 'workflow_router', 'execution_router', 'verification_router']
