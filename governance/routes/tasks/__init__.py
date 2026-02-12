"""
Tasks Routes Module.

Per RULE-032: File Size Limit (< 300 lines)
Modularized from: governance/routes/tasks.py (475 lines)

Created: 2026-01-04 (GAP-FILE-020)
Updated: 2026-01-17 - Added verification.py (WORKFLOW-SEQ-01-v1)
Updated: 2026-02-13 - Added details.py (TASK-TECH-01-v1)

Submodules:
- crud.py: Basic CRUD operations (list, create, update, delete)
- workflow.py: Workflow operations (available, claim, complete, promote-resolution)
- execution.py: Execution log (ORCH-007)
- verification.py: Verification subtasks (WORKFLOW-SEQ-01-v1)
- details.py: Detail sections (TASK-TECH-01-v1)
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .workflow import router as workflow_router
from .execution import router as execution_router
from .verification import router as verification_router
from .details import router as details_router

# Combined router for backward compatibility
# NOTE: Order matters! Static routes (workflow) must come before dynamic routes (crud)
# to prevent /{task_id} from matching /available, /execution-log, etc.
router = APIRouter(tags=["Tasks"])
router.include_router(workflow_router)  # /available, /claim, /complete first
router.include_router(execution_router)  # /execution-log
router.include_router(verification_router)  # /{task_id}/verification
router.include_router(details_router)  # /{task_id}/details
router.include_router(crud_router)  # /{task_id} dynamic routes last

__all__ = ['router', 'crud_router', 'workflow_router', 'execution_router',
           'verification_router', 'details_router']
